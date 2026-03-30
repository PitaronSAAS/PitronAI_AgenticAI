"""Core agentic loop. Runs inside a single HTTP request — no background tasks."""
import json
import logging
from datetime import date
from anthropic import Anthropic
from supabase import Client

from api.config import get_settings
from api.tools.definitions import get_tools_for_tenant
from api.tools.handlers import (
    handle_search_knowledge_base,
    handle_capture_lead,
    handle_get_business_info,
    handle_escalate_to_human,
)
import api.db as db

logger = logging.getLogger(__name__)

_FALLBACK = "I'm having a little trouble right now. Please try again in a moment."


def build_system_prompt(tenant: dict) -> str:
    config = tenant.get("agent_config", {})
    persona = config.get("persona_prompt", "You are a helpful business assistant.")
    agent_name = config.get("agent_name", "Assistant")
    business_name = tenant["name"]
    today = date.today().isoformat()

    return f"""{persona}

---
You are {agent_name}, the AI assistant for {business_name}.
Today's date is {today}.

## Rules
- Only answer questions about {business_name} and topics directly relevant to helping their customers.
- Always search the knowledge base before answering any factual question about the business.
- Never fabricate information (hours, prices, policies). Use tools instead.
- Capture lead information only when the user voluntarily provides it or asks to be contacted.
- Escalate to a human when you cannot help, the customer is frustrated, or they explicitly ask.
- Keep replies concise: 1-3 short paragraphs or a brief list. Avoid walls of text.
- Match the language the customer writes in.
"""


def run_agent(
    tenant: dict,
    session_id: str,
    user_message: str,
    metadata: dict,
    db_client: Client,
) -> tuple[str, bool, bool]:
    """
    Run one agentic turn.

    Returns:
        (response_text, lead_captured, escalated)
    """
    settings = get_settings()
    client = Anthropic(api_key=settings.anthropic_api_key)
    config = tenant.get("agent_config", {})

    # Get or create conversation
    conversation = db.get_or_create_conversation(db_client, tenant["id"], session_id, metadata)
    conversation_id = conversation["id"]

    # Guard: max turns reached
    max_turns = config.get("max_turns", 20)
    if conversation["turn_count"] >= max_turns:
        return (
            "We've reached the conversation limit. Please start a new chat or contact us directly.",
            False,
            False,
        )

    # Load history (last 40 messages to bound token usage)
    history = db.get_messages(db_client, conversation_id, limit=40)

    # Persist user message
    db.save_message(db_client, conversation_id, "user", user_message)

    # Build messages for Claude
    messages = history + [{"role": "user", "content": user_message}]

    # Get tools for this tenant
    tools = get_tools_for_tenant(config.get("tools_enabled", []))

    lead_captured = False
    escalated = False

    # ── Agentic loop ──────────────────────────────────────────────────────────
    for iteration in range(settings.max_tool_iterations):
        kwargs = dict(
            model=settings.claude_model,
            max_tokens=settings.max_tokens,
            system=build_system_prompt(tenant),
            messages=messages,
        )
        if tools:
            kwargs["tools"] = tools

        try:
            response = client.messages.create(**kwargs)
        except Exception as e:
            logger.error("Anthropic API error: %s", e)
            return _FALLBACK, False, False

        if response.stop_reason == "end_turn":
            text = _extract_text(response)
            db.save_message(db_client, conversation_id, "assistant", text)
            return text, lead_captured, escalated

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue

                result = _dispatch_tool(
                    block.name,
                    block.input,
                    tenant,
                    conversation_id,
                    db_client,
                )

                # Track side effects
                if block.name == "capture_lead":
                    lead_captured = True
                if block.name == "escalate_to_human":
                    escalated = True

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                })

            # Extend conversation with tool turn
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})
            continue

        # Unexpected stop reason
        break

    # Max iterations reached — extract whatever text exists
    text = _extract_text_from_messages(messages) or _FALLBACK
    db.save_message(db_client, conversation_id, "assistant", text)
    return text, lead_captured, escalated


# ── Helpers ───────────────────────────────────────────────────────────────────

def _extract_text(response) -> str:
    for block in response.content:
        if hasattr(block, "text") and block.text:
            return block.text
    return _FALLBACK


def _extract_text_from_messages(messages: list) -> str:
    for msg in reversed(messages):
        if msg.get("role") == "assistant":
            content = msg.get("content", "")
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                for block in content:
                    if hasattr(block, "text"):
                        return block.text
    return ""


def _dispatch_tool(
    name: str,
    tool_input: dict,
    tenant: dict,
    conversation_id: str,
    db_client: Client,
) -> str:
    try:
        if name == "search_knowledge_base":
            return handle_search_knowledge_base(tool_input, tenant, db_client)
        if name == "capture_lead":
            return handle_capture_lead(tool_input, tenant, conversation_id, db_client)
        if name == "get_business_info":
            return handle_get_business_info(tool_input, tenant)
        if name == "escalate_to_human":
            return handle_escalate_to_human(tool_input, tenant, conversation_id, db_client)
        return f"Unknown tool: {name}"
    except Exception as e:
        logger.error("Tool %s failed: %s", name, e)
        return f"Tool execution error: {e}"
