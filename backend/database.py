import sqlite3
import os
from backend.config import settings

def get_db_connection():
    """
    Creates and returns a raw SQLite database connection.
    Uses DB_FILE configured in settings.
    """
    db_path = settings.DB_FILE
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Enables accessing columns by name
    return conn

def init_db():
    """
    Initializes database schemas for orders and tickets,
    and seeds initial diagnostic & order records if empty.
    """
    conn = get_db_connection()
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
            warranty_valid INTEGER DEFAULT 1,
            tracking_number TEXT,
            replacement_order_id TEXT
        )
    ''')

    # Ensure schema migrations for existing databases
    for col in ["tracking_number TEXT", "replacement_order_id TEXT"]:
        try:
            cursor.execute(f"ALTER TABLE orders ADD COLUMN {col}")
        except sqlite3.OperationalError:
            pass  # Column already exists

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

    # Seed mock order data if table is empty
    cursor.execute("SELECT COUNT(*) FROM orders")
    if cursor.fetchone()[0] == 0:
        cursor.executemany('''
            INSERT INTO orders (order_id, customer_name, item_name, price, status, troubleshooting_step, warranty_valid)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', [
            ("1001", "Alex", "Wireless Headphones", 49.99, "DELIVERED", "Hold power button for 10 seconds to hard reset.", 1),
            ("1002", "Priya", "Smart Watch", 120.00, "LOST_IN_TRANSIT", "Check with building reception or neighbors first.", 1),
            ("1003", "Rohan", "Gaming Mouse", 25.50, "PROCESSING", "Unplug and re-plug into a USB 3.0 port.", 1),
            ("1004", "Sarah", "4K Monitor", 350.00, "DELIVERED", "Inspect HDMI cable and test on a second power outlet.", 0)
        ])

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully!")
