from typing import Optional, Dict, Any
from backend.database import get_db_connection

def get_order_by_id(order_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetches order record from SQLite by Order ID or Replacement Order ID.

    Returns:
        Dict with keys: order_id, customer, item, price, status, troubleshooting, warranty_valid, tracking_number, replacement_order_id
        or None if not found.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT order_id, customer_name, item_name, price, status, troubleshooting_step, warranty_valid, tracking_number, replacement_order_id
        FROM orders 
        WHERE order_id = ? OR replacement_order_id = ?
    """, (order_id, order_id))
    row = cursor.fetchone()
    conn.close()

    if row:
        row_keys = row.keys()
        return {
            "order_id": row["order_id"],
            "customer": row["customer_name"],
            "item": row["item_name"],
            "price": row["price"],
            "status": row["status"],
            "troubleshooting": row["troubleshooting_step"],
            "warranty_valid": bool(row["warranty_valid"]),
            "tracking_number": row["tracking_number"] if "tracking_number" in row_keys else None,
            "replacement_order_id": row["replacement_order_id"] if "replacement_order_id" in row_keys else None
        }
    return None

def update_order_replacement_details(
    order_id: str, 
    new_status: str, 
    tracking_number: Optional[str] = None, 
    replacement_order_id: Optional[str] = None
) -> bool:
    """
    Updates status, tracking_number, and replacement_order_id for an order in SQLite.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE orders 
        SET status = ?, tracking_number = ?, replacement_order_id = ? 
        WHERE order_id = ?
    """, (new_status, tracking_number, replacement_order_id, order_id))
    affected_rows = cursor.rowcount
    conn.commit()
    conn.close()
    return affected_rows > 0

def update_order_status(order_id: str, new_status: str) -> bool:
    """
    Updates the status column of an existing order in SQLite.
    """
    return update_order_replacement_details(order_id, new_status)
