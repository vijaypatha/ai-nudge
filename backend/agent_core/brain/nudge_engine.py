# File Path: backend/agent_core/brain/nudge_engine.py
# Purpose: The core engine for analyzing events and creating campaigns.
# This version is UPDATED to ensure all UUIDs in JSON fields are strings.

import uuid
from data.models.event import MarketEvent
from data.models.campaign import CampaignBriefing, MatchedClient
from data.models.user import User
from data.models.client import Client
from data.models.property import Property
from data import crm as crm_service
from agent_core.agents import conversation as conversation_agent

def _calculate_match_score(client: Client, property_item: Property) -> tuple[int, list[str]]:
    """
    Calculates a 'match score' between a client and a property based on preferences.
    """
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
    elif property_item.price <= budget_max * 1.1:
        score += 15
        reasons.append("Slightly Over Budget")
    if property_item.bedrooms and property_item.bedrooms >= min_bedrooms:
        score += 20
        reasons.append("Met Bedroom Criteria")
        if property_item.bedrooms > min_bedrooms:
            score += 5
            reasons.append("Bonus: More Bedrooms")

    return score, reasons

def _matched_client_to_dict(m: MatchedClient):
    # Ensure UUIDs are strings for JSON serialization
    d = m.model_dump()
    if 'client_id' in d and isinstance(d['client_id'], uuid.UUID):
        d['client_id'] = str(d['client_id'])
    return d

async def _create_campaign_from_event(event: MarketEvent, realtor: User, property_item: Property, matched_audience: list[MatchedClient]):
    """
    Generates the AI message draft via the Conversation Agent and saves the complete campaign briefing.
    """
    key_intel = {
        "address": property_item.address,
        "price": f"${property_item.price:,.0f}",
    }
    if event.event_type == "price_drop":
        price_change = event.payload.get('old_price', 0) - event.payload.get('new_price', 0)
        key_intel["price_change"] = f"${price_change:,.0f}"

    # Ensure no UUIDs in key_intel (if you ever add one, convert to str)

    ai_draft = await conversation_agent.draft_outbound_campaign_message(
        realtor=realtor,
        property_item=property_item,
        event_type=event.event_type,
        matched_audience=matched_audience
    )

    # Convert all UUIDs in matched_audience to strings
    matched_audience_json = [_matched_client_to_dict(m) for m in matched_audience]

    # Ensure triggering_event_id is a string if used in a JSON column (but it's probably a UUID column, so safe)
    new_briefing = CampaignBriefing(
        user_id=realtor.id,
        campaign_type=event.event_type,
        status="new",
        headline=f"Price Drop: {property_item.address}",
        key_intel=key_intel,
        listing_url=property_item.listing_url,
        original_draft=ai_draft,
        matched_audience=matched_audience_json,
        triggering_event_id=event.id if event.id else uuid.uuid4()
    )
    crm_service.save_campaign_briefing(new_briefing)

async def process_event_for_audience(event: MarketEvent, realtor: User):
    """
    Finds a matching audience for an event, then creates a Nudge or an Insight.
    """
    property_item = crm_service.get_property_by_id(event.entity_id)
    if not property_item: return

    all_clients = crm_service.get_all_clients()
    matched_audience = []
    for client in all_clients:
        match_score, reasons = _calculate_match_score(client, property_item)
        NUDGE_THRESHOLD = 70
        if match_score >= NUDGE_THRESHOLD:
            matched_audience.append(MatchedClient(client_id=client.id, client_name=client.full_name, match_score=match_score, match_reason=", ".join(reasons)))

    if not matched_audience:
        print(f"NUDGE ENGINE: No matching clients, creating an Insight for event {event.id}.")
        key_intel = {"address": property_item.address, "price": f"${property_item.price:,.0f}"}
        if event.event_type == "price_drop":
             price_change = event.payload.get('old_price', 0) - event.payload.get('new_price', 0)
             key_intel["price_change"] = f"${price_change:,.0f}"

        insight_briefing = CampaignBriefing(
            user_id=realtor.id,
            campaign_type=event.event_type,
            status="insight",
            headline=f"Market Insight: Price Drop on {property_item.address}",
            key_intel=key_intel,
            listing_url=property_item.listing_url,
            original_draft="",
            matched_audience=[],
            triggering_event_id=event.id if event.id else uuid.uuid4()
        )
        crm_service.save_campaign_briefing(insight_briefing)
        return

    await _create_campaign_from_event(event, realtor, property_item, matched_audience)

async def process_market_event(event: MarketEvent, realtor: User):
    """
    The main entry point for the Nudge Engine.
    """
    print(f"NUDGE ENGINE: Processing event -> {event.event_type} for entity {event.entity_id}")
    if event.event_type in ["price_drop", "new_listing"]:
        await process_event_for_audience(event, realtor)
