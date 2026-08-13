import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="TriagePulse | Customer Support",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling - Enclosed safely inside Python string
CSS_STYLES = """
<style>
    .stApp {
        background-color: #F8FAFC;
    }
    .header-card {
        background: #0F172A;
        padding: 24px;
        border-radius: 12px;
        color: #FFFFFF;
        margin-bottom: 20px;
    }
    .action-badge {
        background: #EEF2FF;
        color: #4F46E5;
        font-size: 0.8rem;
        font-weight: 600;
        padding: 4px 10px;
        border-radius: 6px;
        border: 1px solid #C7D2FE;
        display: inline-block;
        margin-top: 6px;
    }
</style>
"""
st.markdown(CSS_STYLES, unsafe_allow_html=True)

# Top Banner Header
st.markdown("""
<div class="header-card">
    <h2 style="margin:0; font-weight:700;">🛡️ TriagePulse Support Portal</h2>
    <p style="margin:4px 0 0 0; color:#94A3B8;">Autonomous Tier-1 Customer Support & AI Diagnostics Engine</p>
</div>
""", unsafe_allow_html=True)

# Sidebar: Quick Lookup
st.sidebar.markdown("### 🔍 Live Order Lookup")
search_order_id = st.sidebar.text_input("Order ID Search", placeholder="e.g. 1001, 1002")

if search_order_id:
    try:
        lookup_res = requests.get(f"{API_URL}/api/order/{search_order_id.strip()}", timeout=4)
        if lookup_res.status_code == 200:
            data = lookup_res.json()
            status_text = data.get("status", "")
            tracking_id = data.get("tracking_number") or "N/A"
            replacement_id = data.get("replacement_order_id") or "N/A"
            
            is_replaced = "REPLACEMENT" in status_text or "DISPATCHED" in status_text
            is_refunded = "REFUND" in status_text or "RESOLVED" in status_text
            
            st.sidebar.success("Order Identified")
            st.sidebar.markdown(f"**Item:** {data.get('item', 'N/A')}")
            st.sidebar.markdown(f"**Customer:** {data.get('customer', 'N/A')}")
            st.sidebar.markdown(f"**Price:** ${data.get('price', 0.0):.2f}")
            
            if is_replaced:
                st.sidebar.markdown("**Status:** `🟢 REPLACEMENT DISPATCHED`")
                if replacement_id != "N/A":
                    st.sidebar.markdown(f"**Replacement Order #:** `{replacement_id}`")
                if tracking_id != "N/A":
                    st.sidebar.markdown(f"**Tracking ID:** `{tracking_id}`")
            elif is_refunded:
                st.sidebar.markdown("**Status:** `🟢 REFUND PROCESSED`")
                if tracking_id != "N/A":
                    st.sidebar.markdown(f"**Tracking Ref:** `{tracking_id}`")
            else:
                status_flag = "🟢 " if "RESOLVED" in status_text else "🔵 "
                st.sidebar.markdown(f"**Status:** `{status_flag}{status_text}`")
                
            warranty_text = "Valid ✅" if data.get("warranty_valid") else "Expired ⚠️"
            st.sidebar.markdown(f"**Warranty:** `{warranty_text}`")
        else:
            st.sidebar.warning(f"Order ID '{search_order_id}' not found.")
    except Exception:
        st.sidebar.error("Could not reach API backend.")

st.sidebar.divider()
st.sidebar.markdown("### 📊 System Status")
st.sidebar.success("Groq Llama-3.3 Engine: **Active**")

def render_resolution_card(res_data: dict):
    if not res_data:
        return
    repl_id = res_data.get("replacement_order_id", "N/A")
    trk_id = res_data.get("tracking_number", "N/A")
    est_del = res_data.get("estimated_delivery", "2-3 Business Days")
    status_raw = res_data.get("status", "REPLACEMENT_DISPATCHED")
    status_badge = status_raw.replace("_", " ")

    card_html = f"""
    <div style="background: #0F172A; border: 1px solid #1E293B; border-radius: 12px; padding: 18px; margin-top: 12px; color: #FFFFFF; font-family: sans-serif; box-shadow: 0 4px 14px rgba(15, 23, 42, 0.2);">
        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #334155; padding-bottom: 10px; margin-bottom: 12px;">
            <span style="font-size: 0.98rem; font-weight: 700; color: #F8FAFC;">🎉 Resolution Confirmation</span>
            <span style="background: #10B981; color: #064E3B; font-weight: 800; font-size: 0.75rem; padding: 4px 10px; border-radius: 9999px; text-transform: uppercase;">🟢 {status_badge}</span>
        </div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; font-size: 0.9rem;">
            <div>
                <span style="color: #94A3B8; display: block; font-size: 0.8rem; margin-bottom: 2px;">📦 Replacement Order #</span>
                <strong style="color: #60A5FA; font-size: 1.05rem;">{repl_id}</strong>
            </div>
            <div>
                <span style="color: #94A3B8; display: block; font-size: 0.8rem; margin-bottom: 2px;">🚚 Tracking ID</span>
                <code style="background: #1E293B; color: #38BDF8; padding: 3px 8px; border-radius: 6px; font-family: monospace; font-size: 0.92rem; border: 1px solid #334155;">{trk_id}</code>
            </div>
            <div style="grid-column: span 2; margin-top: 4px; background: #1E293B; padding: 10px 12px; border-radius: 8px; border: 1px solid #334155;">
                <span style="color: #94A3B8; display: block; font-size: 0.78rem;">📅 Estimated Delivery</span>
                <strong style="color: #F1F5F9; font-size: 0.95rem;">{est_del}</strong>
            </div>
        </div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)

# Main Content
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

# Session History
if "messages" not in st.session_state:
    st.session_state.messages = []

if prompt_to_add:
    st.session_state.messages.append({"role": "user", "content": prompt_to_add})

for msg in st.session_state.messages:
    avatar = "👤" if msg["role"] == "user" else "🤖"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])
        if msg["role"] == "assistant":
            if msg.get("action"):
                st.markdown(f'<div class="action-badge">⚙️ Executed: {msg["action"]}</div>', unsafe_allow_html=True)
            if msg.get("resolution_data"):
                render_resolution_card(msg["resolution_data"])

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
                clean_history = [
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages[:-1]
                    if isinstance(m, dict) and "role" in m and "content" in m
                ]
                res = requests.post(
                    f"{API_URL}/api/chat",
                    json={"message": user_input, "history": clean_history},
                    timeout=30
                )
                if res.status_code == 200:
                    data = res.json()
                    bot_reply = data.get("bot_response", "")
                    action = data.get("action_taken", "Information Provided")
                    res_data = data.get("resolution_data")

                    st.markdown(bot_reply)
                    st.markdown(f'<div class="action-badge">⚙️ Executed: {action}</div>', unsafe_allow_html=True)
                    if res_data:
                        render_resolution_card(res_data)

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": bot_reply,
                        "action": action,
                        "resolution_data": res_data
                    })
                else:
                    st.error("Error communicating with backend.")
            except Exception as e:
                st.error(f"Failed to reach FastAPI backend: {e}")
