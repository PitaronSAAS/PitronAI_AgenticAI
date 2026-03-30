from fastapi import APIRouter, Depends
from api.db.supabase_client import get_db
import api.db as db_module

router = APIRouter(prefix="/admin")


def _get_db():
    return get_db()


@router.get("/tenants/{tenant_id}/conversations")
def list_conversations(
    tenant_id: str,
    limit: int = 50,
    db_client = Depends(_get_db),
) -> list:
    return db_module.list_conversations(db_client, tenant_id, limit)


@router.get("/conversations/{conversation_id}/messages")
def get_messages(
    conversation_id: str,
    db_client = Depends(_get_db),
) -> list:
    return db_module.get_messages(db_client, conversation_id, limit=200)
