# File Path: backend/agent_core/brain/nudge_engine.py
# --- MODIFIED: Fixed crash by removing invalid argument and tuned similarity threshold.

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
from agent_core import llm_client

MATCH_THRESHOLD = 50

SCORE_WEIGHTS = {
    "semantic_match": 50,
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

def _calculate_cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    if not isinstance(vec1, list) or not isinstance(vec2, list) or not vec1 or not vec2: return 0.0
    v1 = np.array(vec1)
    v2 = np.array(vec2)
    if v1.shape != v2.shape or np.linalg.norm(v1) == 0 or np.linalg.norm(v2) == 0:
        return 0.0
    return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))

def _get_client_score_for_property(client: Client, resource_payload: Dict[str, Any], property_embedding: Optional[List[float]]) -> tuple[int, list[str]]:
    total_score = 0
    reasons = []
    
    logging.info(f"--- Scoring Client: {client.full_name} (ID: {client.id}) ---")

    # 1. Score by Semantic Match
    client_embedding = client.notes_embedding
    if client_embedding and property_embedding:
        similarity = _calculate_cosine_similarity(client_embedding, property_embedding)
        logging.info(f"  - Semantic Similarity: {similarity:.4f}")
        # --- MODIFIED: Lowered threshold to a more reasonable value for tuning. ---
        if similarity > 0.45:
            score_contribution = SCORE_WEIGHTS['semantic_match'] * similarity
            total_score += score_contribution
            reasons.append("🔥 Conceptual Match")
            logging.info(f"  - Semantic Match contribution: {score_contribution:.2f}")
    else:
        logging.info(f"  - Semantic Similarity: SKIPPED (Client Embedding: {'Exists' if client_embedding else 'None'}, Property Embedding: {'Exists' if property_embedding else 'None'})")

    # 2. Score by Price
    client_prefs = client.preferences or {}
    max_budget = client_prefs.get('budget_max')
    list_price = resource_payload.get('ListPrice')
    if list_price and max_budget:
        logging.info(f"  - Price Check: Budget=${max_budget}, Price=${list_price}")
        if list_price <= max_budget:
            total_score += SCORE_WEIGHTS['price']
            reasons.append("✅ Budget Match")
            logging.info(f"  - Price contribution: {SCORE_WEIGHTS['price']}")
    else:
        logging.info(f"  - Price Check: SKIPPED (Budget: {max_budget}, Price: {list_price})")

    # 3. Score by Location
    resource_location = resource_payload.get('SubdivisionName', '').lower()
    client_locations = client_prefs.get('locations', [])
    if resource_location and client_locations:
        logging.info(f"  - Location Check: Client wants {client_locations}, Property is in '{resource_location}'")
        if any(loc.lower() in resource_location for loc in client_locations):
            total_score += SCORE_WEIGHTS['location']
            reasons.append("✅ Location Match")
            logging.info(f"  - Location contribution: {SCORE_WEIGHTS['location']}")
    else:
        logging.info(f"  - Location Check: SKIPPED (Client Locations: {client_locations}, Resource Location: {resource_location})")

    # 4. Score by Features
    min_beds = client_prefs.get('min_bedrooms')
    resource_beds = resource_payload.get('BedroomsTotal')
    if min_beds and resource_beds:
        logging.info(f"  - Features Check: Client wants min {min_beds} beds, Property has {resource_beds}")
        if resource_beds >= min_beds:
            total_score += SCORE_WEIGHTS['features']
            reasons.append(f"✅ Features Match ({resource_beds} Beds)")
            logging.info(f"  - Features contribution: {SCORE_WEIGHTS['features']}")
    else:
        logging.info(f"  - Features Check: SKIPPED (Min Beds: {min_beds}, Resource Beds: {resource_beds})")

    # 5. Score by Keywords
    keywords = set([tag.lower() for tag in client.user_tags] + [tag.lower() for tag in client.ai_tags])
    notes_keywords = re.findall(r'\b\w+\b', (client.notes or '').lower())
    keywords.update(notes_keywords)
    property_remarks = resource_payload.get('PublicRemarks')
    found_keywords = {kw for kw in keywords if kw in (property_remarks or '').lower() and len(kw) > 2}
    if found_keywords:
        total_score += SCORE_WEIGHTS['keywords']
        reasons.append(f"✅ Keyword Match ({', '.join(list(found_keywords)[:2])})")
        logging.info(f"  - Keyword contribution: {SCORE_WEIGHTS['keywords']}")

    logging.info(f"  - FINAL SCORE for {client.full_name}: {int(total_score)}")
    
    return int(total_score), reasons

