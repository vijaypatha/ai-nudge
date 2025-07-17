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
ALL_LEGACY_PLAYBOOKS = []