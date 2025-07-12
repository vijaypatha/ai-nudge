# File Path: backend/agent_core/brain/nudge_engine.py
# --- MODIFIED: Refactored to be vertical-agnostic, operating on generic Resources instead of Properties.

import uuid
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Callable, List, Optional

from sqlmodel import Session
from data.models.event import MarketEvent
# --- MODIFIED: Imported CampaignStatus to align with the new data model ---
from data.models.campaign import CampaignBriefing, MatchedClient, CampaignStatus
from data.models.user import User
from data.models.client import Client
from data.models.resource import Resource
from data import crm as crm_service
from integrations.mls.factory import get_mls_client
from agent_core.agents import conversation as conversation_agent

# --- Key Intel Builder Functions (Unchanged) ---
def _build_price_drop_intel(event: MarketEvent, resource: Resource) -> Dict[str, Any]:
    price_change = event.payload.get('old_price', 0) - event.payload.get('new_price', 0)
    return {"Price Drop": f"${price_change:,.0f}", "New Price": f"${event.payload.get('new_price', 0):,.0f}"}

def _build_sold_intel(event: MarketEvent, resource: Resource) -> Dict[str, Any]:
    return {"Sold Price": f"${resource.attributes.get('price', 0):,.0f}", "Address": resource.attributes.get('address', 'N/A')}

def _build_simple_intel(event: MarketEvent, resource: Resource) -> Dict[str, Any]:
    return {"Asking Price": f"${resource.attributes.get('price', 0):,.0f}", "Address": resource.attributes.get('address', 'N/A')}

def _build_expired_intel(event: MarketEvent, resource: Resource) -> Dict[str, Any]:
    return {"Last Price": f"${resource.attributes.get('price', 0):,.0f}", "Status": "Expired"}

def _build_coming_soon_intel(event: MarketEvent, resource: Resource) -> Dict[str, Any]:
    return {"Anticipated Price": f"${resource.attributes.get('price', 0):,.0f}", "Status": "Coming Soon"}

def _build_withdrawn_intel(event: MarketEvent, resource: Resource) -> Dict[str, Any]:
    return {"Last Price": f"${resource.attributes.get('price', 0):,.0f}", "Status": "Withdrawn"}

CAMPAIGN_CONFIG = {
    "price_drop": {"headline": "Price Drop: {address}", "intel_builder": _build_price_drop_intel},
    "new_listing": {"headline": "New Listing: {address}", "intel_builder": _build_simple_intel},
    "sold_listing": {"headline": "Just Sold Nearby: {address}", "intel_builder": _build_sold_intel},
    "back_on_market": {"headline": "Back on Market: {address}", "intel_builder": _build_simple_intel},
    "expired_listing": {"headline": "Expired Listing Opportunity: {address}", "intel_builder": _build_expired_intel},
    "coming_soon": {"headline": "Coming Soon: {address}", "intel_builder": _build_coming_soon_intel},
    "withdrawn_listing": {"headline": "Withdrawn Listing: {address}", "intel_builder": _build_withdrawn_intel},
}

def _calculate_match_score(client: Client, resource: Resource) -> tuple[int, list[str]]:
    score = 0
    reasons = []
    resource_address = resource.attributes.get('address', '').lower()
    if client.preferences and resource_address and any(loc.lower() in resource_address for loc in client.preferences.get("locations", [])):
        score += 100
        reasons.append("Location Match")
    return score, reasons

async def _create_campaign_from_event(event: MarketEvent, realtor: User, resource: Resource, matched_audience: list[MatchedClient], db_session: Session):
    config = CAMPAIGN_CONFIG.get(event.event_type)
    if not config: return
    
    headline = config["headline"].format(address=resource.attributes.get('address', 'N/A'))
    key_intel = config["intel_builder"](event, resource)
    
    ai_draft = await conversation_agent.draft_outbound_campaign_message(realtor=realtor, resource=resource, event_type=event.event_type, matched_audience=matched_audience)
    
    audience_for_db = [m.model_dump(mode='json') for m in matched_audience]
    
    new_briefing = CampaignBriefing(
        id=uuid.uuid4(), 
        user_id=realtor.id, 
        campaign_type=event.event_type, 
        # --- FIX: The status is now correctly set to CampaignStatus.DRAFT ---
        status=CampaignStatus.DRAFT,
        headline=headline, 
        key_intel=key_intel, 
        listing_url=resource.attributes.get('listing_url'),
        original_draft=ai_draft, 
        matched_audience=audience_for_db,
        triggering_event_id=event.id if event.id else uuid.uuid4()
    )
    
    crm_service.save_campaign_briefing(new_briefing)

async def process_market_event(event: MarketEvent, realtor: User, db_session: Optional[Session] = None):
    logging.info(f"NUDGE ENGINE: Processing event -> {event.event_type} for entity {event.entity_id}")
    
    def _process(session: Session):
        resource = crm_service.get_resource_by_id(resource_id=event.entity_id, user_id=realtor.id)
        if not resource:
            logging.warning(f"NUDGE ENGINE: Resource {event.entity_id} not found.")
            return None

        all_clients = crm_service.get_all_clients(user_id=realtor.id)
        matched_audience = []
        for client in all_clients:
            score, reasons = _calculate_match_score(client, resource)
            if score >= 100:
                matched_audience.append(MatchedClient(client_id=client.id, client_name=client.full_name, match_score=score, match_reason=", ".join(reasons)))
        
        if not matched_audience:
            logging.info(f"NUDGE ENGINE: No matching audience found for event {event.id}.")
            return None
            
        return resource, matched_audience

    if db_session:
        result = _process(db_session)
    else:
        with Session(crm_service.engine) as session:
            result = _process(session)
            
    if result:
        resource, matched_audience = result
        session_to_use = db_session if db_session else Session(crm_service.engine)
        await _create_campaign_from_event(event, realtor, resource, matched_audience, db_session=session_to_use)

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
    matched_audience = [MatchedClient(client_id=c.id, client_name=c.full_name, match_score=100, match_reason=f"Last contacted on {c.last_interaction or 'never'}") for c in at_risk_clients]
    
    ai_draft = await conversation_agent.draft_outbound_campaign_message(realtor=realtor, event_type="recency_nudge", matched_audience=matched_audience)
    
    recency_briefing = CampaignBriefing(
        id=uuid.uuid4(),
        user_id=realtor.id,
        campaign_type="recency_nudge",
        # --- FIX: The status is now correctly set to CampaignStatus.DRAFT ---
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
            all_resources = crm_service.get_all_resources_for_user(user_id=realtor.id)
            if not all_resources:
                logging.debug("NUDGE ENGINE: No resources in DB to associate events with.")
                continue

            property_resources = [r for r in all_resources if r.resource_type == 'property']
            if not property_resources:
                logging.debug("NUDGE ENGINE: No 'property' type resources found for this MLS scan.")
                continue

            resource_id_for_demo = property_resources[0].id
            listings = fetcher_func(minutes_ago=minutes_ago)
            if listings:
                for listing_data in listings:
                    event = MarketEvent(event_type=event_type, entity_id=resource_id_for_demo, payload=listing_data, market_area="default")
                    await process_market_event(event, realtor)
        except Exception as e:
            logging.error(f"NUDGE ENGINE: Error processing {event_type}: {e}", exc_info=True)