import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="TriagePulse | Agentic Support Engine",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS styling strictly enclosed in Python multiline string
CSS_STYLES = """
<style>
    .stApp {
        background-color: #F8FAFC;
    }
    .header-banner {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
        padding: 24px 32px;
        border-radius: 14px;
        color: #FFFFFF;
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.15);
        margin-bottom: 24px;
    }
    .action-badge {
        background-color: #EEF2FF;
        color: #4F46E5;
        border: 1px solid #C7D2FE;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.82rem;
        font-weight: 600;
        display: inline-block;
        margin-top: 6px;
    }
    .ticket-card {
        background: #FFFFFF;
        border-radius: 12px;
        padding: 20px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
        margin-bottom: 16px;
    }
    .badge-pending {
        background-color: #FEF3C7;
        color: #92400E;
        padding: 4px 12px;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 0.78rem;
    }
    .amount-highlight {
        font-size: 1.3rem;
        color: #2563EB;
        font-weight: 800;
    }
    .lock-card {
        background: #FFFFFF;
        padding: 32px;
        border-radius: 16px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 4px 16px rgba(0,0,0,0.06);
        max-width: 500px;
        margin: 40px auto;
        text-align: center;
    }
</style>
"""
st.markdown(CSS_STYLES, unsafe_allow_html=True)

# Top Banner Header
st.markdown("""
<div class="header-banner">
    <h2 style="margin:0; font-weight:800; color:#FFFFFF;">🛡️ TriagePulse Support Portal</h2>
    <p style="margin:4px 0 0 0; color:#94A3B8;">Autonomous Tier-1 Customer Support & AI Diagnostics Engine</p>
</div>
""", unsafe_allow_html=True)

# Sidebar Navigation
st.sidebar.markdown("### 🛡️ Portal Navigation")
mode = st.sidebar.radio("Select View", ["💬 Customer Support Portal", "⚙️ Admin Escalation Queue (HITL)"])

# --- SIDEBAR: LIVE ORDER LOOKUP ---
st.sidebar.divider()
st.sidebar.markdown("### 🔍 Live Order Lookup")
search_order_id = st.sidebar.text_input("Order ID Search", placeholder="e.g. 1001, 1002")

if search_order_id:
    try:
        lookup_res = requests.get(f"{API_URL}/api/order/{search_order_id.strip()}", timeout=4)
        if lookup_res.status_code == 200:
            data = lookup_res.json()
            is_resolved = "RESOLVED" in data.get("status", "")
            
            status_flag = "🟢 " if is_resolved else "🔵 "
            status_text = status_flag + data.get("status", "")
            warranty_text = "Valid ✅" if data.get("warranty_valid") else "Expired ⚠️"
            
            st.sidebar.success("Order Identified")
            st.sidebar.markdown(f"**Item:** {data.get('item', 'N/A')}")
            st.sidebar.markdown(f"**Customer:** {data.get('customer', 'N/A')}")
            st.sidebar.markdown(f"**Price:** ${data.get('price', 0.0):.2f}")
            st.sidebar.markdown(f"**Status:** `{status_text}`")
            st.sidebar.markdown(f"**Warranty:** `{warranty_text}`")
        else:
            st.sidebar.warning(f"Order ID '{search_order_id}' not found.")
    except Exception:
        st.sidebar.error("Could not reach API backend.")

# Sidebar System Health Status
st.sidebar.divider()
st.sidebar.markdown("### 📊 System Status")
try:
    health_res = requests.get(f"{API_URL}/", timeout=2)
    backend_online = health_res.status_code == 200
except Exception:
    backend_online = False

if backend_online:
    st.sidebar.success("Groq Llama-3.3 Engine: **Active**")
    st.sidebar.info("SQLite Database: **Connected**")
else:
    st.sidebar.error("Backend Server: **Disconnected**")

# -------------------------------------------------------------------
# VIEW 1: CUSTOMER SUPPORT PORTAL
# -------------------------------------------------------------------
if mode == "💬 Customer Support Portal":
    st.subheader("💬 Interactive Support Console")
    st.caption("Chat with Alex, your autonomous support engineer.")

    # Quick Scenario Actions
    st.caption("⚡ Quick Test Scenarios:")
    col_a, col_b, col_c = st.columns(3)

    prompt_to_add = None
    if col_a.button("🎧 Defective Item (Order 1001)"):
        prompt_to_add = "My wireless headphones for order 1001 won't turn on!"
    if col_b.button("📦 Lost Package (Order 1002)"):
        prompt_to_add = "My order 1002 smart watch never arrived!"
    if col_c.button("🔄 Check Status (Order 1001)"):
        prompt_to_add = "What is the status of my order 1001 now?"

    # Session History Initialization
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if prompt_to_add:
        st.session_state.messages.append({"role": "user", "content": prompt_to_add})

    # Render History
    for msg in st.session_state.messages:
        avatar = "👤" if msg["role"] == "user" else "🤖"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])
            if msg["role"] == "assistant" and msg.get("action"):
                st.markdown(f'<div class="action-badge">⚙️ Executed: {msg["action"]}</div>', unsafe_allow_html=True)

    user_input = st.chat_input("Describe your issue (e.g., Order 1001 headphones won't turn on)...")
    if prompt_to_add:
        user_input = prompt_to_add

    if user_input and not prompt_to_add:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user", avatar="👤"):
            st.markdown(user_input)

    if user_input:
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Alex checking database..."):
                try:
                    history_payload = [
                        {"role": m["role"], "content": m["content"]}
                        for m in st.session_state.messages[:-1]
                    ]
                    res = requests.post(
                        f"{API_URL}/api/chat",
                        json={"message": user_input, "history": history_payload},
                        timeout=30
                    )
                    if res.status_code == 200:
                        data = res.json()
                        bot_reply = data.get("bot_response", "")
                        action = data.get("action_taken", "Information Provided")

                        st.markdown(bot_reply)
                        st.markdown(f'<div class="action-badge">⚙️ Executed: {action}</div>', unsafe_allow_html=True)
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": bot_reply,
                            "action": action
                        })
                    else:
                        st.error("Error communicating with backend server.")
                except Exception as e:
                    st.error(f"Failed to reach FastAPI backend: {e}")

