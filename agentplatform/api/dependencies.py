"""FastAPI dependency injection."""
from fastapi import Header, HTTPException, status
import api.db as db_module
from api.db.supabase_client import get_db, get_tenant_cache, get_cache_lock


def get_db_client():
    return get_db()


def get_tenant(
    x_api_key: str = Header(..., alias="X-API-Key"),
    db_client = None,
) -> dict:
    """Resolve and validate tenant from API key header."""
    if db_client is None:
        db_client = get_db()
    tenant = db_module.get_tenant_by_api_key(
        db_client,
        x_api_key,
        get_tenant_cache(),
        get_cache_lock(),
    )
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or inactive API key.",
        )
    return tenant
