# ---
# File Path: backend/workflow/relationship_playbooks.py
# --- V6: Added Potential Seller Playbook ---
# This version adds a strategic playbook for nurturing seller leads.
# ---

import logging
from typing import List, Dict, Any, Optional, Literal

# --- ADDED: Define conversational intent types ---
IntentType = Literal["LONG_TERM_NURTURE", "SHORT_TERM_LEAD"]

# --- ADDED: A structured class for playbooks for better type safety and clarity ---
class PlaybookStep:
    def __init__(self, delay_days: int, prompt: str, name: str, event_type: str = "date_offset"):
        self.delay_days = delay_days
        self.prompt = prompt
        self.name = name
        self.event_type = event_type

class ConversationalPlaybook:
    def __init__(self, name: str, intent_type: IntentType, steps: List[PlaybookStep]):
        self.name = name
        self.intent_type = intent_type
        self.steps = steps

# --- ADDED: New Conversational Playbooks ---
LONG_TERM_NURTURE_PLAYBOOK = ConversationalPlaybook(
    name="Long-Term Nurture",
    intent_type="LONG_TERM_NURTURE",
    steps=[
        PlaybookStep(delay_days=0, name="Initial Acknowledgement", prompt="Acknowledge the client's long-term timeline and confirm you will stay in touch. Keep it brief and professional."),
        PlaybookStep(delay_days=30, name="Helpful Content", prompt="Draft a helpful, no-pressure check-in. Share a relevant piece of market information or a valuable article. Do not ask for a call or meeting."),
        PlaybookStep(delay_days=90, name="Personal Check-in", prompt="Draft a personal, warm check-in message. Ask if their timeline or priorities have changed. Mention something from your last conversation to show you remember them."),
    ]
)

SHORT_TERM_LEAD_PLAYBOOK = ConversationalPlaybook(
    name="Short-Term Lead Conversion",
    intent_type="SHORT_TERM_LEAD",
    steps=[
        PlaybookStep(delay_days=0, name="Immediate Engagement", prompt="Acknowledge the client's immediate interest and propose a specific time for a call or meeting in the next 1-2 days to discuss their needs."),
        PlaybookStep(delay_days=3, name="Polite Follow-up", prompt="Draft a polite and brief follow-up message if the client has not responded. Gently nudge them to schedule a time."),
    ]
)

# --- ADDED: A registry for the new conversational playbooks ---
CONVERSATIONAL_PLAYBOOK_REGISTRY: Dict[IntentType, ConversationalPlaybook] = {
    "LONG_TERM_NURTURE": LONG_TERM_NURTURE_PLAYBOOK,
    "SHORT_TERM_LEAD": SHORT_TERM_LEAD_PLAYBOOK,
}

def get_playbook_for_intent(intent: IntentType) -> Optional[ConversationalPlaybook]:
    """Selects the appropriate conversational playbook based on the AI's analysis."""
    logging.info(f"PLAYBOOKS: Retrieving playbook for intent '{intent}'")
    return CONVERSATIONAL_PLAYBOOK_REGISTRY.get(intent)

POTENTIAL_SELLER_PLAYBOOK = {
    "name": "Potential Seller Nurture",
    "triggers": ["potential_seller", "seller_lead"],
    "touchpoints": [
        {
            "name": "Initial Value Offer",
            "event_type": "date_offset",
            "offset_days": 7,
            "prompt": (
                "<role>You are a friendly and professional real estate agent's assistant.</role>\n"
                "<task>Draft a brief, no-pressure SMS to a potential seller named {client_name}.</task>\n"
                "<instructions>Offer a complimentary, no-obligation home valuation to provide immediate value. Frame it as a simple way for them to understand their current equity position. Sign it from {realtor_name}.</instructions>"
            )
        },
        {
            "name": "Local Market Update",
            "event_type": "date_offset",
            "offset_days": 45,
            "prompt": (
                "<role>You are a local real estate market expert.</role>\n"
                "<task>Draft a brief, insightful SMS to a potential seller named {client_name}.</task>\n"
                "<instructions>Mention a recent sale or an interesting market trend in their specific area. The client's notes are: '{notes}'. Use this to infer their neighborhood if possible. The goal is to show you are an expert on their hyper-local market. End with a soft question like 'Just wanted to keep you in the loop!'. Sign it from {realtor_name}.</instructions>"
            )
        },
        {
            "name": "Helpful Tip",
            "event_type": "date_offset",
            "offset_days": 90,
            "prompt": (
                "<role>You are a helpful real estate advisor.</role>\n"
                "<task>Draft a brief, value-add SMS to a potential seller named {client_name}.</task>\n"
                "<instructions>Offer a simple, actionable tip for homeowners considering selling, like 'a guide to the 5 best ROI home improvements'. Position it as free, helpful advice. Do not ask for a meeting. Sign it from {realtor_name}.</instructions>"
            )
        }
    ]
}


