import os
import traceback
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from backend.database import init_db
from backend.services.order_service import get_order_by_id
from backend.services.ticket_service import get_pending_tickets, approve_or_reject_ticket
from backend.services.llm_service import run_chat_completion, tool_process_refund_or_replacement, tool_get_order_status

# Initialize FastAPI App
app = FastAPI(
    title="TriagePulse Agentic API (Groq Engine)",
    version="1.0",
    description="Clean, modular backend for Autonomous Tier-1 Support and Human-in-the-Loop Escalation"
)

# Enable CORS Middleware for UI / web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Database on Server Startup
@app.on_event("startup")
def startup_event():
    """Initializes SQLite database schemas and seed records on app startup."""
    init_db()

# --- PYDANTIC SCHEMAS ---
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[Any]] = []

class ChatResponse(BaseModel):
    user_message: str
    bot_response: str
    action_taken: str
    resolution_data: Optional[Dict[str, Any]] = None

class ApprovalRequest(BaseModel):
    ticket_id: int
    decision: str  # "APPROVE" or "REJECT"

# --- API ENDPOINTS ---

@app.get("/")
def root():
    """Serves templates/index.html single-page app or JSON health status."""
    if os.path.exists("templates/index.html"):
        return FileResponse("templates/index.html")
    elif os.path.exists("index.html"):
        return FileResponse("index.html")
    return {"status": "online", "system": "TriagePulse Agentic API (Groq Engine)"}

@app.get("/api/health")
def health_check():
    """Explicit health check endpoint."""
    return {"status": "online", "system": "TriagePulse Agentic API (Groq Engine)"}

@app.get("/api/order/{order_id}")
def lookup_order(order_id: str):
    """Direct order lookup endpoint for instant sidebar verification."""
    order = get_order_by_id(order_id)
    if not order:
        raise HTTPException(status_code=404, detail=f"Order ID '{order_id}' not found")
    return order

@app.post("/api/chat", response_model=ChatResponse)
def handle_chat(request: ChatRequest):
    """Multi-turn chat & autonomous tool orchestration endpoint."""
    try:
        # Safe fallback parsing for history: filter out invalid entries or empty strings
        sanitized_history = []
        if request.history:
            for item in request.history:
                if isinstance(item, dict):
                    role = str(item.get("role", "")).strip()
                    content = str(item.get("content", "")).strip()
                    if role and content:
                        sanitized_history.append({"role": role, "content": content})
        
        result = run_chat_completion(
            message=request.message,
            history=sanitized_history
        )
        return ChatResponse(
            user_message=request.message,
            bot_response=result["bot_response"],
            action_taken=result["action_taken"],
            resolution_data=result.get("resolution_data")
        )
    except Exception as e:
        print("\n" + "="*50)
        print("EXACT ERROR OCCURRED IN GROQ BACKEND:")
        traceback.print_exc()
        print("="*50 + "\n")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/tickets/pending")
def pending_tickets():
    """Retrieves list of all pending human-in-the-loop escalation tickets."""
    tickets = get_pending_tickets()
    return {"pending_tickets": tickets}

@app.post("/api/tickets/approve")
def approve_ticket(req: ApprovalRequest):
    """Approve or reject a pending escalation ticket."""
    try:
        res = approve_or_reject_ticket(ticket_id=req.ticket_id, decision=req.decision)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
