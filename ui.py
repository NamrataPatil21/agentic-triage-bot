import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="TriagePulse Agentic Platform", layout="wide")

st.title("🛡️ TriagePulse: Autonomous Support & Escalation System")

# Sidebar Mode Navigation
mode = st.sidebar.radio("Select View Mode", ["Customer Chat Portal", "Admin Escalation Panel (HITL)"])

# -------------------------------------------------------------------
# VIEW 1: CUSTOMER CHAT PORTAL
# -------------------------------------------------------------------
if mode == "Customer Chat Portal":
    st.subheader("💬 Customer Support Assistant")
    st.caption("Ask questions about your order, track shipments, or request refunds.")

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat Input
    if user_input := st.chat_input("How can I help you today? (e.g., My order 1002 was lost!)"):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # Call FastAPI Backend
        with st.chat_message("assistant"):
            with st.spinner("AI Agent investigating order & database..."):
                try:
                    res = requests.post(f"{API_URL}/api/chat", json={
                    "message": user_input,
                    "history": st.session_state.messages })
                    if res.status_code == 200:
                        data = res.json()
                        bot_reply = data["bot_response"]
                        action = data["action_taken"]

                        st.markdown(bot_reply)
                        st.caption(f"⚙️ **System Action Log:** {action}")
                        
                        st.session_state.messages.append({"role": "assistant", "content": bot_reply})
                    else:
                        st.error("Error connecting to backend API server.")
                except Exception as e:
                    st.error(f"Failed to reach FastAPI backend: {e}")

# -------------------------------------------------------------------
# VIEW 2: ADMIN ESCALATION PANEL (HUMAN-IN-THE-LOOP)
# -------------------------------------------------------------------
else:
    st.subheader("📋 Human-in-the-Loop Admin Approval Queue")
    st.caption("Review high-value refunds and critical escalations flagged by the AI agent.")

    if st.button("🔄 Refresh Queue"):
        st.rerun()

    try:
        res = requests.get(f"{API_URL}/api/tickets/pending")
        if res.status_code == 200:
            tickets = res.json().get("pending_tickets", [])
            
            if not tickets:
                st.success("No pending approval requests. All tickets resolved!")
            else:
                for t in tickets:
                    with st.expander(f"🔴 Ticket #{t['ticket_id']} - Order #{t['order_id']} (${t['requested_amount']:.2f})", expanded=True):
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.write(f"**Customer Name:** {t['customer_name']}")
                            st.write(f"**Requested Amount:** ${t['requested_amount']:.2f}")
                            st.write(f"**Escalation Reason:** {t['reason']}")
                        with col2:
                            if st.button("✅ Approve Refund", key=f"app_{t['ticket_id']}"):
                                app_res = requests.post(
                                f"{API_URL}/api/tickets/approve", 
                                json={"ticket_id": t['ticket_id'], "decision": "APPROVE"})
                                if app_res.status_code == 200:
                                    msg = app_res.json().get("message")
                                    st.toast(f"🎉 {msg}", icon="✅")
                                    st.success(msg)
                                    st.rerun()
                                    
                            if st.button("❌ Reject Request", key=f"rej_{t['ticket_id']}"):
                                rej_res = requests.post(f"{API_URL}/api/tickets/approve", json={"ticket_id": t['ticket_id'], "decision": "REJECT"})
                                if rej_res.status_code == 200:
                                    st.warning(f"Ticket #{t['ticket_id']} Rejected.")
                                    st.rerun()
        else:
            st.error("Could not load escalation queue.")
    except Exception as e:
        st.error(f"Failed to connect to backend server: {e}")