# FILE: backend/agent_core/brain/verticals/therapy.py
#
# PURPOSE:
# This file defines the specific AI logic and configuration for the 'Therapy' vertical.
# It tells the central Nudge Engine how to score events, what kind of campaigns to create,
# and how to display information in the UI, tailored specifically to a therapist's workflow.
#
# STRATEGIC DECISION:
# This implementation focuses entirely on the "Content Suggestion" feature. It replaces
# previous placeholder logic that required a non-existent calendar integration. This new
# approach delivers immediate user value by leveraging the Google Search API and the app's
# existing client tagging system, creating a powerful, proactive, and vertical-agnostic
# content discovery pipeline that can be extended to other verticals in the future.

import logging
from typing import Dict, Any, List, Optional

from data.models.event import MarketEvent
from data.models.resource import Resource
from data.models.client import Client

def _build_content_intel(event: MarketEvent, resource: Resource) -> Dict[str, Any]:
    """
    (Act Layer)
    Builds the structured "Key Intel" object for the frontend card.
    This function takes the raw event and resource data and transforms it into a clean,
    human-readable format for the therapist to see in the Action Deck.
    """
    return {
        "Content Title": resource.attributes.get('title', 'N/A'),
        "Source": resource.attributes.get('source_name', 'N/A'),
        "Topic": event.payload.get('topic', 'General'),
        "URL": resource.attributes.get('url', 'N/A')
    }

def score_therapy_event(client: Client, event: MarketEvent, resource_embedding: Optional[List[float]], config: Dict) -> tuple[int, list[str]]:
    """
    (Reason Layer)
    This is the core scoring logic for the therapy vertical. It determines if a specific
    client is a good match for a given event.

    For a 'content_suggestion' event, it performs a simple but powerful match:
    Does the topic of the content (e.g., "anxiety") match any of the tags
    associated with the client? These tags can be manually set by the therapist
    or automatically extracted by the AI from conversations, making the match highly relevant.
    This approach is HIPAA-safe as it does not analyze sensitive clinical notes.
    """
    # This scorer only cares about 'content_suggestion' events.
    if event.event_type != "content_suggestion":
        logging.info(f"THERAPY_SCORER: Skipping event {event.id} - not 'content_suggestion'.")
        return 0, []

    content_topic = event.payload.get("topic", "").lower()
    if not content_topic:
        logging.warning(f"THERAPY_SCORER: Content topic missing for event {event.id}. Skipping.")
        return 0, []

    # Combine user-set tags and AI-extracted intel for a comprehensive match.
    client_tags = [tag.lower() for tag in (client.user_tags or []) + (client.ai_tags or [])]
    logging.info(f"THERAPY_SCORER: Client {client.id} ({client.full_name}) tags: {client_tags}")
    logging.info(f"THERAPY_SCORER: Content topic: {content_topic}")
    
    # If a direct match is found, assign a perfect score.
    if content_topic in client_tags:
        # The reason is sent to the frontend to show the therapist *why* the match was made.
        score = 100
        reasons = [f"✅ Topic Match: {content_topic.capitalize()}"]
        logging.info(f"THERAPY_SCORER: Match found for client {client.id} on topic '{content_topic}'. Score: {score}")
        return score, reasons
            
    # If no match, return a zero score so no nudge is created.
    logging.info(f"THERAPY_SCORER: No match found for client {client.id} on topic '{content_topic}'. Score: 0")
    return 0, []

# --- VERTICAL CONFIGURATION OBJECT ---
# This dictionary is the central "plug-in" for the therapy vertical.
# The Nudge Engine reads this config to understand how to behave for any therapist user.
THERAPY_CONFIG = {
    # Specifies the function to use for scoring events.
    "scorer": score_therapy_event,

    # Defines the primary resource type for this vertical's main events.
    # For content suggestions, the resource is the article/video itself.
    "resource_type": "web_content",

    # Defines which event types this vertical's configuration should handle.
    "roles": {
        "default": {"event_types": ["content_suggestion"]},
    },

    # Scoring weights are not needed for this simple, direct-match logic.
    "scoring_weights": {},

    # Defines the templates for campaigns triggered by different events.
    "campaign_configs": {
        "content_suggestion": {
            # Headline for the nudge card (client_name is a dynamic placeholder).
            "headline": "Content Suggestion for {client_name}",
            
            # Function to build the structured intel display.
            "intel_builder": _build_content_intel,
            
            # UI hints for the frontend to render the nudge card correctly.
            "display": {
                "title": "Content Suggestion", 
                "icon": "BookOpen", # Must match a key in the frontend ICONS map
                "color": "text-sky-400"  # Tailwind CSS color class
            },
            "call_to_action": "Share Article" # A clear call to action for the frontend
        },
    }
}