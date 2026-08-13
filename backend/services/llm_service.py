import json
import traceback
from typing import List, Dict, Any, Union, Optional
from groq import Groq

from backend.config import settings
from backend.services.order_service import get_order_by_id, update_order_status, update_order_replacement_details
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
    Returns structured details including replacement_order_id, tracking_number, estimated_delivery, and status.
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
            "message": f"High-value action flagged for management review. Ticket #{ticket_id} created for ${numeric_amount:.2f}."
        })
    
    # Auto-approval for amounts under $100.00
    replacement_order_id = f"{order_id}-R"
    tracking_number = "TRK-FEDEX-89021"
    estimated_delivery = "2-3 Business Days"
    
    reason_str = str(reason).lower()
    if "refund" in reason_str:
        status = "REFUND_PROCESSED"
    else:
        status = "REPLACEMENT_DISPATCHED"

    update_order_replacement_details(
        order_id=order_id,
        new_status=status,
        tracking_number=tracking_number,
        replacement_order_id=replacement_order_id
    )
    update_order_status(order_id, "RESOLVED")

    return json.dumps({
        "status": status, 
        "replacement_order_id": replacement_order_id,
        "tracking_number": tracking_number,
        "estimated_delivery": estimated_delivery,
        "message": f"Refund/replacement auto-approved for order {order_id} (${numeric_amount:.2f}). Status: {status}, Tracking: {tracking_number}, Replacement Order #: {replacement_order_id}."
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
Follow this exact protocol:
STEP 1 (Inspect): Always call `tool_get_order_status` first to fetch order details (customer name, price, status, troubleshooting steps).
STEP 2 (Troubleshoot): If the customer is reporting a defective or lost item for the first time, guide them through the recommended troubleshooting step.
STEP 3 (Escalate/Solve): If the customer confirms the troubleshooting step FAILED, or if they explicitly ask for a replacement/refund, you MUST immediately call `tool_process_refund_or_replacement`.

CRITICAL TOOL PARAMETERS:
- `order_id`: The ID of the order.
- `customer_name`: The customer's full name (from the order details retrieved in Step 1).
- `amount`: The full price of the item (from the order details retrieved in Step 1).
- `reason`: Brief explanation of the failure (e.g., "Troubleshooting failed - item won't turn on").

RESPONSE FORMATTING FOR ESCALATIONS:
When `tool_process_refund_or_replacement` returns status `REQUIRES_HUMAN_APPROVAL` with a `ticket_id`, politely inform the customer that their request (Ticket #X) has been submitted to management for supervisor sign-off because the requested amount equals or exceeds $100.00."""

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

        resolution_data = None
        for tool_call in response_message.tool_calls:
            fn_name = tool_call.function.name
            fn_args = json.loads(tool_call.function.arguments)
            action_log = f"Executed Tool: {fn_name}"

            if fn_name == "tool_get_order_status":
                tool_output = tool_get_order_status(**fn_args)
            elif fn_name == "tool_process_refund_or_replacement":
                tool_output = tool_process_refund_or_replacement(**fn_args)
                try:
                    res_obj = json.loads(tool_output)
                    if res_obj.get("status") in ["SUCCESS", "REPLACEMENT_DISPATCHED", "REFUND_PROCESSED"]:
                        resolution_data = {
                            "replacement_order_id": res_obj.get("replacement_order_id", f"{fn_args.get('order_id', '')}-R"),
                            "tracking_number": res_obj.get("tracking_number", "TRK-FEDEX-89021"),
                            "estimated_delivery": res_obj.get("estimated_delivery", "2-3 Business Days"),
                            "status": res_obj.get("status", "REPLACEMENT_DISPATCHED")
                        }
                except Exception:
                    pass
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
            "action_taken": action_log,
            "resolution_data": resolution_data
        }

    return {
        "bot_response": response_message.content or "No response generated.",
        "action_taken": action_log
    }
