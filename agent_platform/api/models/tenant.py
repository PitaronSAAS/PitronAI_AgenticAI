from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime


class AgentConfig(BaseModel):
    agent_name: str = "Assistant"
    persona_prompt: str
    primary_color: str = "#6366f1"
    welcome_message: str = "Hi! How can I help you today?"
    business_info: dict = {}
    tools_enabled: List[str] = ["search_knowledge_base", "capture_lead", "get_business_info"]
    escalation_email: Optional[str] = None
    max_turns: int = 20


class AgentConfigUpdate(BaseModel):
    agent_name: Optional[str] = None
    persona_prompt: Optional[str] = None
    primary_color: Optional[str] = None
    welcome_message: Optional[str] = None
    business_info: Optional[dict] = None
    tools_enabled: Optional[List[str]] = None
    escalation_email: Optional[str] = None
    max_turns: Optional[int] = None


class Tenant(BaseModel):
    id: str
    name: str
    slug: str
    api_key: str
    plan: str
    status: str
    allowed_origins: List[str]
    created_at: datetime
    agent_config: Optional[AgentConfig] = None


class TenantCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    slug: str = Field(..., min_length=2, max_length=80, pattern=r'^[a-z0-9-]+$')
    plan: str = "starter"
    allowed_origins: List[str] = []
    agent_config: AgentConfig


class WidgetConfig(BaseModel):
    """Public config returned to the JS widget — no secrets."""
    tenant_id: str
    agent_name: str
    welcome_message: str
    primary_color: str
    api_key: str              # included so the widget can authenticate /chat calls