FIRST_TIME_BUYER_PLAYBOOK = {
    "name": "First-Time Buyer Support",
    "triggers": ["first_time_buyer"],
    "touchpoints": [
        {
            "name": "Initial Welcome & Reassurance",
            "event_type": "date_offset",
            "offset_days": 3,
            "prompt": (
                "<role>You are a friendly and professional real estate agent's assistant.</role>\n"
                "<task>Draft a brief, welcoming SMS to a new first-time home buyer named {client_name}.</task>\n"
                "<instructions>Reassure them that you're there to help with any questions, no matter how small. Keep it under 3 sentences. Sign it from {realtor_name}.</instructions>"
            )
        },
        {
            "name": "30-Day Process Check-in",
            "event_type": "date_offset",
            "offset_days": 30,
            "prompt": (
                "<role>You are a friendly and professional real estate agent's assistant.</role>\n"
                "<task>Draft a brief and casual SMS check-in for {client_name}.</task>\n"
                "<instructions>Ask them how the pre-approval process is going and if they have any questions about the next steps. Sign it from {realtor_name}.</instructions>"
            )
        },
        {
            "name": "Birthday Greeting",
            "event_type": "birthday",
            "prompt": (
                "<role>You are a friendly and professional real estate agent's assistant.</role>\n"
                "<task>Draft a warm and personal birthday SMS for {client_name}.</task>\n"
                "<instructions>You MUST reference one of the client's specific interests from their notes to make the message feel personal. The client's notes are: '{notes}'. Do NOT mention real estate. The message should be celebratory and brief. Sign it from {realtor_name}.</instructions>"
            )
        },
    ]
}

NEW_BUYER_PLAYBOOK = {
    "name": "New Buyer 6-Month Nurture",
    "triggers": ["buyer"],
    "touchpoints": [
        {
            "name": "Initial Follow-Up",
            "event_type": "date_offset",
            "offset_days": 7,
            "prompt": (
                "<role>You are a friendly and professional real estate agent's assistant.</role>\n"
                "<task>Draft a brief, casual SMS to get in touch with a new client named {client_name}.</task>\n"
                "<instructions>Ask if they have any initial questions about the home buying process. Keep it under 2 sentences. Sign it from {realtor_name}.</instructions>"
            )
        },
        {
            "name": "90-Day Market Check-in",
            "event_type": "date_offset",
            "offset_days": 90,
            "prompt": (
                "<role>You are a friendly and professional real estate agent's assistant.</role>\n"
                "<task>Draft a brief and casual SMS check-in for {client_name}. Your goal is to provide value.</task>\n"
                "<instructions>The message MUST incorporate a helpful insight about the current market or a tip relevant to their intel. The client's notes are: '{notes}'. End with a question. Sign it from {realtor_name}.</instructions>"
            )
        },
        {
            "name": "Birthday Greeting",
            "event_type": "birthday",
            "prompt": (
                "<role>You are a friendly and professional real estate agent's assistant.</role>\n"
                "<task>Draft a warm and personal birthday SMS for {client_name}.</task>\n"
                "<instructions>You MUST reference one of the client's specific interests from their notes to make the message feel personal. The client's notes are: '{notes}'. Do NOT mention real estate. The message should be celebratory and brief. Sign it from {realtor_name}.</instructions>"
            )
        },
        {
            "name": "6-Month Check-in",
            "event_type": "date_offset",
            "offset_days": 180,
            "prompt": (
                "<role>You are a friendly and professional real estate agent's assistant.</role>\n"
                "<task>Draft a brief and casual SMS to check in with {client_name}, who you started working with 6 months ago.</task>\n"
                "<instructions>Ask them how their search is going and if their priorities have changed at all. Reference their initial interest in '{notes}' if possible. Sign it from {realtor_name}.</instructions>"
            )
        }
    ]
}

INVESTOR_PLAYBOOK = {
    "name": "Investor Nurture",
    "triggers": ["investor"],
    "touchpoints": [
        {
            "name": "Initial Goal Alignment",
            "event_type": "date_offset",
            "offset_days": 5,
            "prompt": (
                "<role>You are a professional real estate investment advisor.</role>\n"
                "<task>Draft a concise, professional SMS to a new investor client named {client_name}.</task>\n"
                "<instructions>State that you're looking forward to helping them find properties that match their portfolio goals. Ask if they are currently focused more on cash flow or appreciation. Sign it from {realtor_name}.</instructions>"
            )
        },
        {
            "name": "Quarterly Market Opportunities",
            "event_type": "date_offset",
            "offset_days": 90,
            "prompt": (
                "<role>You are a professional real estate investment advisor.</role>\n"
                "<task>Draft a data-driven SMS to an investor client named {client_name}.</task>\n"
                "<instructions>Mention a specific, interesting market trend (e.g., rising rental rates in a certain neighborhood, a new development project). Ask if they'd be interested in a brief analysis of new opportunities. Sign it from {realtor_name}.</instructions>"
            )
        }
    ]
}


