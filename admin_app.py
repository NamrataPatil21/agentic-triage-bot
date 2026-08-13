import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000"
ADMIN_PASSWORD = "admin123"

st.set_page_config(
    page_title="TriagePulse | Admin Escalation Portal",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Clean, strictly enclosed CSS styling block
CSS_STYLES = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    .main {
        background-color: #F8FAFC;
    }
    .tp-header-banner {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
        padding: 24px 32px;
        border-radius: 14px;
        color: #FFFFFF;
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.15);
        margin-bottom: 24px;
    }
    .tp-header-title {
        font-size: 2.1rem;
        font-weight: 800;
        color: #F8FAFC;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .tp-header-subtitle {
        font-size: 0.98rem;
        color: #94A3B8;
        margin-top: 6px;
        font-weight: 400;
    }
    .tp-ticket-card {
        background: #FFFFFF;
        border-radius: 12px;
        padding: 22px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.04);
        margin-bottom: 20px;
    }
    .tp-ticket-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
    }
    .tp-ticket-title {
        font-size: 1.25rem;
        font-weight: 700;
        color: #0F172A;
        margin: 0;
    }
    .tp-badge-pending {
        background-color: #FEF3C7;
        color: #92400E;
        padding: 5px 14px;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 0.8rem;
        letter-spacing: 0.04em;
        border: 1px solid #FDE68A;
    }
    .tp-amount-blue {
        font-size: 1.4rem;
        color: #2563EB;
        font-weight: 800;
    }
    .tp-ticket-divider {
        border: 0;
        border-top: 1px solid #F1F5F9;
        margin: 12px 0;
    }
    .tp-detail-label {
        color: #64748B;
        font-weight: 500;
        font-size: 0.92rem;
    }
    .tp-detail-val {
        color: #1E293B;
        font-weight: 600;
        font-size: 0.95rem;
    }
    .tp-lock-card {
        background: #FFFFFF;
        border-radius: 16px;
        padding: 40px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.08);
        max-width: 500px;
        margin: 40px auto;
        text-align: center;
    }
</style>
"""

st.markdown(CSS_STYLES, unsafe_allow_html=True)

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

st.markdown("""
<div class="tp-header-banner">
    <div class="tp-header-title">🛡️ TriagePulse Admin Portal</div>
    <div class="tp-header-subtitle">Human-in-the-Loop Approval & High-Value Escalation Queue</div>
</div>
""", unsafe_allow_html=True)

# Lock Screen Authentication Guard
if not st.session_state.authenticated:
    col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
    with col_l2:
        st.markdown("""
        <div class="tp-lock-card">
            <h2 style="color: #0F172A; font-weight: 800; margin-bottom: 6px;">🔒 Restricted Access</h2>
            <p style="color: #64748B; font-size: 0.95rem; margin-bottom: 24px;">Authorized Supervisor Personnel Only</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("admin_login_form"):
            st.markdown("##### 🔑 Enter Supervisor Credentials")
            password = st.text_input("Password", type="password", placeholder="Enter password (default: admin123)")
            login_submitted = st.form_submit_button("🔓 Unlock Admin Queue", use_container_width=True)
            
            if login_submitted:
                if password == ADMIN_PASSWORD:
                    st.session_state.authenticated = True
                    st.toast("Access Granted! Welcome Supervisor.", icon="🔓")
                    st.rerun()
                else:
                    st.error("❌ Invalid Password. Access Denied.")
    st.stop()

# Authenticated Supervisor Dashboard
st.sidebar.markdown("### ⚙️ Navigation")
st.sidebar.caption("Logged in as **System Supervisor**")

st.sidebar.divider()
if st.sidebar.button("🔒 Lock Portal (Logout)", use_container_width=True):
    st.session_state.authenticated = False
    st.rerun()

st.sidebar.divider()
st.sidebar.info("🛡️ Human-in-the-Loop Security Active")
st.sidebar.caption("Rule Engine: All customer requests >= $100.00 are held for supervisor sign-off.")

pending_tickets = []
api_healthy = False

try:
    res = requests.get(f"{API_URL}/api/tickets/pending", timeout=5)
    if res.status_code == 200:
        pending_tickets = res.json().get("pending_tickets", [])
        api_healthy = True
except Exception:
    api_healthy = False

m1, m2, m3 = st.columns(3)
m1.metric("Pending Approval Queue", len(pending_tickets))
m2.metric("Auto-Approval Limit", "$100.00")
m3.metric("System Health", "Healthy ✅" if api_healthy else "Offline ⚠️")

st.divider()

if not api_healthy:
    st.error("❌ Unable to reach FastAPI backend server at `http://127.0.0.1:8000`. Please start backend server.")
elif not pending_tickets:
    st.success("🎉 All clear! No tickets currently awaiting supervisor review.")
else:
    st.markdown(f"### 📋 Escalation Queue ({len(pending_tickets)} Items Awaiting Review)")
    
    for ticket in pending_tickets:
        t_id = ticket["ticket_id"]
        o_id = ticket["order_id"]
        c_name = ticket["customer_name"]
        amount = ticket["requested_amount"]
        reason = ticket["reason"]
        
        with st.container():
            st.markdown(f"""
            <div class="tp-ticket-card">
                <div class="tp-ticket-header">
                    <div class="tp-ticket-title">Ticket #{t_id} — Order #{o_id}</div>
                    <span class="tp-badge-pending">PENDING APPROVAL</span>
                </div>
                <div class="tp-ticket-divider"></div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                    <div><span class="tp-detail-label">Customer Name:</span> <span class="tp-detail-val">{c_name}</span></div>
                    <div><span class="tp-detail-label">Requested Amount:</span> <span class="tp-amount-blue">${amount:.2f}</span></div>
                </div>
                <div style="margin-top: 10px;">
                    <span class="tp-detail-label">Reason Flagged:</span> 
                    <span class="tp-detail-val" style="color: #475569;">{reason}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            col_approve, col_reject = st.columns(2)
            
            with col_approve:
                if st.button(f"✅ Approve Refund (${amount:.2f})", key=f"approve_{t_id}", use_container_width=True):
                    try:
                        app_res = requests.post(
                            f"{API_URL}/api/tickets/approve",
                            json={"ticket_id": t_id, "decision": "APPROVE"},
                            timeout=5
                        )
                        if app_res.status_code == 200:
                            st.toast(f"Ticket #{t_id} APPROVED! SQLite database updated.", icon="✅")
                            st.rerun()
                        else:
                            st.error(f"Failed to approve ticket #{t_id}.")
                    except Exception as e:
                        st.error(f"Error executing approval: {e}")
            
            with col_reject:
                if st.button(f"❌ Reject Request", key=f"reject_{t_id}", use_container_width=True):
                    try:
                        rej_res = requests.post(
                            f"{API_URL}/api/tickets/approve",
                            json={"ticket_id": t_id, "decision": "REJECT"},
                            timeout=5
                        )
                        if rej_res.status_code == 200:
                            st.toast(f"Ticket #{t_id} REJECTED.", icon="❌")
                            st.rerun()
                        else:
                            st.error(f"Failed to reject ticket #{t_id}.")
                    except Exception as e:
                        st.error(f"Error executing rejection: {e}")
            
            st.write("")
