"""Typed query helpers. All DB access goes through these functions."""
from supabase import Client
from typing import Optional
from threading import Lock
from cachetools import TTLCache


# ── Tenant ───────────────────────────────────────────────────────────────────

def get_tenant_by_api_key(
    db: Client,
    api_key: str,
    cache: TTLCache,
    lock: Lock,
) -> Optional[dict]:
    """Returns merged tenant + agent_config dict, with 60-second in-process cache."""
    with lock:
        if api_key in cache:
            return cache[api_key]

    res = (
        db.table("tenants")
        .select("*, agent_configs(*)")
        .eq("api_key", api_key)
        .eq("status", "active")
        .single()
        .execute()
    )
    if not res.data:
        return None

    tenant = res.data
    # Flatten agent_configs list into a single dict
    configs = tenant.pop("agent_configs", [])
    tenant["agent_config"] = configs[0] if configs else {}

    with lock:
        cache[api_key] = tenant
    return tenant


def get_tenant_by_slug(db: Client, slug: str) -> Optional[dict]:
    res = (
        db.table("tenants")
        .select("*, agent_configs(*)")
        .eq("slug", slug)
        .eq("status", "active")
        .single()
        .execute()
    )
    if not res.data:
        return None
    tenant = res.data
    configs = tenant.pop("agent_configs", [])
    tenant["agent_config"] = configs[0] if configs else {}
    return tenant


def list_tenants(db: Client) -> list:
    res = db.table("tenants").select("*, agent_configs(agent_name, primary_color)").order("created_at", desc=True).execute()
    return res.data or []


def create_tenant(db: Client, data: dict) -> dict:
    res = db.table("tenants").insert(data).execute()
    return res.data[0]


def create_agent_config(db: Client, data: dict) -> dict:
    res = db.table("agent_configs").insert(data).execute()
    return res.data[0]


def update_agent_config(db: Client, tenant_id: str, data: dict) -> dict:
    res = (
        db.table("agent_configs")
        .update(data)
        .eq("tenant_id", tenant_id)
        .execute()
    )
    return res.data[0]


# ── Conversations & Messages ──────────────────────────────────────────────────

def get_or_create_conversation(db: Client, tenant_id: str, session_id: str, metadata: dict) -> dict:
    res = (
        db.table("conversations")
        .select("*")
        .eq("tenant_id", tenant_id)
        .eq("session_id", session_id)
        .single()
        .execute()
    )
    if res.data:
        # Bump last_activity
        db.table("conversations").update({"last_activity": "now()"}).eq("id", res.data["id"]).execute()
        return res.data

    new = db.table("conversations").insert({
        "tenant_id": tenant_id,
        "session_id": session_id,
        "metadata": metadata or {},
    }).execute()
    return new.data[0]


def get_messages(db: Client, conversation_id: str, limit: int = 40) -> list:
    res = (
        db.table("messages")
        .select("role, content")
        .eq("conversation_id", conversation_id)
        .order("created_at", desc=False)
        .limit(limit)
        .execute()
    )
    return res.data or []


def save_message(db: Client, conversation_id: str, role: str, content: str) -> None:
    db.table("messages").insert({
        "conversation_id": conversation_id,
        "role": role,
        "content": content,
    }).execute()
    db.table("conversations").update({"turn_count": "turn_count + 1", "last_activity": "now()"}).eq("id", conversation_id).execute()


def mark_escalated(db: Client, conversation_id: str) -> None:
    db.table("conversations").update({"is_escalated": True}).eq("id", conversation_id).execute()


def list_conversations(db: Client, tenant_id: str, limit: int = 50) -> list:
    res = (
        db.table("conversations")
        .select("*, messages(count)")
        .eq("tenant_id", tenant_id)
        .order("last_activity", desc=True)
        .limit(limit)
        .execute()
    )
    return res.data or []


# ── Knowledge base ────────────────────────────────────────────────────────────

def search_knowledge(db: Client, tenant_id: str, query: str, limit: int = 5) -> list:
    """Keyword-based search using GIN index on keywords array.
    Falls back to full text scan if no keyword matches.
    """
    query_words = [w.lower() for w in query.split() if len(w) > 2]

    if query_words:
        # GIN array overlap: keywords && ARRAY[...]
        res = (
            db.table("knowledge_entries")
            .select("question, answer, keywords, category")
            .eq("tenant_id", tenant_id)
            .eq("is_active", True)
            .contains("keywords", query_words[:5])   # overlap with top 5 query words
            .limit(limit)
            .execute()
        )
        if res.data:
            return res.data

    # Fallback: scan all and score locally (cheap for small knowledge bases)
    all_res = (
        db.table("knowledge_entries")
        .select("question, answer, keywords, category")
        .eq("tenant_id", tenant_id)
        .eq("is_active", True)
        .execute()
    )
    entries = all_res.data or []
    query_lower = query.lower()
    scored = []
    for e in entries:
        text = (e["question"] + " " + e["answer"]).lower()
        score = sum(1 for w in query_words if w in text)
        if score > 0:
            scored.append((score, e))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [e for _, e in scored[:limit]]


def list_knowledge(db: Client, tenant_id: str) -> list:
    res = (
        db.table("knowledge_entries")
        .select("*")
        .eq("tenant_id", tenant_id)
        .order("created_at", desc=False)
        .execute()
    )
    return res.data or []


def create_knowledge_entry(db: Client, data: dict) -> dict:
    res = db.table("knowledge_entries").insert(data).execute()
    return res.data[0]


def update_knowledge_entry(db: Client, entry_id: str, tenant_id: str, data: dict) -> dict:
    res = (
        db.table("knowledge_entries")
        .update(data)
        .eq("id", entry_id)
        .eq("tenant_id", tenant_id)
        .execute()
    )
    return res.data[0]


def delete_knowledge_entry(db: Client, entry_id: str, tenant_id: str) -> None:
    db.table("knowledge_entries").delete().eq("id", entry_id).eq("tenant_id", tenant_id).execute()


# ── Leads ─────────────────────────────────────────────────────────────────────

def create_lead(db: Client, data: dict) -> dict:
    res = db.table("leads").insert(data).execute()
    return res.data[0]


def list_leads(db: Client, tenant_id: str, limit: int = 200) -> list:
    res = (
        db.table("leads")
        .select("*")
        .eq("tenant_id", tenant_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return res.data or []


def update_lead_status(db: Client, lead_id: str, status: str) -> dict:
    res = db.table("leads").update({"status": status}).eq("id", lead_id).execute()
    return res.data[0]
