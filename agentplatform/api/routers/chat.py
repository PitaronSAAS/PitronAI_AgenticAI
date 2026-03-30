import uuid
import logging
from fastapi import APIRouter, Depends, Request
from supabase import Client

from api.models import ChatRequest, ChatResponse
from api.dependencies import get_tenant, get_db_client
from api.services.agent import run_agent

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/chat", response_model=ChatResponse)
def chat(
    request: Request,
    body: ChatRequest,
    tenant: dict = Depends(get_tenant),
    db_client: Client = Depends(get_db_client),
) -> ChatResponse:
    request_id = str(uuid.uuid4())[:8]

    metadata = body.metadata or {}
    metadata["request_id"] = request_id

    response_text, lead_captured, escalated = run_agent(
        tenant=tenant,
        session_id=body.session_id,
        user_message=body.message,
        metadata=metadata,
        db_client=db_client,
    )

    return ChatResponse(
        message=response_text,
        session_id=body.session_id,
        lead_captured=lead_captured,
        escalated=escalated,
        request_id=request_id,
    )
