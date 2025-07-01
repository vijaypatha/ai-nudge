# ---
# File Path: backend/agent_core/brain/nudge_engine.py
# --- CORRECTED: Restored the generate_recency_nudges function ---

import uuid
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Callable, List

from data.models.event import MarketEvent
from data.models.campaign import CampaignBriefing, MatchedClient
from data.models.user import User
from data.models.client import Client
from data.models.property import Property
from data import crm as crm_service
from integrations.mls.factory import get_mls_client
from agent_core.agents import conversation as conversation_agent

# --- Key Intel Builder Functions ---
def _build_price_drop_intel(event: MarketEvent, property_item: Property) -> Dict[str, Any]:
    price_change = event.payload.get('old_price', 0) - event.payload.get('new_price', 0)
    return {"Price Drop": f"${price_change:,.0f}", "New Price": f"${event.payload.get('new_price', 0):,.0f}"}

def _build_sold_intel(event: MarketEvent, property_item: Property) -> Dict[str, Any]:
    return {"Sold Price": f"${property_item.price:,.0f}", "Address": property_item.address}

def _build_simple_intel(event: MarketEvent, property_item: Property) -> Dict[str, Any]:
    return {"Asking Price": f"${property_item.price:,.0f}", "Address": property_item.address}

def _build_expired_intel(event: MarketEvent, property_item: Property) -> Dict[str, Any]:
    return {"Last Price": f"${property_item.price:,.0f}", "Status": "Expired"}

def _build_coming_soon_intel(event: MarketEvent, property_item: Property) -> Dict[str, Any]:
    return {"Anticipated Price": f"${property_item.price:,.0f}", "Status": "Coming Soon"}

def _build_withdrawn_intel(event: MarketEvent, property_item: Property) -> Dict[str, Any]:
    return {"Last Price": f"${property_item.price:,.0f}", "Status": "Withdrawn"}


CAMPAIGN_CONFIG = {
    "price_drop": {"headline": "Price Drop: {address}", "intel_builder": _build_price_drop_intel},
    "new_listing": {"headline": "New Listing: {address}", "intel_builder": _build_simple_intel},
    "sold_listing": {"headline": "Just Sold Nearby: {address}", "intel_builder": _build_sold_intel},
    "back_on_market": {"headline": "Back on Market: {address}", "intel_builder": _build_simple_intel},
    "expired_listing": {"headline": "Expired Listing Opportunity: {address}", "intel_builder": _build_expired_intel},
    "coming_soon": {"headline": "Coming Soon: {address}", "intel_builder": _build_coming_soon_intel},
    "withdrawn_listing": {"headline": "Withdrawn Listing: {address}", "intel_builder": _build_withdrawn_intel},
}


def _calculate_match_score(client: Client, property_item: Property) -> tuple[int, list[str]]:
    """Calculates a match score between a client and a property."""
    score = 0
    reasons = []
    if any(loc.lower() in property_item.address.lower() for loc in client.preferences.get("locations", [])):
        score += 100
        reasons.append("Location Match")
    return score, reasons


async def _create_campaign_from_event(event: MarketEvent, realtor: User, property_item: Property, matched_audience: list[MatchedClient]):
    """Generates the AI message draft and saves the complete campaign briefing."""
    config = CAMPAIGN_CONFIG.get(event.event_type)
    if not config:
        print(f"NUDGE ENGINE: No campaign configuration for event type '{event.event_type}'. Skipping.")
        return

    headline = config["headline"].format(address=property_item.address)
    intel_builder = config["intel_builder"]
    key_intel = intel_builder(event, property_item)

    ai_draft = await conversation_agent.draft_outbound_campaign_message(
        realtor=realtor,
        property_item=property_item,
        event_type=event.event_type,
        matched_audience=matched_audience
    )
    
    audience_for_db = [m.model_dump(mode='json') for m in matched_audience]
    
    new_briefing = CampaignBriefing(
        id=uuid.uuid4(),
        user_id=realtor.id,
        campaign_type=event.event_type,
        status="new",
        headline=headline,
        key_intel=key_intel,
        listing_url=property_item.listing_url,
        original_draft=ai_draft,
        matched_audience=audience_for_db,
        triggering_event_id=event.id if event.id else uuid.uuid4()
    )
    crm_service.save_campaign_briefing(new_briefing)


