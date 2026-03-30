import streamlit as st
import pandas as pd
from utils import get_supabase

st.title("📋 Leads")

if not st.session_state.get("authed"):
    st.error("Please log in from the main page.")
    st.stop()

sb = get_supabase()

tenants = sb.table("tenants").select("id, name").order("name").execute().data or []
tenant_map = {t["name"]: t["id"] for t in tenants}

col1, col2 = st.columns([2, 1])
with col1:
    selected = st.selectbox("Client", ["— All —"] + list(tenant_map.keys()))
with col2:
    status_filter = st.selectbox("Status", ["all", "new", "contacted", "qualified", "closed"])

query = sb.table("leads").select("*").order("created_at", desc=True).limit(500)
if selected != "— All —":
    query = query.eq("tenant_id", tenant_map[selected])
if status_filter != "all":
    query = query.eq("status", status_filter)

leads = query.execute().data or []

if not leads:
    st.info("No leads captured yet.")
    st.stop()

df = pd.DataFrame(leads)
df["created_at"] = pd.to_datetime(df["created_at"]).dt.strftime("%Y-%m-%d %H:%M")

display_cols = [c for c in ["created_at", "name", "email", "phone", "interest_notes", "status"] if c in df.columns]
st.dataframe(df[display_cols], use_container_width=True, height=400)

col_a, col_b = st.columns(2)
with col_a:
    csv = df[display_cols].to_csv(index=False)
    st.download_button("⬇ Export CSV", csv, "leads.csv", "text/csv", use_container_width=True)
with col_b:
    st.metric("Total Leads", len(leads))
