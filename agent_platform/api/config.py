from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Anthropic
    anthropic_api_key: str
    claude_model: str = "claude-sonnet-4-6"
    max_tokens: int = 1024
    max_tool_iterations: int = 5

    # Supabase
    supabase_url: str
    supabase_service_key: str   # bypasses RLS — server-side only
    supabase_anon_key: str

    # App
    environment: str = "production"
    tenant_cache_ttl: int = 60          # seconds to cache tenant config in memory
    rate_limit_rpm: int = 30            # requests per minute per tenant

    # Email (optional — for escalation notifications)
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "agent@pitronai.pro"


@lru_cache
def get_settings() -> Settings:
    return Settings()
