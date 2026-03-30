import streamlit as st
from utils import get_supabase

st.title("💬 Conversations")

if not st.session_state.get("authed"):
    st.error("Please log in from the main page.")
    st.stop()

sb = get_supabase()

tenants = sb.table("tenants").select("id, name").order("name").execute().data or []
tenant_map = {t["name"]: t["id"] for t in tenants}

selected = st.selectbox("Client", ["— All —"] + list(tenant_map.keys()))

query = sb.table("conversations").select("*").order("last_activity", desc=True).limit(100)
if selected != "— All —":
    query = query.eq("tenant_id", tenant_map[selected])

convos = query.execute().data or []

if not convos:
    st.info("No conversations yet.")
    st.stop()

st.caption(f"{len(convos)} conversations")

for c in convos:
    escalated = "🔴 Escalated" if c.get("is_escalated") else ""
    label = f"Session `{c['session_id'][:14]}…`  |  {c['turn_count']} turns  |  {c['last_activity'][:16]}  {escalated}"
    with st.expander(label):
        msgs = sb.table("messages").select("role, content, created_at").eq("conversation_id", c["id"]).order("created_at").execute().data or []
        for m in msgs:
            icon = "🧑" if m["role"] == "user" else "🤖"
            st.markdown(f"**{icon} {m['role'].title()}** _{m['created_at'][11:16]}_")
            st.markdown(f"> {m['content']}")
