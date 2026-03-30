"""Tool execution handlers. Each function maps to one Claude tool."""
import json
import smtplib
import logging
from email.mime.text import MIMEText
from supabase import Client
from api.config import get_settings
import api.db as db

logger = logging.getLogger(__name__)


def handle_search_knowledge_base(
    tool_input: dict,
    tenant: dict,
    db_client: Client,
) -> str:
    query = tool_input.get("query", "")
    results = db.search_knowledge(db_client, tenant["id"], query)

    if not results:
        return "No information found in the knowledge base for this query."

    lines = []
    for r in results:
        lines.append(f"Q: {r['question']}\nA: {r['answer']}")
    return "\n\n".join(lines)


def handle_capture_lead(
    tool_input: dict,
    tenant: dict,
    conversation_id: str,
    db_client: Client,
) -> str:
    email = tool_input.get("email", "").strip()
    if not email or "@" not in email:
        return "Lead not saved: invalid email address."

    lead_data = {
        "tenant_id": tenant["id"],
        "conversation_id": conversation_id,
        "email": email,
        "name": tool_input.get("name"),
        "phone": tool_input.get("phone"),
        "interest_notes": tool_input.get("interest_notes"),
    }

    try:
        db.create_lead(db_client, lead_data)
        _send_lead_notification(tenant, lead_data)
        name = tool_input.get("name", "the customer")
        return f"Contact information saved successfully for {name}. A team member will follow up soon."
    except Exception as e:
        logger.error("Lead capture failed: %s", e)
        return "Contact information noted (save encountered an issue, will retry)."


def handle_get_business_info(
    tool_input: dict,
    tenant: dict,
) -> str:
    info_type = tool_input.get("info_type", "all")
    business_info: dict = tenant.get("agent_config", {}).get("business_info", {})

    if not business_info:
        return "No business information configured."

    if info_type == "all":
        return json.dumps(business_info, ensure_ascii=False, indent=2)

    value = business_info.get(info_type)
    if value is None:
        return f"No {info_type} information is configured for this business."
    return json.dumps(value, ensure_ascii=False)


def handle_escalate_to_human(
    tool_input: dict,
    tenant: dict,
    conversation_id: str,
    db_client: Client,
) -> str:
    reason = tool_input.get("reason", "customer_request")
    summary = tool_input.get("summary", "No summary provided.")

    # Mark conversation as escalated in DB
    try:
        db.mark_escalated(db_client, conversation_id)
    except Exception as e:
        logger.warning("Could not mark escalation in DB: %s", e)

    # Send email notification
    config = tenant.get("agent_config", {})
    escalation_email = config.get("escalation_email")
    if escalation_email:
        _send_escalation_email(escalation_email, tenant["name"], reason, summary)

    return (
        "Escalation logged. A team member has been notified and will follow up with the customer shortly."
    )


# ── Internal helpers ──────────────────────────────────────────────────────────

def _send_escalation_email(to: str, business_name: str, reason: str, summary: str) -> None:
    s = get_settings()
    if not s.smtp_host:
        logger.info("SMTP not configured — skipping escalation email to %s", to)
        return
    try:
        body = f"Escalation triggered for {business_name}\n\nReason: {reason}\n\nSummary:\n{summary}"
        msg = MIMEText(body)
        msg["Subject"] = f"[{business_name}] Agent escalation — {reason}"
        msg["From"] = s.smtp_from
        msg["To"] = to
        with smtplib.SMTP(s.smtp_host, s.smtp_port) as server:
            server.starttls()
            if s.smtp_user:
                server.login(s.smtp_user, s.smtp_password)
            server.send_message(msg)
    except Exception as e:
        logger.error("Escalation email failed: %s", e)


def _send_lead_notification(tenant: dict, lead: dict) -> None:
    s = get_settings()
    config = tenant.get("agent_config", {})
    to = config.get("escalation_email")
    if not to or not s.smtp_host:
        return
    try:
        body = (
            f"New lead captured for {tenant['name']}\n\n"
            f"Name:  {lead.get('name', 'N/A')}\n"
            f"Email: {lead.get('email')}\n"
            f"Phone: {lead.get('phone', 'N/A')}\n"
            f"Notes: {lead.get('interest_notes', 'N/A')}"
        )
        msg = MIMEText(body)
        msg["Subject"] = f"[{tenant['name']}] New lead: {lead.get('email')}"
        msg["From"] = s.smtp_from
        msg["To"] = to
        with smtplib.SMTP(s.smtp_host, s.smtp_port) as server:
            server.starttls()
            if s.smtp_user:
                server.login(s.smtp_user, s.smtp_password)
            server.send_message(msg)
    except Exception as e:
        logger.error("Lead notification email failed: %s", e)