PAST_SELLER_PLAYBOOK = {
    "name": "Past Seller Annual Check-in",
    "triggers": ["seller", "past_client"],
    "touchpoints": [
        {
            "name": "Home Anniversary",
            "event_type": "date_offset", 
            "offset_days": 365,
            "prompt": (
                "<role>You are a friendly and professional real estate agent's assistant.</role>\n"
                "<task>Draft a warm and celebratory 'Home Anniversary' message for {client_name}.</task>\n"
                "<instructions>Congratulate them on one year in their home. Ask them what their favorite part of living there has been. Sign it from {realtor_name}.</instructions>"
            )
        },
        {
            "name": "Annual Equity Update",
            "event_type": "date_offset",
            "offset_days": 372,
            "prompt": (
                "<role>You are a friendly and professional real estate agent's assistant.</role>\n"
                "<task>Draft a value-driven SMS to {client_name} offering a home equity update.</task>\n"
                "<instructions>Follow up on the recent home anniversary message. Offer to send them an updated analysis of their home's value, as the market has likely changed. Keep it professional and helpful. Sign it from {realtor_name}.</instructions>"
            )
        }
    ]
}

CUSTOM_FREQUENCY_PLAYBOOK = {
    "name": "Client Preferred Cadence",
    "triggers": [], # No explicit trigger tag
    "touchpoints": [
        {
            "id": "custom_check_in",
            "name": "Custom Frequency Check-in",
            "event_type": "recurring",
            "recurrence": {"parse_from_notes": True}, # Tells the planner to look for a frequency in the notes
            "prompt": (
                "<role>You are a friendly and professional real estate agent's assistant.</role>\n"
                "<task>Draft a brief and casual SMS check-in for {client_name}.</task>\n"
                "<instructions>Your goal is to be helpful and maintain the relationship. You can mention a local event or a general market insight. Client's notes for context: '{notes}'. Sign it from {realtor_name}.</instructions>"
            )
        }
    ]
}

# --- NEW: Playbook for sending holiday messages ---
HOLIDAY_GREETING_PLAYBOOK = {
    "name": "General Holiday Greetings",
    "triggers": ["sphere", "past_client", "lead"],
    "touchpoints": [
        {
            "id": "holiday_july_4th",
            "name": "4th of July Greeting",
            "event_type": "holiday",
            "holiday_name": "july_4th",
            "send_before_days": 4,
            "prompt": (
                "<role>You are a friendly local professional.</role>\n"
                "<task>Draft a brief, warm, and festive 4th of July greeting for {client_name}.</task>\n"
                "<instructions>Wish them a happy and safe holiday. Do not mention real estate. Sign it from {realtor_name}.</instructions>"
            )
        },
        {
            "id": "holiday_thanksgiving",
            "name": "Thanksgiving Greeting",
            "event_type": "holiday",
            "holiday_name": "thanksgiving",
            "send_before_days": 3,
            "prompt": (
                "<role>You are a friendly local professional.</role>\n"
                "<task>Draft a brief and sincere Thanksgiving message for {client_name}.</task>\n"
                "<instructions>Express gratitude and wish them a wonderful time with family and friends. Sign it from {realtor_name}.</instructions>"
            )
        },
        {
            "id": "holiday_christmas",
            "name": "Christmas Greeting",
            "event_type": "holiday",
            "holiday_name": "christmas",
            "send_before_days": 4,
            "prompt": (
                "<role>You are a friendly local professional.</role>\n"
                "<task>Draft a brief, warm, and festive Christmas or general holiday greeting for {client_name}.</task>\n"
                "<instructions>Wish them a happy holiday season. Sign it from {realtor_name}.</instructions>"
            )
        }
    ]
}



# A list of all available playbooks. They are matched in order.
# The order determines priority. Custom frequency is checked first.

ALL_PLAYBOOKS = [
    CUSTOM_FREQUENCY_PLAYBOOK,
    POTENTIAL_SELLER_PLAYBOOK,
    FIRST_TIME_BUYER_PLAYBOOK,
    INVESTOR_PLAYBOOK,
    NEW_BUYER_PLAYBOOK,
    PAST_SELLER_PLAYBOOK,
    HOLIDAY_GREETING_PLAYBOOK
]