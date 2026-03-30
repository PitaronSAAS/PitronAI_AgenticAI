from pydantic import BaseModel, Field
from typing import Optional


class ChatRequest(BaseModel):
    session_id: str = Field(..., min_length=8, max_length=64)
    message: str = Field(..., min_length=1, max_length=2000)
    metadata: Optional[dict] = None       # page_url, referrer, etc.


class ChatResponse(BaseModel):
    message: str
    session_id: str
    lead_captured: bool = False
    escalated: bool = False
    request_id: Optional[str] = None
