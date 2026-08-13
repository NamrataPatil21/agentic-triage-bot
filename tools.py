import json

# Mock Database simulating real company records
MOCK_ORDERS = {
    "1001": {"customer": "Alex", "item": "Wireless Headphones", "price": 49.99, "status": "DELIVERED"},
    "1002": {"customer": "Priya", "item": "Smart Watch", "price": 120.00, "status": "LOST_IN_TRANSIT"},
    "1003": {"customer": "Rohan", "item": "Gaming Mouse", "price": 25.50, "status": "PROCESSING"},
}

def get_order_status(order_id: str) -> str:
    """
    Looks up the status and details of an order in the database using its Order ID.
    """
    print(f"\n[TOOL EXECUTION]: Querying database for Order ID '{order_id}'...")
    if order_id in MOCK_ORDERS:
        return json.dumps({"found": True, **MOCK_ORDERS[order_id]})
    return json.dumps({"found": False, "error": f"Order ID {order_id} not found in database."})


def process_refund(order_id: str, amount: float) -> str:
    """
    Simulates issuing a refund to the customer's payment card.
    Auto-approves amounts under $100.
    """
    print(f"\n[TOOL EXECUTION]: Attempting Stripe Refund for Order #{order_id} (Amount: ${amount:.2f})...")
    
    # Business Guardrail Rule
    if amount > 100.00:
        return json.dumps({
            "success": False, 
            "status": "REQUIRES_HUMAN_APPROVAL", 
            "message": f"Refund of ${amount:.2f} exceeds auto-approval limit ($100.00). Escalate to manager."
        })
        
    return json.dumps({
        "success": True, 
        "status": "REFUND_ISSUED", 
        "message": f"Successfully refunded ${amount:.2f} to original payment card."
    })