async def process_market_event(event: MarketEvent, realtor: User):
    """The main entry point for the Nudge Engine to process a single market event."""
    print(f"NUDGE ENGINE: Processing event -> {event.event_type} for entity {event.entity_id}")
    property_item = crm_service.get_property_by_id(event.entity_id)
    if not property_item:
        print(f"NUDGE ENGINE: Property {event.entity_id} not found.")
        return

    all_clients = crm_service.get_all_clients()
    matched_audience = []
    
    if event.event_type in ["expired_listing", "withdrawn_listing"]:
        matched_audience.append(MatchedClient(client_id=realtor.id, client_name=realtor.full_name, match_score=100, match_reason="Seller Lead Opportunity"))
    else:
        for client in all_clients:
            score, reasons = _calculate_match_score(client, property_item)
            if score >= 100:
                matched_audience.append(MatchedClient(client_id=client.id, client_name=client.full_name, match_score=score, match_reason=", ".join(reasons)))

    if not matched_audience:
        print(f"NUDGE ENGINE: No matching audience found for event {event.id}.")
        return

    await _create_campaign_from_event(event, realtor, property_item, matched_audience)


# --- RESTORED: Relationship-based Nudge Generator ---
async def generate_recency_nudges(realtor: User):
    """
    Finds clients who haven't been contacted in a long time and creates a nudge.
    This is now restored as a standalone feature.
    """
    print("NUDGE ENGINE: Checking for clients needing a follow-up...")
    RECENCY_THRESHOLD_DAYS = 90
    
    all_clients = crm_service.get_all_clients()
    at_risk_clients = [
        client for client in all_clients 
        if not client.last_interaction or (datetime.now(timezone.utc) - datetime.fromisoformat(client.last_interaction)) > timedelta(days=RECENCY_THRESHOLD_DAYS)
    ]

    if not at_risk_clients:
        print("NUDGE ENGINE: No at-risk clients found for recency nudge.")
        return

    print(f"NUDGE ENGINE: Found {len(at_risk_clients)} at-risk clients. Generating nudge...")
    
    matched_audience = [MatchedClient(client_id=c.id, client_name=c.full_name, match_score=100, match_reason=f"Last contacted on {c.last_interaction or 'never'}") for c in at_risk_clients]
    
    ai_draft = await conversation_agent.draft_outbound_campaign_message(realtor=realtor, event_type="recency_nudge", matched_audience=matched_audience)
    
    recency_briefing = CampaignBriefing(
        id=uuid.uuid4(),
        user_id=realtor.id,
        campaign_type="recency_nudge",
        status="new",
        headline=f"Relationship Opportunity: {len(at_risk_clients)} clients need a follow-up",
        key_intel={"At-Risk Clients": len(at_risk_clients), "Threshold": f"{RECENCY_THRESHOLD_DAYS} days"},
        original_draft=ai_draft,
        matched_audience=[m.model_dump(mode='json') for m in matched_audience],
        triggering_event_id=uuid.uuid4()
    )
    crm_service.save_campaign_briefing(recency_briefing)


async def scan_for_all_market_events(realtor: User, minutes_ago: int = 60):
    """Connects to the MLS, fetches all new event types, and processes them."""
    mls_client = get_mls_client()
    if not mls_client:
        print("NUDGE ENGINE: Could not initialize MLS client. Aborting scan.")
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
        print(f"NUDGE ENGINE: Scanning for '{event_type}' events...")
        try:
            listings = fetcher_func(minutes_ago=minutes_ago)
            if listings:
                for listing_data in listings:
                    property_id = crm_service.get_all_properties()[0].id 
                    event = MarketEvent(event_type=event_type, entity_id=property_id, payload=listing_data)
                    await process_market_event(event, realtor)
        except Exception as e:
            print(f"NUDGE ENGINE: Error processing {event_type}: {e}")
