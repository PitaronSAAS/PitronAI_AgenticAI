from fastapi import APIRouter, HTTPException
from api.models import WidgetConfig
from api.db.supabase_client import get_db
from api.db.queries import get_tenant_by_slug

router = APIRouter()


@router.get("/widget/{slug}/config", response_model=WidgetConfig)
def widget_config(slug: str) -> WidgetConfig:
    """Public endpoint — no auth. Returns only safe, non-secret config for the JS widget."""
    tenant = get_tenant_by_slug(get_db(), slug)
    if not tenant:
        raise HTTPException(status_code=404, detail="Agent not found.")

    config = tenant.get("agent_config", {})
    return WidgetConfig(
        tenant_id=tenant["id"],
        agent_name=config.get("agent_name", "Assistant"),
        welcome_message=config.get("welcome_message", "Hi! How can I help you today?"),
        primary_color=config.get("primary_color", "#6366f1"),
        api_key=tenant["api_key"],
    )
