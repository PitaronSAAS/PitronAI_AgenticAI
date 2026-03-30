"""
Reads secrets from ~/.streamlit/secrets.toml — the same file used by the
Streamlit store, so there is only one secrets file to manage on the droplet.
"""
import sys
from pathlib import Path
from functools import lru_cache

if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomllib
    except ImportError:
        import tomli as tomllib  # pip install tomli on Python < 3.11


def _load_toml() -> dict:
    path = Path.home() / ".streamlit" / "secrets.toml"
    if not path.exists():
        raise FileNotFoundError(f"secrets.toml not found at {path}")
    with open(path, "rb") as f:
        return tomllib.load(f)


class Settings:
    def __init__(self):
        s = _load_toml()

        # Anthropic
        self.anthropic_api_key: str = s["anthropic"]["api_key"]
        self.claude_model: str = "claude-sonnet-4-6"
        self.max_tokens: int = 1024
        self.max_tool_iterations: int = 5

        # Supabase — use service_key if present, fall back to key
        self.supabase_url: str = s["supabase"]["url"]
        self.supabase_service_key: str = s["supabase"].get("service_key") or s["supabase"]["key"]
        self.supabase_anon_key: str = s["supabase"]["key"]

        # App
        self.environment: str = "production"
        self.tenant_cache_ttl: int = 60     # seconds to cache tenant in memory
        self.rate_limit_rpm: int = 30        # requests per minute per tenant

        # Admin dashboard password
        self.admin_password: str = s.get("agent_platform", {}).get("admin_password", "changeme")

        # Email — optional, for escalation/lead notifications
        smtp = s.get("smtp", {})
        self.smtp_host: str = smtp.get("host", "")
        self.smtp_port: int = smtp.get("port", 587)
        self.smtp_user: str = smtp.get("user", "")
        self.smtp_password: str = smtp.get("password", "")
        self.smtp_from: str = smtp.get("from", "agent@pitronai.pro")


@lru_cache
def get_settings() -> Settings:
    return Settings()
