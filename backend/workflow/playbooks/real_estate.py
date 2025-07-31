# FILE: backend/workflow/playbooks/real_estate.py
# --- NEW FILE ---
# Contains all conversational and time-based playbooks for the Real Estate vertical.

from .base import ConversationalPlaybook, PlaybookStep, IntentType

# --- Modern, Class-Based Conversational Playbooks ---

REALTOR_LONG_TERM_NURTURE = ConversationalPlaybook(
    name="Long-Term Nurture (Real Estate)",
    intent_type="LONG_TERM_NURTURE",
    steps=[
        PlaybookStep(delay_days=30, name="Helpful Content", prompt="Draft a helpful, no-pressure check-in. Share a relevant piece of market information or a valuable article about homeownership. Do not ask for a call or meeting."),
        PlaybookStep(delay_days=90, name="Personal Check-in", prompt="Draft a personal, warm check-in message. Ask if their timeline or real estate priorities have changed. Mention something from your last conversation to show you remember them."),
    ]
)
REALTOR_SHORT_TERM_LEAD = ConversationalPlaybook(
    name="Short-Term Lead Conversion (Real Estate)",
    intent_type="SHORT_TERM_LEAD",
    steps=[
        PlaybookStep(delay_days=3, name="Polite Follow-up", prompt="Draft a polite and brief follow-up message if the client has not responded. Gently nudge them to schedule a time to discuss their real estate needs."),
    ]
)

# --- Legacy, Dictionary-Based Playbooks (for time-based scheduling) ---

POTENTIAL_SELLER_PLAYBOOK = {
    "name": "Potential Seller Nurture",
    "triggers": ["potential_seller", "seller_lead"],
    "touchpoints": [
        {"id": "seller_value_offer", "name": "Initial Value Offer", "event_type": "date_offset", "offset_days": 7, "prompt": "<role>You are a friendly and professional real estate agent's assistant.</role>\n<task>Draft a brief, no-pressure SMS to a potential seller named {client_name}.</task>\n<instructions>Offer a complimentary, no-obligation home valuation to provide immediate value. Frame it as a simple way for them to understand their current equity position. Sign it from {user_full_name}.</instructions>"},
        {"id": "seller_market_update", "name": "Local Market Update", "event_type": "date_offset", "offset_days": 45, "prompt": "<role>You are a local real estate market expert.</role>\n<task>Draft a brief, insightful SMS to a potential seller named {client_name}.</task>\n<instructions>Mention a recent sale or an interesting market trend in their specific area. The client's notes are: '{notes}'. Use this to infer their neighborhood if possible. The goal is to show you are an expert on their hyper-local market. End with a soft question like 'Just wanted to keep you in the loop!'. Sign it from {user_full_name}.</instructions>"},
        {"id": "seller_helpful_tip", "name": "Helpful Tip", "event_type": "date_offset", "offset_days": 90, "prompt": "<role>You are a helpful real estate advisor.</role>\n<task>Draft a brief, value-add SMS to a potential seller named {client_name}.</task>\n<instructions>Offer a simple, actionable tip for homeowners considering selling, like 'a guide to the 5 best ROI home improvements'. Position it as free, helpful advice. Do not ask for a meeting. Sign it from {user_full_name}.</instructions>"}
    ]
}

FIRST_TIME_BUYER_PLAYBOOK = {
    "name": "First-Time Buyer Support",
    "triggers": ["first_time_buyer"],
    "touchpoints": [
        {"id": "ftb_welcome", "name": "Initial Welcome & Reassurance", "event_type": "date_offset", "offset_days": 3, "prompt": "<role>You are a friendly and professional real estate agent's assistant.</role>\n<task>Draft a brief, welcoming SMS to a new first-time home buyer named {client_name}.</task>\n<instructions>Reassure them that you're there to help with any questions, no matter how small. Keep it under 3 sentences. Sign it from {user_full_name}.</instructions>"},
        {"id": "ftb_30_day_checkin", "name": "30-Day Process Check-in", "event_type": "date_offset", "offset_days": 30, "prompt": "<role>You are a friendly and professional real estate agent's assistant.</role>\n<task>Draft a brief and casual SMS check-in for {client_name}.</task>\n<instructions>Ask them how the pre-approval process is going and if they have any questions about the next steps. Sign it from {user_full_name}.</instructions>"},
    ]
}

