import os
import json
import sqlite3
import traceback
from typing import Optional, List, Dict
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from groq import Groq

import database
from database import get_order_by_id, create_escalation_ticket, DB_FILE

# Initialize Database on Server Startup
database.init_db()

app = FastAPI(title="TriagePulse Agentic API (Groq Engine)", version="1.0")

# --- PYDANTIC SCHEMAS ---
class ChatRequest(BaseModel):
    message: str
    history: Optional[List[Dict[str, str]]] = []

class ChatResponse(BaseModel):
    user_message: str
    bot_response: str
    action_taken: str

class ApprovalRequest(BaseModel):
    ticket_id: int
    decision: str # "APPROVE" or "REJECT"

# --- HELPER FUNCTIONS & TOOLS ---
def get_groq_client():
    key = os.getenv("GROQ_API_KEY", "")
    if not key:
        raise ValueError("GROQ_API_KEY environment variable is missing or empty!")
    return Groq(api_key=key)

def tool_get_order_status(order_id: str) -> str:
    order = get_order_by_id(order_id)
    if order:
        return json.dumps({
            "order_id": order['order_id'],
            "customer": order['customer'],
            "item": order['item'],
            "price": order['price'],
            "status": order['status'],
            "warranty_valid": order['warranty_valid'],
            "recommended_troubleshooting_step": order['troubleshooting']
        })
    return json.dumps({"error": f"Order ID '{order_id}' was not found in database."})

def tool_process_refund_or_replacement(order_id: str, customer_name: str, amount: float | str, reason: str) -> str:
    """Tool: Issues replacement/refund or escalates to human approval if amount >= $100."""
    try:
        numeric_amount = float(amount)
    except (ValueError, TypeError):
        numeric_amount = 0.0

    # FIX: Change > 100.00 to >= 100.00 so $100 triggers ticket creation!
    if numeric_amount >= 100.00:
        ticket_id = create_escalation_ticket(order_id, customer_name, numeric_amount, f"High-Value Action ({reason}): Equals/Exceeds $100 limit")
        return json.dumps({
            "status": "REQUIRES_HUMAN_APPROVAL", 
            "ticket_id": ticket_id, 
            "amount": numeric_amount,
            "message": f"Escalated to management. Ticket #{ticket_id} created for ${numeric_amount:.2f}."
        })
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE orders SET status = 'RESOLVED' WHERE order_id = ?", (order_id,))
    conn.commit()
    conn.close()
    return json.dumps({"status": "SUCCESS", "message": f"Action processed for order {order_id} (${numeric_amount:.2f})."})
# Define Groq Tool Specifications
GROQ_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "tool_get_order_status",
            "description": "Queries database for order information, warranty status, and diagnostic steps.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "string", "description": "The order ID (e.g., 1001, 1002)"}
                },
                "required": ["order_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "tool_process_refund_or_replacement",
            "description": "Issues replacement/refund or escalates to human approval if amount > $100.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "string", "description": "The order ID"},
                    "customer_name": {"type": "string", "description": "Full customer name"},
                    "amount": {
                        "type": ["number", "string"], 
                        "description": "Requested refund or replacement amount (e.g. 100 or 120.50)"
                    },
                    "reason": {"type": "string", "description": "Reason for action"}
                },
                "required": ["order_id", "customer_name", "amount", "reason"]
            }
        }
    }
]
# --- API ENDPOINTS ---

@app.get("/")
def root():
    return {"status": "online", "system": "TriagePulse Agentic API (Groq Engine)"}

@app.post("/api/chat", response_model=ChatResponse)
def handle_chat(request: ChatRequest):
    user_msg = request.message
    system_instruction = """You are an Autonomous Support Engineer named Alex.
Follow this exact 3-Step Protocol:
STEP 1 (Inspect): Always call `tool_get_order_status` first to fetch order details and recommended troubleshooting steps.
STEP 2 (Troubleshoot): Ask the user to try the `recommended_troubleshooting_step` returned by the tool FIRST. Do not process refunds or replacements immediately.
STEP 3 (Solve): If the user confirms in conversation history that they completed the troubleshooting step and it STILL failed (e.g., they say "no they didn't receive it" or "it didn't work"), call `tool_process_refund_or_replacement`."""

    action_log = "Information Provided"

    try:
        client = get_groq_client()
        messages = [{"role": "system", "content": system_instruction}]

        # Reconstruct chat context safely
        if request.history:
            for msg in request.history:
                role = "user" if msg.get("role") == "user" else "assistant"
                text = str(msg.get("content", "")).strip()
                if text:
                    messages.append({"role": role, "content": text})

        messages.append({"role": "user", "content": user_msg})

        # Step 1: Query Groq
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            tools=GROQ_TOOLS,
            tool_choice="auto",
            temperature=0.1
        )

        response_message = response.choices[0].message

        # Step 2: Handle Tool Calls
        if response_message.tool_calls:
            # Convert response message to dict so it serializes cleanly into messages array
            messages.append({
                "role": "assistant",
                "content": response_message.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    } for tc in response_message.tool_calls
                ]
            })
            
            for tool_call in response_message.tool_calls:
                fn_name = tool_call.function.name
                fn_args = json.loads(tool_call.function.arguments)
                action_log = f"Executed Tool: {fn_name}"

                if fn_name == "tool_get_order_status":
                    tool_output = tool_get_order_status(**fn_args)
                elif fn_name == "tool_process_refund_or_replacement":
                    tool_output = tool_process_refund_or_replacement(**fn_args)
                else:
                    tool_output = json.dumps({"error": "Unknown tool"})

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_output
                })

            # Step 3: Send tool outputs back to Groq for final natural language response
            second_response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages
            )
            return ChatResponse(
                user_message=user_msg,
                bot_response=second_response.choices[0].message.content,
                action_taken=action_log
            )

        return ChatResponse(
            user_message=user_msg,
            bot_response=response_message.content or "No response generated.",
            action_taken=action_log
        )

    except Exception as e:
        print("\n" + "="*50)
        print("EXACT ERROR OCCURRED IN GROQ BACKEND:")
        traceback.print_exc()
        print("="*50 + "\n")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/tickets/pending")
def get_pending_tickets():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT ticket_id, order_id, customer_name, requested_amount, reason, status FROM tickets WHERE status = 'PENDING'")
    rows = cursor.fetchall()
    conn.close()
    
    tickets = [
        {"ticket_id": r[0], "order_id": r[1], "customer_name": r[2], "requested_amount": r[3], "reason": r[4], "status": r[5]}
        for r in rows
    ]
    return {"pending_tickets": tickets}

@app.post("/api/tickets/approve")
def approve_ticket(req: ApprovalRequest):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    if req.decision == "APPROVE":
        cursor.execute("UPDATE tickets SET status = 'APPROVED' WHERE ticket_id = ?", (req.ticket_id,))
        cursor.execute("SELECT order_id FROM tickets WHERE ticket_id = ?", (req.ticket_id,))
        row = cursor.fetchone()
        if row:
            order_id = row[0]
            cursor.execute("UPDATE orders SET status = 'RESOLVED_AND_REFUNDED' WHERE order_id = ?", (order_id,))
            message = f"Ticket #{req.ticket_id} APPROVED! Order #{order_id} updated to RESOLVED_AND_REFUNDED in SQLite."
        else:
            message = f"Ticket #{req.ticket_id} APPROVED."
    else:
        cursor.execute("UPDATE tickets SET status = 'REJECTED' WHERE ticket_id = ?", (req.ticket_id,))
        message = f"Ticket #{req.ticket_id} REJECTED."
        
    conn.commit()
    conn.close()
    return {"status": "success", "message": message}