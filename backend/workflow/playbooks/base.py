# FILE: backend/workflow/playbooks/base.py
# --- NEW FILE ---
# This file contains the shared, agnostic data structures for all playbooks.

from typing import List, Literal

# --- Define conversational intent types ---
IntentType = Literal["LONG_TERM_NURTURE", "SHORT_TERM_LEAD"]

# --- A structured class for playbooks for better type safety and clarity ---
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