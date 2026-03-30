import streamlit as st
import secrets
import json
from utils import get_supabase

st.title("👥 Clients")

if not st.session_state.get("authed"):
    st.error("Please log in from the main page.")
    st.stop()

sb = get_supabase()

# ── Existing clients ──────────────────────────────────────────────────────────
st.subheader("Active Clients")
tenants = sb.table("tenants").select("*, agent_configs(agent_name, primary_color)").order("created_at", desc=True).execute().data or []

if not tenants:
    st.info("No clients yet. Add one below.")
else:
    for t in tenants:
        cfg = (t.get("agent_configs") or [{}])[0]
        badge = "🟢" if t["status"] == "active" else "🔴"
        with st.expander(f"{badge} {t['name']} — /{t['slug']}  |  {t['plan'].upper()}"):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**API Key:** `{t['api_key']}`")
                st.markdown(f"**Agent Name:** {cfg.get('agent_name', '—')}")
                st.markdown(f"**Status:** {t['status']}")
            with col2:
                st.markdown("**Embed snippet:**")
                st.code(
                    f'<script src="https://api.pitronai.pro/widget/widget.js" '
                    f'data-agent-slug="{t["slug"]}"></script>',
                    language="html",
                )

st.divider()

# ── Add new client ────────────────────────────────────────────────────────────
st.subheader("Add New Client")
with st.form("new_client"):
    c1, c2 = st.columns(2)
    with c1:
        name     = st.text_input("Business Name *")
        slug     = st.text_input("URL Slug *", help="Lowercase letters, numbers, hyphens only. e.g. 'acme-bakery'")
        plan     = st.selectbox("Plan", ["starter", "pro", "enterprise"])
    with c2:
        agent_name   = st.text_input("Agent Name", value="Assistant")
        color        = st.color_picker("Brand Color", value="#6366f1")
        notif_email  = st.text_input("Notification Email", help="Receives lead and escalation alerts")

    persona = st.text_area(
        "Agent Persona / Instructions *",
        placeholder="You are a friendly assistant for Acme Bakery. You help customers with orders, hours, and menu questions.",
        height=100,
    )
    welcome = st.text_input("Welcome Message", value="Hi! How can I help you today?")
    biz_info_raw = st.text_area(
        "Business Info (JSON)",
        value='{\n  "hours": "Mon–Fri 9am–6pm",\n  "location": "123 Main St",\n  "phone": "+1 555-0100"\n}',
        height=120,
    )
    tools = st.multiselect(
        "Enabled Tools",
        ["search_knowledge_base", "capture_lead", "get_business_info", "escalate_to_human"],
        default=["search_knowledge_base", "capture_lead", "get_business_info"],
    )

    submitted = st.form_submit_button("Create Client", type="primary")

if submitted:
    if not name or not slug or not persona:
        st.error("Business Name, Slug, and Persona are required.")
    else:
        try:
            biz_info = json.loads(biz_info_raw)
        except json.JSONDecodeError:
            st.error("Business Info must be valid JSON.")
            st.stop()

        api_key = "pak_" + secrets.token_hex(24)

        tenant_res = sb.table("tenants").insert({
            "name": name, "slug": slug, "api_key": api_key,
            "plan": plan, "status": "active", "allowed_origins": [],
        }).execute()
        tenant_id = tenant_res.data[0]["id"]

        sb.table("agent_configs").insert({
            "tenant_id": tenant_id,
            "agent_name": agent_name,
            "persona_prompt": persona,
            "primary_color": color,
            "welcome_message": welcome,
            "business_info": biz_info,
            "tools_enabled": tools,
            "escalation_email": notif_email or None,
        }).execute()

        st.success(f"✅ Client **{name}** created!")
        st.code(api_key, language="text")
        st.code(
            f'<script src="https://api.pitronai.pro/widget/widget.js" '
            f'data-agent-slug="{slug}"></script>',
            language="html",
        )
        st.rerun()
