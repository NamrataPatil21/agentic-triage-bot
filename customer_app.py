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
search_order_id = st.sidebar.text_input("Order ID Search", placeholder="e.g. 1001")

if search_order_id:
    try:
        lookup_res = requests.get(f"{API_URL}/api/order/{search_order_id.strip()}")
        if lookup_res.status_code == 200:
            data = lookup_res.json()
            is_resolved = "RESOLVED" in data["status"]
            
            st.sidebar.success("Order Identified")
            st.sidebar.markdown(f"**Item:** {data['item']}")
            st.sidebar.markdown(f"**Customer:** {data['customer']}")
            st.sidebar.markdown(f"**Price:** ${data['price']:.2f}")
            status_flag = "🟢 " if is_resolved else "🔵 "
            st.sidebar.markdown(f"**Status:** `{status_flag + data['status']}`")
            warranty_text = "Valid" if data['warranty_valid'] else "Expired"
            st.sidebar.markdown(f"**Warranty:** `{warranty_text}`")
        else:
            st.sidebar.warning("Order ID not found.")
    except Exception:
        st.sidebar.error("Could not reach API backend.")

st.sidebar.divider()
st.sidebar.markdown("### 📊 System Status")
st.sidebar.success("Groq Llama-3.3 Engine: **Active**")

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
                res = requests.post(
                    f"{API_URL}/api/chat",
                    json={"message": user_input, "history": st.session_state.messages[:-1]}
                )
                if res.status_code == 200:
                    data = res.json()
                    bot_reply = data["bot_response"]
                    action = data["action_taken"]

                    st.markdown(bot_reply)
                    st.markdown(f'<div class="action-badge">⚙️ Executed: {action}</div>', unsafe_allow_html=True)
                    st.session_state.messages.append({"role": "assistant", "content": bot_reply})
                else:
                    st.error("Error communicating with backend.")
            except Exception as e:
                st.error(f"Failed to reach FastAPI backend: {e}")
