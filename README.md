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

