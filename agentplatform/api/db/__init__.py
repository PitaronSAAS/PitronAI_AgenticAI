from .supabase_client import get_db, get_tenant_cache, get_cache_lock
from .queries import (
    get_tenant_by_api_key, get_tenant_by_slug, list_tenants,
    create_tenant, create_agent_config, update_agent_config,
    get_or_create_conversation, get_messages, save_message,
    mark_escalated, list_conversations,
    search_knowledge, list_knowledge, create_knowledge_entry,
    update_knowledge_entry, delete_knowledge_entry,
    create_lead, list_leads, update_lead_status,
)