NEW_BUYER_PLAYBOOK = {
    "name": "New Buyer 6-Month Nurture", "triggers": ["buyer"],
    "touchpoints": [
        {"id": "new_buyer_initial_followup", "name": "Initial Follow-Up", "event_type": "date_offset", "offset_days": 7, "prompt": "<role>You are a friendly and professional real estate agent's assistant.</role>\n<task>Draft a brief, casual SMS to get in touch with a new client named {client_name}.</task>\n<instructions>Ask if they have any initial questions about the home buying process. The message must be friendly, professional, and very short (under 3 sentences). Sign it from {user_full_name}.</instructions>"},
        {"id": "new_buyer_90_day_checkin", "name": "90-Day Market Check-in", "event_type": "date_offset", "offset_days": 90, "prompt": "<role>You are a friendly and professional real estate agent's assistant.</role>\n<task>Draft a brief and casual SMS check-in for {client_name}. Your goal is to provide value.</task>\n<instructions>The message MUST incorporate a helpful insight about the current market or a tip relevant to their intel. Use the client's notes for general context: '{notes}'. Do NOT mention specific dates like birthdays or anniversaries. The message must be concise (under 160 characters). End with a question. Sign it from {user_full_name}.</instructions>"},
        {"id": "new_buyer_180_day_checkin", "name": "6-Month Check-in", "event_type": "date_offset", "offset_days": 180, "prompt": "<role>You are a friendly and professional real estate agent's assistant.</role>\n<task>Draft a brief and casual SMS to check in with {client_name}, who you started working with 6 months ago.</task>\n<instructions>Ask them how their search is going and if their priorities have changed at all. You can reference their initial interests from their notes: '{notes}'. Do NOT mention specific dates like birthdays or anniversaries. The message must be concise (under 160 characters). Sign it from {user_full_name}.</instructions>"},
        {"id": "personal_event_greeting", "name": "Personal Event Greeting", "event_type": "personal_event", "handled_events": ["birthday", "bday", "anniversary", "christmas", "new year's", "thanksgiving"], "prompt": "<role>You are a thoughtful personal assistant.</role>\n<task>Draft a warm, celebratory SMS message to {client_name} for their upcoming {event_name}.</task>\n<instructions>The client's notes are: '{notes}'. Use these notes to make the message feel personal and relevant to the event. Do NOT mention business. Keep the message concise and celebratory (under 3 sentences). Sign it from {user_full_name}.</instructions>"},
        {"id": "tax_day_reminder", "name": "Tax Day Reminder", "event_type": "personal_event", "handled_events": ["tax day"], "prompt": "<role>You are a helpful real estate advisor.</role>\n<task>Draft a brief, helpful SMS to {client_name} about the upcoming tax day.</task>\n<instructions>Frame the message as a helpful check-in. Ask if they need any settlement statements or documents from past transactions for their tax preparation. Keep it professional and value-oriented. Sign it from {user_full_name}.</instructions>"}
    ]
}

INVESTOR_PLAYBOOK = {
    "name": "Investor Nurture", "triggers": ["investor"],
    "touchpoints": [
        {"id": "investor_goal_alignment", "name": "Initial Goal Alignment", "event_type": "date_offset", "offset_days": 5, "prompt": "<role>You are a professional real estate investment advisor.</role>\n<task>Draft a concise, professional SMS to a new investor client named {client_name}.</task>\n<instructions>State that you're looking forward to helping them find properties that match their portfolio goals. Ask if they are currently focused more on cash flow or appreciation. Sign it from {user_full_name}.</instructions>"},
        {"id": "investor_quarterly_update", "name": "Quarterly Market Opportunities", "event_type": "date_offset", "offset_days": 90, "prompt": "<role>You are a professional real estate investment advisor.</role>\n<task>Draft a data-driven SMS to an investor client named {client_name}.</task>\n<instructions>Mention a specific, interesting market trend (e.g., rising rental rates in a certain neighborhood, a new development project). Ask if they'd be interested in a brief analysis of new opportunities. Sign it from {user_full_name}.</instructions>"}
    ]
}

