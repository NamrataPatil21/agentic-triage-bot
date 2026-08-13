import sqlite3
import json

DB_FILE = "triage_bot.db"

def init_db():
    """Initializes the database schema and seeds initial order & diagnostic data."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Table for Orders with Warranty & Troubleshooting metadata
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            order_id TEXT PRIMARY KEY,
            customer_name TEXT,
            item_name TEXT,
            price REAL,
            status TEXT,
            troubleshooting_step TEXT,
            warranty_valid INTEGER DEFAULT 1
        )
    ''')

    # Table for Escalated Tickets (Human-in-the-Loop Queue)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tickets (
            ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id TEXT,
            customer_name TEXT,
            requested_amount REAL,
            reason TEXT,
            status TEXT DEFAULT 'PENDING'
        )
    ''')

    # Seed mock data if empty
    cursor.execute("SELECT COUNT(*) FROM orders")
    if cursor.fetchone()[0] == 0:
        cursor.executemany('''
            INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', [
            ("1001", "Alex", "Wireless Headphones", 49.99, "DELIVERED", "Hold power button for 10 seconds to hard reset.", 1),
            ("1002", "Priya", "Smart Watch", 120.00, "LOST_IN_TRANSIT", "Check with building reception or neighbors first.", 1),
            ("1003", "Rohan", "Gaming Mouse", 25.50, "PROCESSING", "Unplug and re-plug into a USB 3.0 port.", 1),
            ("1004", "Sarah", "4K Monitor", 350.00, "DELIVERED", "Inspect HDMI cable and test on a second power outlet.", 0)
        ])

    conn.commit()
    conn.close()

def get_order_by_id(order_id: str):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT order_id, customer_name, item_name, price, status, troubleshooting_step, warranty_valid FROM orders WHERE order_id = ?", (order_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "order_id": row[0], 
            "customer": row[1], 
            "item": row[2], 
            "price": row[3], 
            "status": row[4],
            "troubleshooting": row[5],
            "warranty_valid": bool(row[6])
        }
    return None

def create_escalation_ticket(order_id: str, customer_name: str, amount: float, reason: str):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO tickets (order_id, customer_name, requested_amount, reason, status)
        VALUES (?, ?, ?, ?, 'PENDING')
    ''', (order_id, customer_name, amount, reason))
    ticket_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return ticket_id

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully with Diagnostic schemas!")