TriageBot — Autonomous Tier-1 AI Support & Diagnostics Engine
TriageBot is an enterprise-grade agentic customer support platform built with FastAPI, Groq (Llama 3.3), and SQLite. It leverages LLM Tool Calling (Function Calling) to inspect order databases, run automated diagnostics, and manage high-value refund escalations.

✨ Key Features
🔍 Real-Time Order Verification: Queries order status, price, and warranty details dynamically via SQLite function tools.

⚙️ Agentic Decision Logic: Guides users through troubleshooting workflows before initiating replacement/refund protocols.

🛡️ Human-in-the-Loop Escalation: Auto-approves requests under $100.00 and queues high-value requests (≥ $100.00) to a protected supervisor queue.

🔒 Protected Admin Portal: Password-gated dashboard for supervisors to approve or reject pending escalation tickets.

🏗️ Architecture Overview
Customer/User  -->  Streamlit Web UI (Port 8501)
|
(REST API)
|
v
FastAPI Core (Port 8000)
|
+---------+---------+
|                   |
v                   v
Groq Llama 3.3       SQLite Database
(Tool Calling)      (Orders & Tickets)

🚀 Quickstart Guide
1. Clone the Repository
Bash
git clone https://github.com/NamrataPatil21/agentic-triage-bot.git
cd agentic-triage-bot
2. Set Up Environment Variables
Create a .env file in the root directory:

Code snippet
GROQ_API_KEY=your_groq_api_key_here
3. Run the Backend API (Port 8000)
Bash
python -m uvicorn app:app --reload --port 8000
4. Run the Web Application (Port 8501)
Bash
python -m streamlit run ui.py --server.port 8501
🛠️ Tech Stack
Backend: Python 3.11, FastAPI, Uvicorn, Pydantic

LLM Engine: Groq API (llama-3.3-70b-versatile)

Database: SQLite

Frontend: Streamlit, Custom CSS

Version Control: Git, GitHub