async def _create_campaign_from_event(event: MarketEvent, realtor: User, resource: Resource, matched_audience: list[MatchedClient], db_session: Session):
    config = CAMPAIGN_CONFIG.get(event.event_type)
    if not config: return
    address = event.payload.get('UnparsedAddress', resource.attributes.get('address', 'N/A'))
    headline = config["headline"].format(address=address)
    key_intel = config["intel_builder"](event, resource)
    
    # --- MODIFIED: Removed the invalid 'resource_payload' argument to prevent crash. ---
    ai_draft = await conversation_agent.draft_outbound_campaign_message(
        realtor=realtor, 
        resource=resource, 
        event_type=event.event_type, 
        matched_audience=matched_audience
    )
    
    audience_for_db = [m.model_dump(mode='json') for m in matched_audience]
    
    briefing_id = uuid.uuid4()
    new_briefing = CampaignBriefing(
        id=briefing_id, 
        user_id=realtor.id, 
        campaign_type=event.event_type, 
        status=CampaignStatus.DRAFT,
        headline=headline, 
        key_intel=key_intel, 
        listing_url=next((media['MediaURL'] for media in event.payload.get('Media', []) if media.get('Order') == 0), None),
        original_draft=ai_draft, 
        matched_audience=audience_for_db,
        triggering_event_id=uuid.uuid5(uuid.NAMESPACE_DNS, f"{event.payload.get('ListingKey', str(uuid.uuid4()))}-{event.event_type}")
    )
    
    crm_service.save_campaign_briefing(new_briefing, session=db_session)
    logging.info(f"NUDGE ENGINE: Successfully created Campaign Briefing {briefing_id} for event {event.event_type}")

async def process_market_event(event: MarketEvent, realtor: User, db_session: Optional[Session] = None):
    logging.info(f"NUDGE ENGINE: Processing event -> {event.event_type} for entity {event.entity_id}")
    resource_payload = event.payload
    if not resource_payload:
        logging.warning("NUDGE ENGINE: Event payload is empty. Cannot process.")
        return

    property_remarks = resource_payload.get('PublicRemarks')
    property_embedding = await llm_client.generate_embedding(property_remarks) if property_remarks else None

    resource = Resource(id=event.entity_id, user_id=realtor.id, resource_type="property", status="active", attributes={"address": resource_payload.get("UnparsedAddress", "N/A")})
    all_clients = crm_service.get_all_clients(user_id=realtor.id)
    matched_audience = []

    for client in all_clients:
        score, reasons = _get_client_score_for_property(client, resource_payload, property_embedding)
        
        if score >= MATCH_THRESHOLD:
            matched_audience.append(MatchedClient(
                client_id=client.id, 
                client_name=client.full_name, 
                match_score=score, 
                match_reasons=reasons
            ))
    
    if not matched_audience:
        logging.info(f"NUDGE ENGINE: No clients scored >= {MATCH_THRESHOLD} for event on resource {resource.id}.")
        return

    matched_audience.sort(key=lambda m: m.match_score, reverse=True)
    logging.info(f"NUDGE ENGINE: Found {len(matched_audience)} potential clients. Top match score: {matched_audience[0].match_score}")

    session_to_use = db_session if db_session else Session(crm_service.engine)
    try:
        await _create_campaign_from_event(event, realtor, resource, matched_audience, db_session=session_to_use)
        if not db_session:
            session_to_use.commit()
    except Exception as e:
        logging.error(f"NUDGE ENGINE: Error creating campaign from event: {e}", exc_info=True)
        if not db_session:
            session_to_use.rollback()
    finally:
        if not db_session:
            session_to_use.close()

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
            listings = await asyncio.to_thread(fetcher_func, minutes_ago=minutes_ago)
            if listings:
                for listing_data in listings:
                    resource_id_for_demo = uuid.uuid5(uuid.NAMESPACE_DNS, listing_data.get('ListingKey', str(uuid.uuid4())))
                    event = MarketEvent(event_type=event_type, entity_id=resource_id_for_demo, payload=listing_data, entity_type="property", market_area="default")
                    await process_market_event(event, realtor)
        except Exception as e:
            logging.error(f"NUDGE ENGINE: Error processing {event_type}: {e}", exc_info=True)