# FILE: backend/workflow/relationship_playbooks.py
# --- REFACTORED V3 (REGISTRY ONLY) ---
# This file is now a clean, vertically-aware registry that imports playbook
# definitions from specialized modules.

import logging
from typing import Dict, Optional

# --- Import base structures and vertical-specific playbooks ---
from .playbooks.base import ConversationalPlaybook, IntentType
from .playbooks import real_estate as re_playbooks
from .playbooks import therapy as therapy_playbooks

# --- Master Registry for ALL Vertical Playbooks ---
# This registry maps a vertical name to its set of conversational playbooks.
VERTICAL_PLAYBOOK_REGISTRY: Dict[str, Dict[IntentType, ConversationalPlaybook]] = {
    "real_estate": {
        "LONG_TERM_NURTURE": re_playbooks.REALTOR_LONG_TERM_NURTURE,
        "SHORT_TERM_LEAD": re_playbooks.REALTOR_SHORT_TERM_LEAD,
    },
    "therapy": {
        "LONG_TERM_NURTURE": therapy_playbooks.THERAPIST_LONG_TERM_NURTURE,
        "SHORT_TERM_LEAD": therapy_playbooks.THERAPIST_SHORT_TERM_LEAD,
    }
}

# --- Master Registry for legacy, time-based playbooks ---
# This is used by the older relationship_planner cron job.
VERTICAL_LEGACY_PLAYBOOKS_REGISTRY = {
    "real_estate": re_playbooks.ALL_LEGACY_PLAYBOOKS,
    "therapy": therapy_playbooks.ALL_LEGACY_PLAYBOOKS,
    # Add other verticals here
}


def get_playbook_for_intent(intent: IntentType, vertical: str) -> Optional[ConversationalPlaybook]:
    """
    Selects the appropriate conversational playbook based on the AI's analysis
    AND the user's vertical.
    """
    logging.info(f"PLAYBOOKS: Retrieving playbook for intent '{intent}' in vertical '{vertical}'")
    vertical_playbooks = VERTICAL_PLAYBOOK_REGISTRY.get(vertical)
    if not vertical_playbooks:
        logging.warning(f"No conversational playbooks found for vertical: {vertical}")
        return None
    
    playbook = vertical_playbooks.get(intent)
    if not playbook:
        logging.warning(f"No playbook found for intent '{intent}' in vertical '{vertical}'")
    
    return playbook