# ---
# File Path: backend/agent_core/brain/nudge_engine.py
# This is the FINAL, DEFINITIVE fix for all JSON serialization errors.
# ---

import uuid
from datetime import datetime, timezone, timedelta
from data.models.event import MarketEvent
from data.models.campaign import CampaignBriefing, MatchedClient
from data.models.user import User
from data.models.client import Client
from data.models.property import Property
from data import crm as crm_service
from agent_core.agents import conversation as conversation_agent


def _calculate_match_score(client: Client, property_item: Property) -> tuple[int, list[str]]:
    score = 0
    reasons = []
    client_locations = client.preferences.get("locations", [])
    budget_max = client.preferences.get("budget_max", float('inf'))
    min_bedrooms = client.preferences.get("min_bedrooms", 0)

    if property_item.address and any(loc.lower() in property_item.address.lower() for loc in client_locations):
        score += 50
        reasons.append("Location Match")
    if property_item.price <= budget_max:
        score += 30
        reasons.append("Under Budget")
    if property_item.bedrooms and property_item.bedrooms >= min_bedrooms:
        score += 20
        reasons.append("Met Bedroom Criteria")
    return score, reasons


async def _create_campaign_from_event(event: MarketEvent, realtor: User, property_item: Property, matched_audience: list[MatchedClient]):
    """
    Generates the AI message draft and saves the complete campaign briefing.
    """
    key_intel = {"address": property_item.address, "price": f"${property_item.price:,.0f}"}
    if event.event_type == "price_drop":
        price_change = event.payload.get('old_price', 0) - event.payload.get('new_price', 0)
        key_intel["price_change"] = f"${price_change:,.0f}"

    ai_draft = await conversation_agent.draft_outbound_campaign_message(
        realtor=realtor,
        property_item=property_item,
        event_type=event.event_type,
        matched_audience=matched_audience
    )
    
    # Use Pydantic's .model_dump() to create a JSON-serializable list of dictionaries.
    audience_for_db = [m.model_dump(mode='json') for m in matched_audience]
    
    new_briefing = CampaignBriefing(
        id=uuid.uuid4(),
        user_id=realtor.id,
        campaign_type=event.event_type,
        status="new",
        headline=f"Price Drop: {property_item.address}",
        key_intel=key_intel,
        listing_url=property_item.listing_url,
        original_draft=ai_draft,
        matched_audience=audience_for_db,
        triggering_event_id=event.id if event.id else uuid.uuid4()
    )
    crm_service.save_campaign_briefing(new_briefing)


async def process_event_for_audience(event: MarketEvent, realtor: User):
    """
    Finds a matching audience for an event, then creates a Nudge.
    """
    property_item = crm_service.get_property_by_id(event.entity_id)
    if not property_item:
        print(f"NUDGE ENGINE: Property {event.entity_id} not found.")
        return

    all_clients = crm_service.get_all_clients()
    matched_audience = []
    NUDGE_THRESHOLD = 70
    
    for client in all_clients:
        score, reasons = _calculate_match_score(client, property_item)
        if score >= NUDGE_THRESHOLD:
            matched_audience.append(MatchedClient(client_id=client.id, client_name=client.full_name, match_score=score, match_reason=", ".join(reasons)))

    if not matched_audience:
        print(f"NUDGE ENGINE: No clients met the threshold for event {event.id}.")
        return

    await _create_campaign_from_event(event, realtor, property_item, matched_audience)


async def generate_recency_nudges():
    """
    Finds clients who haven't been contacted in a long time and creates a nudge.
    """
    print("NUDGE ENGINE: Checking for clients needing a follow-up...")
    RECENCY_THRESHOLD_DAYS = 90
    
    realtor = crm_service.get_user_by_id(uuid.UUID("a8c6f1d7-8f7a-4b6e-8b0f-9e5a7d6c5b4a"))
    if not realtor: return

    all_clients = crm_service.get_all_clients()
    at_risk_clients = []

    for client in all_clients:
        is_at_risk = False
        if client.last_interaction:
            last_contact_date = datetime.fromisoformat(client.last_interaction)
            if (datetime.now(timezone.utc) - last_contact_date) > timedelta(days=RECENCY_THRESHOLD_DAYS):
                is_at_risk = True
        else:
            is_at_risk = True
        
        if is_at_risk:
            at_risk_clients.append(client)

    if not at_risk_clients:
        print("NUDGE ENGINE: No clients are at risk.")
        return

    print(f"NUDGE ENGINE: Found {len(at_risk_clients)} at-risk clients. Generating nudge...")
    
    matched_audience_for_agent = [MatchedClient(client_id=c.id, client_name=c.full_name, match_score=100, match_reason=f"Last contacted on {c.last_interaction or 'never'}") for c in at_risk_clients]
    
    ai_draft = await conversation_agent.draft_outbound_campaign_message(
        realtor=realtor,
        event_type="recency_nudge",
        matched_audience=matched_audience_for_agent
    )

    # --- DEFINITIVE FIX ---
    # Use Pydantic's .model_dump() here as well to ensure data is serializable.
    audience_for_db = [m.model_dump(mode='json') for m in matched_audience_for_agent]

    recency_briefing = CampaignBriefing(
        id=uuid.uuid4(),
        user_id=realtor.id,
        campaign_type="recency_nudge",
        status="new",
        headline=f"Relationship Opportunity: {len(at_risk_clients)} clients need a follow-up",
        key_intel={"At-Risk Clients": len(at_risk_clients), "Threshold": f"{RECENCY_THRESHOLD_DAYS} days"},
        original_draft=ai_draft,
        matched_audience=audience_for_db,
        triggering_event_id=uuid.uuid4()
    )
    crm_service.save_campaign_briefing(recency_briefing)

async def process_market_event(event: MarketEvent, realtor: User):
    """
    The main entry point for the Nudge Engine.
    """
    print(f"NUDGE ENGINE: Processing event -> {event.event_type} for entity {event.entity_id}")
    if event.event_type in ["price_drop", "new_listing"]:
        await process_event_for_audience(event, realtor)