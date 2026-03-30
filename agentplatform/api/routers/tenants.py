import secrets
from fastapi import APIRouter, HTTPException, Depends
from supabase import Client
from api.models.tenant import TenantCreate
from api.db.supabase_client import get_db
import api.db as db_module

router = APIRouter(prefix="/admin")


def _get_db() -> Client:
    return get_db()


@router.get("/tenants")
def list_tenants(db_client: Client = Depends(_get_db)) -> list:
    return db_module.list_tenants(db_client)


@router.post("/tenants", status_code=201)
def create_tenant(body: TenantCreate, db_client: Client = Depends(_get_db)) -> dict:
    api_key = "pak_" + secrets.token_hex(24)

    tenant = db_module.create_tenant(db_client, {
        "name": body.name,
        "slug": body.slug,
        "api_key": api_key,
        "plan": body.plan,
        "allowed_origins": body.allowed_origins,
        "status": "active",
    })

    config_data = body.agent_config.model_dump()
    config_data["tenant_id"] = tenant["id"]
    db_module.create_agent_config(db_client, config_data)

    tenant["api_key"] = api_key
    tenant["embed_snippet"] = (
        f'<script src="https://api.pitronai.pro/widget/widget.js" '
        f'data-agent-slug="{body.slug}"></script>'
    )
    return tenant


@router.patch("/tenants/{tenant_id}/config")
def update_config(tenant_id: str, body: dict, db_client: Client = Depends(_get_db)) -> dict:
    # Invalidate cache for this tenant is handled by TTL expiry (max 60s lag)
    return db_module.update_agent_config(db_client, tenant_id, body)
