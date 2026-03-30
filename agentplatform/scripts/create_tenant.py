"""
CLI to quickly create a tenant without the admin dashboard.

Usage:
  python scripts/create_tenant.py --name "Acme Bakery" --slug acme-bakery --email alerts@acme.com
"""
import argparse, secrets, sys, os
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

def _load_secrets() -> dict:
    path = Path.home() / ".streamlit" / "secrets.toml"
    with open(path, "rb") as f:
        return tomllib.load(f)

from supabase import create_client

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--name",  required=True)
    p.add_argument("--slug",  required=True)
    p.add_argument("--email", default="")
    p.add_argument("--plan",  default="starter")
    args = p.parse_args()

    s   = _load_secrets()
    url = s["supabase"]["url"]
    key = s["supabase"].get("service_key") or s["supabase"]["key"]
    sb  = create_client(url, key)

    api_key = "pak_" + secrets.token_hex(24)

    t = sb.table("tenants").insert({
        "name": args.name, "slug": args.slug,
        "api_key": api_key, "plan": args.plan,
        "status": "active", "allowed_origins": [],
    }).execute().data[0]

    sb.table("agent_configs").insert({
        "tenant_id": t["id"],
        "agent_name": "Assistant",
        "persona_prompt": f"You are a helpful assistant for {args.name}.",
        "welcome_message": "Hi! How can I help you today?",
        "primary_color": "#6366f1",
        "business_info": {},
        "tools_enabled": ["search_knowledge_base", "capture_lead", "get_business_info"],
        "escalation_email": args.email or None,
    }).execute()

    print(f"\n✅ Tenant created: {args.name}")
    print(f"   API Key : {api_key}")
    print(f"   Embed   : <script src=\"https://pitronai.pro/widget/widget.js\" data-agent-slug=\"{args.slug}\"></script>\n")

if __name__ == "__main__":
    main()
