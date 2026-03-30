import streamlit as st
from utils import get_supabase

st.title("🧠 Knowledge Base")

if not st.session_state.get("authed"):
    st.error("Please log in from the main page.")
    st.stop()

sb = get_supabase()

tenants = sb.table("tenants").select("id, name").order("name").execute().data or []
if not tenants:
    st.warning("No clients yet. Add one in the Clients page.")
    st.stop()

tenant_map = {t["name"]: t["id"] for t in tenants}
selected = st.selectbox("Client", list(tenant_map.keys()))
tenant_id = tenant_map[selected]

# ── Existing entries ──────────────────────────────────────────────────────────
entries = (
    sb.table("knowledge_entries")
    .select("*")
    .eq("tenant_id", tenant_id)
    .order("category", nullsfirst=True)
    .execute()
    .data or []
)

st.subheader(f"Knowledge Entries — {len(entries)} total")

for e in entries:
    active_icon = "✅" if e.get("is_active", True) else "⛔"
    label = f"{active_icon} [{e.get('category') or 'General'}] {e['question'][:60]}"
    with st.expander(label):
        st.markdown(f"**Answer:** {e['answer']}")
        st.caption(f"Keywords: {', '.join(e.get('keywords') or [])}")
        if st.button("🗑 Delete", key=f"del_{e['id']}"):
            sb.table("knowledge_entries").delete().eq("id", e["id"]).execute()
            st.rerun()

st.divider()

# ── Add new entry ─────────────────────────────────────────────────────────────
st.subheader("Add Entry")
with st.form("add_entry"):
    c1, c2 = st.columns(2)
    with c1:
        question = st.text_input("Question *")
        category = st.text_input("Category", placeholder="hours / pricing / services / returns")
    with c2:
        keywords_raw = st.text_input("Keywords (comma-separated)", help="Used for fast search matching")

    answer = st.text_area("Answer *", height=100)

    if st.form_submit_button("Add Entry", type="primary"):
        if not question or not answer:
            st.error("Question and Answer are required.")
        else:
            keywords = [k.strip().lower() for k in keywords_raw.split(",") if k.strip()]
            if not keywords:
                # Auto-generate from question
                keywords = [w.lower() for w in question.split() if len(w) > 3][:10]

            sb.table("knowledge_entries").insert({
                "tenant_id": tenant_id,
                "question": question,
                "answer": answer,
                "category": category or None,
                "keywords": keywords,
                "is_active": True,
            }).execute()
            st.success("Entry added!")
            st.rerun()

st.divider()

# ── Bulk import ───────────────────────────────────────────────────────────────
st.subheader("Bulk Import (CSV)")
st.caption("CSV must have columns: `question`, `answer`, `category` (optional), `keywords` (optional, comma-separated)")
uploaded = st.file_uploader("Upload CSV", type="csv")
if uploaded:
    import pandas as pd
    try:
        df = pd.read_csv(uploaded)
        st.dataframe(df.head())
        if st.button("Import All Rows", type="primary"):
            rows = []
            for _, row in df.iterrows():
                q = str(row.get("question", "")).strip()
                a = str(row.get("answer", "")).strip()
                if not q or not a:
                    continue
                kw_raw = str(row.get("keywords", ""))
                kw = [k.strip().lower() for k in kw_raw.split(",") if k.strip()] if kw_raw else []
                if not kw:
                    kw = [w.lower() for w in q.split() if len(w) > 3][:10]
                rows.append({
                    "tenant_id": tenant_id,
                    "question": q, "answer": a,
                    "category": str(row.get("category", "")) or None,
                    "keywords": kw, "is_active": True,
                })
            sb.table("knowledge_entries").insert(rows).execute()
            st.success(f"Imported {len(rows)} entries!")
            st.rerun()
    except Exception as ex:
        st.error(f"CSV error: {ex}")
