from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class LeadCreate(BaseModel):
    name: Optional[str] = None
    email: str
    phone: Optional[str] = None
    interest_notes: Optional[str] = None
    source_page: Optional[str] = None


class Lead(BaseModel):
    id: str
    tenant_id: str
    conversation_id: Optional[str]
    name: Optional[str]
    email: str
    phone: Optional[str]
    interest_notes: Optional[str]
    status: str
    created_at: datetime
