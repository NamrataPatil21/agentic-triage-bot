from typing import Optional, Dict, Any
from backend.database import get_db_connection

def get_order_by_id(order_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetches order record from SQLite by Order ID.

    Returns:
        Dict with keys: order_id, customer, item, price, status, troubleshooting, warranty_valid
        or None if not found.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT order_id, customer_name, item_name, price, status, troubleshooting_step, warranty_valid
        FROM orders 
        WHERE order_id = ?
    """, (order_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            "order_id": row["order_id"],
            "customer": row["customer_name"],
            "item": row["item_name"],
            "price": row["price"],
            "status": row["status"],
            "troubleshooting": row["troubleshooting_step"],
            "warranty_valid": bool(row["warranty_valid"])
        }
    return None

def update_order_status(order_id: str, new_status: str) -> bool:
    """
    Updates the status column of an existing order in SQLite.

    Returns:
        True if updated successfully, False if order was not found.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE orders SET status = ? WHERE order_id = ?", (new_status, order_id))
    affected_rows = cursor.rowcount
    conn.commit()
    conn.close()
    return affected_rows > 0
