from fastapi import APIRouter, Depends
from api.db.supabase_client import get_db
import api.db as db_module

router = APIRouter(prefix="/admin")


def _get_db():
    return get_db()


@router.get("/tenants/{tenant_id}/leads")
def list_leads(tenant_id: str, limit: int = 200, db_client = Depends(_get_db)) -> list:
    return db_module.list_leads(db_client, tenant_id, limit)


@router.patch("/leads/{lead_id}")
def update_lead(lead_id: str, body: dict, db_client = Depends(_get_db)) -> dict:
    status = body.get("status", "new")
    return db_module.update_lead_status(db_client, lead_id, status)
