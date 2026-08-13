from typing import List, Dict, Any
from backend.database import get_db_connection

def create_escalation_ticket(order_id: str, customer_name: str, amount: float, reason: str) -> int:
    """
    Creates a new escalation ticket in the SQLite database with 'PENDING' status.

    Returns:
        The generated ticket_id integer.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO tickets (order_id, customer_name, requested_amount, reason, status)
        VALUES (?, ?, ?, ?, 'PENDING')
    ''', (order_id, customer_name, amount, reason))
    ticket_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return ticket_id

def get_pending_tickets() -> List[Dict[str, Any]]:
    """
    Queries SQLite for all escalation tickets with status 'PENDING'.

    Returns:
        List of ticket dictionaries.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT ticket_id, order_id, customer_name, requested_amount, reason, status 
        FROM tickets 
        WHERE status = 'PENDING'
    """)
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "ticket_id": r["ticket_id"],
            "order_id": r["order_id"],
            "customer_name": r["customer_name"],
            "requested_amount": r["requested_amount"],
            "reason": r["reason"],
            "status": r["status"]
        }
        for r in rows
    ]

def approve_or_reject_ticket(ticket_id: int, decision: str) -> Dict[str, Any]:
    """
    Processes human supervisor decision ('APPROVE' or 'REJECT') on a ticket.
    If approved, updates ticket status to 'APPROVED' and sets order status to 'RESOLVED_AND_REFUNDED'.
    If rejected, updates ticket status to 'REJECTED'.

    Returns:
        Dict with status and human-readable message.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    if decision.upper() == "APPROVE":
        cursor.execute("UPDATE tickets SET status = 'APPROVED' WHERE ticket_id = ?", (ticket_id,))
        cursor.execute("SELECT order_id FROM tickets WHERE ticket_id = ?", (ticket_id,))
        row = cursor.fetchone()
        
        if row and row["order_id"]:
            order_id = row["order_id"]
            replacement_order_id = f"{order_id}-R"
            tracking_number = "TRK-FEDEX-89021"
            status_text = f"REPLACEMENT_DISPATCHED ({tracking_number})"
            cursor.execute("""
                UPDATE orders 
                SET status = ?, tracking_number = ?, replacement_order_id = ? 
                WHERE order_id = ?
            """, (status_text, tracking_number, replacement_order_id, order_id))
            message = f"Ticket #{ticket_id} APPROVED! Order #{order_id} updated to {status_text} in SQLite."
        else:
            message = f"Ticket #{ticket_id} APPROVED."
    else:
        cursor.execute("UPDATE tickets SET status = 'REJECTED' WHERE ticket_id = ?", (ticket_id,))
        message = f"Ticket #{ticket_id} REJECTED."

    conn.commit()
    conn.close()
    return {"status": "success", "message": message}