PAST_SELLER_PLAYBOOK = {
    "name": "Past Seller Annual Check-in", "triggers": ["seller", "past_client"],
    "touchpoints": [
        {"id": "past_seller_home_anniversary", "name": "Home Anniversary", "event_type": "date_offset", "offset_days": 365, "prompt": "<role>You are a friendly and professional real estate agent's assistant.</role>\n<task>Draft a warm and celebratory 'Home Anniversary' message for {client_name}.</task>\n<instructions>Congratulate them on one year in their home. Ask them what their favorite part of living there has been. Sign it from {user_full_name}.</instructions>"},
        {"id": "past_seller_equity_update", "name": "Annual Equity Update", "event_type": "date_offset", "offset_days": 372, "prompt": "<role>You are a friendly and professional real estate agent's assistant.</role>\n<task>Draft a value-driven SMS to {client_name} offering a home equity update.</task>\n<instructions>Follow up on the recent home anniversary message. Offer to send them an updated analysis of their home's value, as the market has likely changed. Keep it professional and helpful. Sign it from {user_full_name}.</instructions>"}
    ]
}

CUSTOM_FREQUENCY_PLAYBOOK = {
    "name": "Client Preferred Cadence", "triggers": [],
    "touchpoints": [{"id": "custom_check_in", "name": "Custom Frequency Check-in", "event_type": "recurring", "recurrence": {"parse_from_notes": True}, "prompt": "<role>You are a friendly and professional real estate agent's assistant.</role>\n<task>Draft a brief and casual SMS check-in for {client_name}.</task>\n<instructions>Your goal is to be helpful and maintain the relationship. You can mention a local event or a general market insight. Client's notes for context: '{notes}'. Sign it from {user_full_name}.</instructions>"}]
}

PERSONAL_EVENT_PLAYBOOK = {
    "name": "Personal Event Reminder",
    "triggers": [],
    "touchpoints": [
        {
            "id": "personal_event_greeting",
            "name": "Personal Event Greeting",
            "event_type": "personal_event",
            "handled_events": ["birthday", "bday", "anniversary", "christmas", "new year's", "thanksgiving"],
            "prompt": "<role>You are a thoughtful personal assistant.</role>\n<task>Draft a warm, celebratory SMS message to {client_name} for their upcoming {event_name}.</task>\n<instructions>The client's notes are: '{notes}'. Use these notes to make the message feel personal and relevant to the event. Do NOT mention business unless the event is directly related. Sign it from {user_full_name}.</instructions>"
        },
        {
            "id": "tax_day_reminder",
            "name": "Tax Day Reminder",
            "event_type": "personal_event",
            "handled_events": ["tax day"],
            "prompt": "<role>You are a helpful real estate advisor.</role>\n<task>Draft a brief, helpful SMS to {client_name} about the upcoming tax day.</task>\n<instructions>Frame the message as a helpful check-in. Ask if they need any settlement statements or documents from past transactions for their tax preparation. Keep it professional and value-oriented. Sign it from {user_full_name}.</instructions>"
        }
    ]
}

# --- Consolidated list for the Relationship Planner ---
ALL_LEGACY_PLAYBOOKS = [
    CUSTOM_FREQUENCY_PLAYBOOK, PERSONAL_EVENT_PLAYBOOK, POTENTIAL_SELLER_PLAYBOOK,
    FIRST_TIME_BUYER_PLAYBOOK, INVESTOR_PLAYBOOK, NEW_BUYER_PLAYBOOK, PAST_SELLER_PLAYBOOK
]