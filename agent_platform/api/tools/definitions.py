"""Single source of truth for all Claude tool definitions."""

TOOL_SEARCH_KNOWLEDGE = {
    "name": "search_knowledge_base",
    "description": (
        "Search the business's knowledge base for answers to customer questions. "
        "Use this FIRST before answering any factual question about the business: "
        "services, pricing, hours, policies, location, products, or FAQs. "
        "Always call this tool before saying 'I don't know'."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The customer question rephrased as a clear search query.",
            },
            "category": {
                "type": "string",
                "description": "Optional category filter.",
                "enum": ["hours", "pricing", "services", "policies", "contact", "other"],
            },
        },
        "required": ["query"],
    },
}

TOOL_CAPTURE_LEAD = {
    "name": "capture_lead",
    "description": (
        "Save a customer's contact information when they express purchase interest, "
        "ask to be contacted, request a quote, or want to book an appointment. "
        "Only call after the user has voluntarily provided their details. "
        "Email is required; name and phone are optional."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Customer's full name."},
            "email": {"type": "string", "description": "Customer's email address."},
            "phone": {"type": "string", "description": "Customer's phone number (optional)."},
            "interest_notes": {
                "type": "string",
                "description": "1-2 sentence summary of what the customer is interested in.",
            },
        },
        "required": ["email"],
    },
}

TOOL_GET_BUSINESS_INFO = {
    "name": "get_business_info",
    "description": (
        "Retrieve structured information about the business: "
        "address, phone number, social links, current promotions, and operating status."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "info_type": {
                "type": "string",
                "description": "What to retrieve.",
                "enum": ["contact", "location", "hours", "social_media", "promotions", "all"],
            },
        },
        "required": ["info_type"],
    },
}

TOOL_ESCALATE = {
    "name": "escalate_to_human",
    "description": (
        "Escalate the conversation to a human team member. Use when: "
        "(1) the customer is frustrated or angry, "
        "(2) after searching the knowledge base you still cannot answer, "
        "(3) the customer explicitly asks for a human, "
        "(4) the topic involves complaints, refunds, or legal matters. "
        "After calling this, tell the customer a team member will follow up soon."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "reason": {
                "type": "string",
                "enum": ["customer_request", "frustrated_customer", "unanswered_question", "complaint", "technical_issue"],
            },
            "summary": {
                "type": "string",
                "description": "2-3 sentence summary of the conversation for the human agent.",
            },
        },
        "required": ["reason", "summary"],
    },
}

# Registry: name → definition
ALL_TOOLS = {
    "search_knowledge_base": TOOL_SEARCH_KNOWLEDGE,
    "capture_lead": TOOL_CAPTURE_LEAD,
    "get_business_info": TOOL_GET_BUSINESS_INFO,
    "escalate_to_human": TOOL_ESCALATE,
}


def get_tools_for_tenant(tools_enabled: list[str]) -> list[dict]:
    return [ALL_TOOLS[t] for t in tools_enabled if t in ALL_TOOLS]
