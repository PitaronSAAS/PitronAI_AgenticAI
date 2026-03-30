from fastapi import APIRouter, Depends
from api.models.knowledge import KnowledgeCreate, KnowledgeUpdate, KnowledgeEntry
from api.db.supabase_client import get_db
import api.db as db_module

router = APIRouter(prefix="/admin")


def _get_db():
    return get_db()


@router.get("/tenants/{tenant_id}/knowledge")
def list_knowledge(tenant_id: str, db_client = Depends(_get_db)) -> list:
    return db_module.list_knowledge(db_client, tenant_id)


@router.post("/tenants/{tenant_id}/knowledge", status_code=201)
def create_entry(
    tenant_id: str,
    body: KnowledgeCreate,
    db_client = Depends(_get_db),
) -> dict:
    data = body.model_dump()
    data["tenant_id"] = tenant_id
    # Auto-generate keywords from question words if none provided
    if not data.get("keywords"):
        data["keywords"] = [
            w.lower() for w in data["question"].split()
            if len(w) > 3
        ][:10]
    return db_module.create_knowledge_entry(db_client, data)


@router.patch("/tenants/{tenant_id}/knowledge/{entry_id}")
def update_entry(
    tenant_id: str,
    entry_id: str,
    body: KnowledgeUpdate,
    db_client = Depends(_get_db),
) -> dict:
    data = {k: v for k, v in body.model_dump().items() if v is not None}
    return db_module.update_knowledge_entry(db_client, entry_id, tenant_id, data)


@router.delete("/tenants/{tenant_id}/knowledge/{entry_id}", status_code=204)
def delete_entry(
    tenant_id: str,
    entry_id: str,
    db_client = Depends(_get_db),
) -> None:
    db_module.delete_knowledge_entry(db_client, entry_id, tenant_id)