# -------------------------------------------------------------------
# VIEW 2: ADMIN ESCALATION QUEUE (PROTECTED)
# -------------------------------------------------------------------
else:
    st.subheader("⚙️ Human-In-The-Loop Approval Operations")
    st.caption("Review high-value requests flagged for human supervisor sign-off.")

    # Authentication Check
    if "admin_authenticated" not in st.session_state:
        st.session_state.admin_authenticated = False

    if not st.session_state.admin_authenticated:
        st.markdown("""
        <div class="lock-card">
            <h3>🔒 Restricted Access</h3>
            <p style="color:#64748B;">Authorized Personnel Only. Please enter supervisor credentials.</p>
        </div>
        """, unsafe_allow_html=True)

        col_left, col_mid, col_right = st.columns([1, 2, 1])
        with col_mid:
            pwd = st.text_input("Supervisor Password", type="password", key="pwd_input")
            if st.button("Unlock Admin Queue", use_container_width=True):
                if pwd == "admin123":
                    st.session_state.admin_authenticated = True
                    st.success("Authentication successful!")
                    st.rerun()
                else:
                    st.error("Incorrect password. Access denied.")
    else:
        # Lock status header & Logout option
        auth_col1, auth_col2 = st.columns([4, 1])
        with auth_col1:
            st.success("🔓 Supervisor Session Active (Authenticated)")
        with auth_col2:
            if st.button("🔒 Lock Session"):
                st.session_state.admin_authenticated = False
                st.rerun()

        # Metrics Bar
        m1, m2, m3 = st.columns(3)
        
        try:
            res = requests.get(f"{API_URL}/api/tickets/pending", timeout=5)
            if res.status_code == 200:
                tickets = res.json().get("pending_tickets", [])

                m1.metric("Pending Approval Queue", len(tickets))
                m2.metric("Auto-Approval Limit", "$100.00")
                m3.metric("System Status", "Healthy")

                st.divider()

                if not tickets:
                    st.info("🎉 All clear! No tickets currently awaiting supervisor review.")
                else:
                    for t in tickets:
                        st.markdown(f"""
                        <div class="ticket-card">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <h4 style="margin:0;">Ticket #{t['ticket_id']} — Order #{t['order_id']}</h4>
                                <span class="badge-pending">PENDING APPROVAL</span>
                            </div>
                            <p style="margin:10px 0 4px 0;"><strong>Customer Name:</strong> {t['customer_name']}</p>
                            <p style="margin:4px 0;"><strong>Requested Amount:</strong> <span class="amount-highlight">${t['requested_amount']:.2f}</span></p>
                            <p style="margin:4px 0 0 0;"><strong>Reason Flagged:</strong> {t['reason']}</p>
                        </div>
                        """, unsafe_allow_html=True)

                        col_app, col_rej = st.columns(2)
                        with col_app:
                            if st.button(f"✅ Approve Refund (${t['requested_amount']:.2f})", key=f"app_{t['ticket_id']}", use_container_width=True):
                                app_res = requests.post(
                                    f"{API_URL}/api/tickets/approve",
                                    json={"ticket_id": t['ticket_id'], "decision": "APPROVE"}
                                )
                                if app_res.status_code == 200:
                                    st.toast("Ticket Approved & Order Status Updated!", icon="✅")
                                    st.rerun()
                                else:
                                    st.error("Failed to approve ticket.")

                        with col_rej:
                            if st.button(f"❌ Reject Request", key=f"rej_{t['ticket_id']}", use_container_width=True):
                                rej_res = requests.post(
                                    f"{API_URL}/api/tickets/approve",
                                    json={"ticket_id": t['ticket_id'], "decision": "REJECT"}
                                )
                                if rej_res.status_code == 200:
                                    st.toast("Ticket Rejected.", icon="❌")
                                    st.rerun()
                                else:
                                    st.error("Failed to reject ticket.")
                        st.write("")
            else:
                st.error("Could not fetch pending tickets from backend API.")
        except Exception as e:
            st.error(f"Error connecting to backend server: {e}")