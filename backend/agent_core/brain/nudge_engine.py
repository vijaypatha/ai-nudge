# File Path: backend/agent_core/brain/nudge_engine.py
# --- MODIFIED: Integrated Semantic Matching into the scoring logic.

import uuid
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
import re
import numpy as np

from sqlmodel import Session
from data.models.event import MarketEvent
from data.models.campaign import CampaignBriefing, MatchedClient, CampaignStatus
from data.models.user import User
from data.models.client import Client
from data.models.resource import Resource
from data import crm as crm_service
from integrations.mls.factory import get_mls_client
from agent_core.agents import conversation as conversation_agent
from agent_core import llm_client # Import our LLM client

# --- Configuration for the Match Score system ---
MATCH_THRESHOLD = 50

# --- MODIFIED: Re-balanced weights to include semantic matching ---
SCORE_WEIGHTS = {
    "semantic_match": 50, # High weight for conceptual matches
    "price": 30,
    "location": 25,
    "keywords": 20,
    "features": 15,
}

# --- Key Intel Builder Functions (Unchanged) ---
def _build_price_drop_intel(event: MarketEvent, resource: Resource) -> Dict[str, Any]:
    old_price = event.payload.get('OriginalListPrice', 0)
    new_price = event.payload.get('ListPrice', 0)
    price_change = old_price - new_price
    return {"Price Drop": f"${price_change:,.0f}", "New Price": f"${new_price:,.0f}"}
# ... (other intel builders remain the same) ...

def _build_sold_intel(event: MarketEvent, resource: Resource) -> Dict[str, Any]:
    return {"Sold Price": f"${event.payload.get('ClosePrice', 0):,.0f}", "Address": resource.attributes.get('address', 'N/A')}

def _build_simple_intel(event: MarketEvent, resource: Resource) -> Dict[str, Any]:
    return {"Asking Price": f"${event.payload.get('ListPrice', 0):,.0f}", "Address": resource.attributes.get('address', 'N/A')}

def _build_expired_intel(event: MarketEvent, resource: Resource) -> Dict[str, Any]:
    return {"Last Price": f"${event.payload.get('ListPrice', 0):,.0f}", "Status": "Expired"}

def _build_coming_soon_intel(event: MarketEvent, resource: Resource) -> Dict[str, Any]:
    return {"Anticipated Price": f"${event.payload.get('ListPrice', 0):,.0f}", "Status": "Coming Soon"}

def _build_withdrawn_intel(event: MarketEvent, resource: Resource) -> Dict[str, Any]:
    return {"Last Price": f"${event.payload.get('ListPrice', 0):,.0f}", "Status": "Withdrawn"}

CAMPAIGN_CONFIG = {
    "price_drop": {"headline": "Price Drop: {address}", "intel_builder": _build_price_drop_intel},
    "new_listing": {"headline": "New Listing: {address}", "intel_builder": _build_simple_intel},
    "sold_listing": {"headline": "Just Sold Nearby: {address}", "intel_builder": _build_sold_intel},
    "back_on_market": {"headline": "Back on Market: {address}", "intel_builder": _build_simple_intel},
    "expired_listing": {"headline": "Expired Listing Opportunity: {address}", "intel_builder": _build_expired_intel},
    "coming_soon": {"headline": "Coming Soon: {address}", "intel_builder": _build_coming_soon_intel},
    "withdrawn_listing": {"headline": "Withdrawn Listing: {address}", "intel_builder": _build_withdrawn_intel},
}

