# ---
# File Path: backend/workflow/relationship_playbooks.py
# Purpose: Stores pre-defined relationship campaign templates, or "playbooks."
# ---

GENERIC_BUYER_PLAYBOOK = {
    "name": "Generic Buyer Nurture",
    "triggers": ["buyer"], # This playbook is triggered if a client has the "buyer" tag.
    "touchpoints": [
        {
            "name": "Birthday Greeting",
            "event_type": "birthday",
            "prompt": "Draft a warm, personal, and brief birthday SMS for {client_name}. You know they have these interests: {notes}. Sign it from {realtor_name}."
        },
        {
        "name": "Quarterly Check-in",
        "event_type": "quarterly_check_in",
        "offset_days": 90,
        "prompt": "Draft a brief and casual SMS check-in for {client_name}. Offer a helpful real estate wealth-building tip. The message must be in SMS format and must not have a subject line. Sign it from {realtor_name}."
        }
    ]
}

# A list of all available playbooks for the planner to use.
ALL_PLAYBOOKS = [GENERIC_BUYER_PLAYBOOK]