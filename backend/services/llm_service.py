import json
import traceback
from typing import List, Dict, Any, Union, Optional
from groq import Groq

from backend.config import settings
from backend.services.order_service import get_order_by_id, update_order_status
from backend.services.ticket_service import create_escalation_ticket

# --- GROQ CLIENT INITIALIZATION ---
def get_groq_client() -> Groq:
    """Initializes and returns Groq client using configured GROQ_API_KEY."""
    key = settings.GROQ_API_KEY
    if not key:
        raise ValueError("GROQ_API_KEY environment variable is missing or empty!")
    return Groq(api_key=key)

# --- AGENT TOOLS ---
def tool_get_order_status(order_id: str) -> str:
    """
    Tool: Queries SQLite database for order details, warranty status, and diagnostic steps.
    """
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

def tool_process_refund_or_replacement(order_id: str, customer_name: str, amount: Union[float, str], reason: str) -> str:
    """
    Tool: Issues replacement/refund or escalates to human approval if amount >= $100.00.
    Safely converts string inputs (e.g. "100") to float.
    Enforces threshold logic: amount >= 100.00 MUST create an escalation ticket in SQLite.
    """
    try:
        numeric_amount = float(amount)
    except (ValueError, TypeError):
        numeric_amount = 0.0

    # Business Rule: Amount >= $100.00 requires human manager escalation ticket
    if numeric_amount >= 100.00:
        ticket_id = create_escalation_ticket(
            order_id=order_id, 
            customer_name=customer_name, 
            amount=numeric_amount, 
            reason=f"High-Value Action ({reason}): Equals/Exceeds $100 limit"
        )
        return json.dumps({
            "status": "REQUIRES_HUMAN_APPROVAL", 
            "ticket_id": ticket_id, 
            "amount": numeric_amount,
            "message": f"Escalated to management. Ticket #{ticket_id} created for ${numeric_amount:.2f}."
        })
    
    # Auto-approval for amounts under $100.00
    update_order_status(order_id, "RESOLVED")
    return json.dumps({
        "status": "SUCCESS", 
        "message": f"Action processed for order {order_id} (${numeric_amount:.2f})."
    })

# --- GROQ TOOL SPECIFICATIONS ---
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
            "description": "Issues replacement/refund or escalates to human approval if amount >= $100.",
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

# --- LLAMA-3.3 CHAT ORCHESTRATION ---
SYSTEM_INSTRUCTION = """You are an Autonomous Support Engineer named Alex.
Follow this exact 3-Step Protocol:
STEP 1 (Inspect): Always call `tool_get_order_status` first to fetch order details and recommended troubleshooting steps.
STEP 2 (Troubleshoot): Ask the user to try the `recommended_troubleshooting_step` returned by the tool FIRST. Do not process refunds or replacements immediately.
STEP 3 (Solve): If the user confirms in conversation history that they completed the troubleshooting step and it STILL failed (e.g., they say "no they didn't receive it" or "it didn't work"), call `tool_process_refund_or_replacement`."""

def run_chat_completion(message: str, history: Optional[List[Dict[str, str]]] = None) -> Dict[str, str]:
    """
    Executes multi-turn chat completion using Llama-3.3 on Groq with tool orchestration protocol.

    Returns:
        Dict containing "bot_response" and "action_taken".
    """
    client = get_groq_client()
    messages = [{"role": "system", "content": SYSTEM_INSTRUCTION}]

    # Reconstruct historical messages safely
    if history:
        for msg in history:
            role = "user" if msg.get("role") == "user" else "assistant"
            text = str(msg.get("content", "")).strip()
            if text:
                messages.append({"role": role, "content": text})

    messages.append({"role": "user", "content": message})
    action_log = "Information Provided"

    # Step 1: Initial query to Groq Llama 3.3
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        tools=GROQ_TOOLS,
        tool_choice="auto",
        temperature=0.1
    )

    response_message = response.choices[0].message

    # Step 2: Tool Execution Loop
    if response_message.tool_calls:
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
                tool_output = json.dumps({"error": f"Unknown tool '{fn_name}'"})

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": tool_output
            })

        # Step 3: Send tool execution results back to Groq for final response
        second_response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages
        )
        return {
            "bot_response": second_response.choices[0].message.content or "",
            "action_taken": action_log
        }

    return {
        "bot_response": response_message.content or "No response generated.",
        "action_taken": action_log
    }
