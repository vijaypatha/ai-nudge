# FILE: backend/workflow/playbooks/therapy.py
# --- NEW FILE ---
# Contains all conversational and time-based playbooks for the Therapy vertical.

from .base import ConversationalPlaybook, PlaybookStep, IntentType

# --- Modern, Class-Based Conversational Playbooks ---

THERAPIST_LONG_TERM_NURTURE = ConversationalPlaybook(
    name="Long-Term Client Care (Therapy)",
    intent_type="LONG_TERM_NURTURE",
    steps=[
        PlaybookStep(delay_days=60, name="Gentle Check-in", prompt="Draft a gentle and supportive check-in message for a therapy client. Ask how they have been doing. The message MUST be about personal well-being. CRITICAL: DO NOT mention real estate, property, or home buying."),
    ]
)
THERAPIST_SHORT_TERM_LEAD = ConversationalPlaybook(
    name="New Client Engagement (Therapy)",
    intent_type="SHORT_TERM_LEAD",
    steps=[
        PlaybookStep(delay_days=5, name="Follow-up on In-Progress Topic", prompt="Draft a thoughtful follow-up message for a therapy client about their last session. Offer a link to a relevant mental well-being article or a simple question for reflection. CRITICAL: The topic MUST be therapy. DO NOT mention real estate or investments."),
    ]
)

# --- Legacy, Dictionary-Based Playbooks (if any are needed in the future) ---
CUSTOM_FREQUENCY_PLAYBOOK = {
    "name": "Client Preferred Cadence (Therapy)",
    "triggers": [],
    "touchpoints": [{
        "id": "custom_check_in_therapy",
        "name": "Custom Frequency Check-in",
        "event_type": "recurring",
        "recurrence": {"parse_from_notes": True},
        "prompt": "<role>You are a caring and professional therapist's assistant.</role>\n<task>Draft a brief and gentle SMS check-in for {client_name}.</task>\n<instructions>Your goal is to maintain a supportive connection. You can mention a resource for well-being or a general supportive thought. Client's notes for context: '{notes}'. Sign it from {user_full_name}.</instructions>"
    }]
}

PERSONAL_EVENT_PLAYBOOK = {
    "name": "Personal Event Reminder (Therapy)",
    "triggers": [],
    "touchpoints": [{
        "id": "personal_event_greeting_therapy",
        "name": "Personal Event Greeting",
        "event_type": "personal_event",
        # --- NEW KEY: Specifies which events this touchpoint can handle ---
        "handled_events": ["birthday", "bday", "anniversary", "christmas", "new year's", "thanksgiving"],
        "prompt": "<role>You are a thoughtful personal assistant.</role>\n<task>Draft a warm, celebratory SMS message to {client_name} for their {event_name}, which is today.</task>\n<instructions>Keep the message personal and supportive, relevant to their {event_name}. The client's notes are '{notes}'. Use this for context. CRITICAL: Do not give therapeutic advice. Sign it from {user_full_name}.</instructions>"
    }]
}

ALL_LEGACY_PLAYBOOKS = [
    CUSTOM_FREQUENCY_PLAYBOOK,
    PERSONAL_EVENT_PLAYBOOK
]