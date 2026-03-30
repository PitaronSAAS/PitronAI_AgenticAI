import streamlit as st

st.set_page_config(
    page_title="PitronAgent Admin",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Simple password gate ──────────────────────────────────────────────────────
ADMIN_PASSWORD = st.secrets.get("agent_platform", {}).get("admin_password", "changeme")

if "authed" not in st.session_state:
    st.session_state.authed = False

if not st.session_state.authed:
    st.title("🤖 PitronAgent Admin")
    pw = st.text_input("Password", type="password")
    if st.button("Login", type="primary"):
        if pw == ADMIN_PASSWORD:
            st.session_state.authed = True
            st.rerun()
        else:
            st.error("Wrong password.")
    st.stop()

st.sidebar.title("PitronAgent")
st.sidebar.caption("Admin Dashboard")
st.sidebar.divider()

st.title("🤖 PitronAgent — Overview")
st.info("Use the pages in the sidebar to manage clients, conversations, leads, and knowledge bases.")
