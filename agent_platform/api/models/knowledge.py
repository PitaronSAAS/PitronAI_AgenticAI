from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class KnowledgeCreate(BaseModel):
    category: Optional[str] = None
    question: str
    answer: str
    keywords: List[str] = []


class KnowledgeUpdate(BaseModel):
    category: Optional[str] = None
    question: Optional[str] = None
    answer: Optional[str] = None
    keywords: Optional[List[str]] = None
    is_active: Optional[bool] = None


class KnowledgeEntry(BaseModel):
    id: str
    tenant_id: str
    category: Optional[str]
    question: str
    answer: str
    keywords: List[str]
    is_active: bool
    created_at: datetime
