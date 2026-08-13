from backend.config import settings
from backend.database import init_db, get_db_connection
from backend.services.order_service import get_order_by_id
from backend.services.ticket_service import create_escalation_ticket

DB_FILE = settings.DB_FILE

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully via backend module!")