# --- NEW: Helper function for semantic similarity ---
def _calculate_cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calculates the cosine similarity between two vectors."""
    if not isinstance(vec1, list) or not isinstance(vec2, list): return 0.0
    v1 = np.array(vec1)
    v2 = np.array(vec2)
    if v1.shape != v2.shape or np.linalg.norm(v1) == 0 or np.linalg.norm(v2) == 0:
        return 0.0
    return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))


# --- REWRITTEN & ENHANCED: The new, sophisticated match score engine ---
async def _calculate_match_score(client: Client, resource: Resource, resource_payload: Dict[str, Any]) -> tuple[int, list[str]]:
    """
    Calculates a weighted match score based on multiple criteria, now including semantic search.
    """
    total_score = 0
    reasons = []

    # 1. Score by Semantic Match (The "soft" data)
    client_embedding = client.notes_embedding
    property_remarks = resource_payload.get('PublicRemarks')
    if client_embedding and property_remarks:
        property_embedding = await llm_client.generate_embedding(property_remarks)
        similarity = _calculate_cosine_similarity(client_embedding, property_embedding)
        if similarity > 0.75: # High threshold for conceptual match
            total_score += SCORE_WEIGHTS['semantic_match'] * similarity
            reasons.append("🔥 Conceptual Match")

    # 2. Score by Price
    client_prefs = client.preferences or {}
    max_budget = client_prefs.get('max_budget')
    list_price = resource_payload.get('ListPrice')
    if list_price and max_budget and list_price <= max_budget:
        total_score += SCORE_WEIGHTS['price']
        reasons.append("✅ Budget Match")

    # 3. Score by Location
    resource_location = resource_payload.get('SubdivisionName', '').lower()
    client_locations = client_prefs.get('locations', [])
    if resource_location and any(loc.lower() in resource_location for loc in client_locations):
        total_score += SCORE_WEIGHTS['location']
        reasons.append("✅ Location Match")

    # 4. Score by Features
    min_beds = client_prefs.get('min_bedrooms')
    resource_beds = resource_payload.get('BedroomsTotal')
    if min_beds and resource_beds and resource_beds >= min_beds:
        total_score += SCORE_WEIGHTS['features']
        reasons.append(f"✅ Features Match ({resource_beds} Beds)")

    # 5. Score by Keywords (The "hard" data from notes/tags)
    keywords = set([tag.lower() for tag in client.user_tags] + [tag.lower() for tag in client.ai_tags])
    notes_keywords = re.findall(r'\b\w+\b', (client.notes or '').lower())
    keywords.update(notes_keywords)
    found_keywords = {kw for kw in keywords if kw in (property_remarks or '').lower() and len(kw) > 2}
    if found_keywords:
        total_score += SCORE_WEIGHTS['keywords']
        reasons.append(f"✅ Keyword Match ({', '.join(list(found_keywords)[:2])})")

    return int(total_score), reasons


async def _create_campaign_from_event(event: MarketEvent, realtor: User, resource: Resource, matched_audience: list[MatchedClient], db_session: Session):
    config = CAMPAIGN_CONFIG.get(event.event_type)
    if not config: return
    # ... (rest of function is unchanged)
    address = event.payload.get('UnparsedAddress', resource.attributes.get('address', 'N/A'))
    headline = config["headline"].format(address=address)
    key_intel = config["intel_builder"](event, resource)
    
    ai_draft = await conversation_agent.draft_outbound_campaign_message(realtor=realtor, resource=resource, event_type=event.event_type, matched_audience=matched_audience, resource_payload=event.payload)
    
    audience_for_db = [m.model_dump(mode='json') for m in matched_audience]
    
    new_briefing = CampaignBriefing(
        id=uuid.uuid4(), 
        user_id=realtor.id, 
        campaign_type=event.event_type, 
        status=CampaignStatus.DRAFT,
        headline=headline, 
        key_intel=key_intel, 
        listing_url=next((media['MediaURL'] for media in event.payload.get('Media', []) if media.get('Order') == 0), None),
        original_draft=ai_draft, 
        matched_audience=audience_for_db,
        triggering_event_id=uuid.uuid5(uuid.NAMESPACE_DNS, event.payload.get('ListingKey', str(uuid.uuid4())))
    )
    
    crm_service.save_campaign_briefing(new_briefing)


# --- UPDATED: Now awaits the async _calculate_match_score ---
async def process_market_event(event: MarketEvent, realtor: User, db_session: Optional[Session] = None):
    """
    Processes a single market event, finds a matching audience using the new scoring
    system, and creates a campaign briefing if the match is strong enough.
    """
    logging.info(f"NUDGE ENGINE: Processing event -> {event.event_type} for entity {event.entity_id}")
    
    resource_payload = event.payload
    if not resource_payload:
        logging.warning("NUDGE ENGINE: Event payload is empty. Cannot process.")
        return

    resource = Resource(id=event.entity_id, user_id=realtor.id, resource_type="property", status="active", attributes={"address": resource_payload.get("UnparsedAddress", "N/A")})

    all_clients = crm_service.get_all_clients(user_id=realtor.id)
    matched_audience = []
    for client in all_clients:
        # Now awaiting the async scoring function
        score, reasons = await _calculate_match_score(client, resource, resource_payload)
        
        if score >= MATCH_THRESHOLD:
            matched_audience.append(MatchedClient(
                client_id=client.id, 
                client_name=client.full_name, 
                match_score=score, 
                match_reasons=reasons
            ))
    
    if not matched_audience:
        logging.info(f"NUDGE ENGINE: No matching audience found for event on resource {resource.id}.")
        return

    matched_audience.sort(key=lambda m: m.match_score, reverse=True)

    session_to_use = db_session if db_session else Session(crm_service.engine)
    try:
        await _create_campaign_from_event(event, realtor, resource, matched_audience, db_session=session_to_use)
    finally:
        if not db_session:
            session_to_use.close()

# ... (rest of file, e.g., generate_recency_nudges and scan_for_all_market_events, remains the same) ...
async def generate_recency_nudges(realtor: User):
    logging.info("NUDGE ENGINE: Checking for clients needing a follow-up...")
    RECENCY_THRESHOLD_DAYS = 90
    all_clients = crm_service.get_all_clients(user_id=realtor.id)
    
    at_risk_clients = [
        client for client in all_clients
        if not client.last_interaction or (datetime.now(timezone.utc) - datetime.fromisoformat(client.last_interaction)) > timedelta(days=RECENCY_THRESHOLD_DAYS)
    ]
    
    if not at_risk_clients:
        logging.info("NUDGE ENGINE: No at-risk clients found for recency nudge.")
        return
        
    logging.info(f"NUDGE ENGINE: Found {len(at_risk_clients)} at-risk clients. Generating nudge...")
    # NOTE: The MatchedClient model for recency nudges is simpler as reasons are uniform.
    matched_audience = [MatchedClient(client_id=c.id, client_name=c.full_name, match_score=100, match_reasons=[f"Last contacted on {c.last_interaction or 'never'}"]) for c in at_risk_clients]
    
    ai_draft = await conversation_agent.draft_outbound_campaign_message(realtor=realtor, event_type="recency_nudge", matched_audience=matched_audience)
    
    recency_briefing = CampaignBriefing(
        id=uuid.uuid4(),
        user_id=realtor.id,
        campaign_type="recency_nudge",
        status=CampaignStatus.DRAFT,
        headline=f"Relationship Opportunity: {len(at_risk_clients)} clients need a follow-up",
        key_intel={"At-Risk Clients": len(at_risk_clients), "Threshold": f"{RECENCY_THRESHOLD_DAYS} days"},
        original_draft=ai_draft,
        matched_audience=[m.model_dump(mode='json') for m in matched_audience],
        triggering_event_id=uuid.uuid4()
    )
    
    crm_service.save_campaign_briefing(recency_briefing)

async def scan_for_all_market_events(realtor: User, minutes_ago: int = 60):
    mls_client = get_mls_client()
    if not mls_client:
        logging.warning("NUDGE ENGINE: Could not initialize MLS client. Aborting scan.")
        return

    fetcher_map = {
        "new_listing": mls_client.fetch_new_listings,
        "price_drop": mls_client.fetch_price_changes,
        "sold_listing": mls_client.fetch_sold_listings,
        "back_on_market": mls_client.fetch_back_on_market_listings,
        "expired_listing": mls_client.fetch_expired_listings,
        "coming_soon": mls_client.fetch_coming_soon_listings,
        "withdrawn_listing": mls_client.fetch_withdrawn_listings,
    }

    for event_type, fetcher_func in fetcher_map.items():
        logging.info(f"NUDGE ENGINE: Scanning for '{event_type}' events...")
        try:
            listings = fetcher_func(minutes_ago=minutes_ago)
            if listings:
                for listing_data in listings:
                    resource_id_for_demo = uuid.uuid5(uuid.NAMESPACE_DNS, listing_data.get('ListingKey', str(uuid.uuid4())))
                    event = MarketEvent(event_type=event_type, entity_id=resource_id_for_demo, payload=listing_data, entity_type="property", market_area="default")
                    await process_market_event(event, realtor)
        except Exception as e:
            logging.error(f"NUDGE ENGINE: Error processing {event_type}: {e}", exc_info=True)