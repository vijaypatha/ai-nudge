# FILE: agent_core/brain/verticals/therapy.py

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional

from data.models.event import MarketEvent
from data.models.resource import Resource
from data.models.client import Client

# --- Therapy Specific Intel Builders ---

def _build_recency_intel(event: MarketEvent, resource: Resource) -> Dict[str, Any]:
    days = event.payload.get("days_since_last_contact", "N/A")
    return {"Last Contact": f"{days} days ago", "Status": "Needs Follow-up"}

def _build_milestone_intel(event: MarketEvent, resource: Resource) -> Dict[str, Any]:
    return {"Milestone": f"{event.payload.get('milestone_name', 'Reached')}", "Client": resource.attributes.get('full_name', 'N/A')}

# --- Therapy Specific Scoring Function ---

def score_therapy_event(client: Client, event: MarketEvent, resource_embedding: Optional[List[float]], config: Dict) -> tuple[int, list[str]]:
    """Contains all scoring logic specific to therapy."""
    total_score = 0
    reasons = []
    weights = config["scoring_weights"]
    event_type = event.event_type

    if event_type == "no_recent_booking":
        recency_threshold = timedelta(days=weights.get("no_recent_booking_days", 90))
        last_contact = datetime.fromisoformat(client.last_interaction) if client.last_interaction else datetime.now(timezone.utc) - timedelta(days=999)
        if (datetime.now(timezone.utc) - last_contact) > recency_threshold:
            total_score = 100
            days_since = (datetime.now(timezone.utc) - last_contact).days
            reasons.append(f"Last contact was {days_since} days ago")
            event.payload["days_since_last_contact"] = days_since # Pass info to intel builder
    
    elif event_type == "session_milestone":
        if str(client.id) == str(event.entity_id): # Event is specifically for this client
            total_score = 100
            reasons.append(f"Client reached milestone: {event.payload.get('milestone_name')}")
            
    return int(total_score), reasons

# --- Therapy Vertical Configuration Object ---

THERAPY_CONFIG = {
    "scorer": score_therapy_event,
    "resource_type": "client_profile",
    "roles": {
        "default": {"event_types": ["no_recent_booking", "session_milestone"]},
    },
    "scoring_weights": {
        "no_recent_booking_days": 90
    },
    "campaign_configs": {
        "no_recent_booking": {"headline": "Follow-up Opportunity: {client_name}", "intel_builder": _build_recency_intel},
        "session_milestone": {"headline": "Celebrate a Milestone: {client_name}", "intel_builder": _build_milestone_intel},
    }
}