# File Path: backend/agent_core/brain/nudge_engine.py
# Purpose: The core engine for analyzing events. This version is updated to create a low-confidence "Insight" when no matching clients are found for a market event, ensuring no opportunity is wasted.

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
    budget_max = client.preferences.get("budget_max", float("inf"))
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

async def _generate_campaign_briefing(event: MarketEvent, realtor: User, property_item: Property, matched_audience: list[MatchedClient], prompt_template: str):
    """
    Generates the AI message draft and saves the complete high-confidence campaign briefing.
    """
    key_intel = {
        "address": property_item.address,
        "price": property_item.price, # Use raw number for calculations
    }
    if event.event_type == "price_drop":
        key_intel["price_change"] = event.payload.get('old_price', 0) - event.payload.get('new_price', 0)

    prompt = prompt_template.format(property_address=property_item.address, price=f"${property_item.price:,.0f}", listing_url=property_item.listing_url)

    # For now, we are not making a real LLM call to save time and cost.
    # In a real scenario, this would be: await conversation_agent.generate_response(...)
    ai_draft = f"Hi [Client Name], good news! The price on {property_item.address} was just reduced. Thought you might be interested. Let me know if you'd like to see it. {property_item.listing_url}"
    
    new_briefing = CampaignBriefing(
        user_id=realtor.id,
        campaign_type=event.event_type,
        status="new", # 'new' status indicates a high-confidence, ready-to-send nudge
        headline=f"Price Drop: {property_item.address}",
        key_intel=key_intel,
        listing_url=property_item.listing_url,
        original_draft=ai_draft,
        matched_audience=matched_audience,
        triggering_event_id=event.id
    )
    crm_service.save_campaign_briefing(new_briefing)

async def process_event_for_audience(event: MarketEvent, realtor: User):
    """
    Finds a matching audience for an event. If matches are found, it generates a
    high-confidence Nudge. If not, it generates a low-confidence Insight.
    """
    property_item = crm_service.get_property_by_id(event.entity_id)
    if not property_item: return

    all_clients = crm_service.get_all_clients_mock()
    matched_audience = []
    for client in all_clients:
        match_score, reasons = _calculate_match_score(client, property_item)
        NUDGE_THRESHOLD = 70
        if match_score >= NUDGE_THRESHOLD:
            matched_audience.append(MatchedClient(client_id=client.id, client_name=client.full_name, match_score=match_score, match_reason=", ".join(reasons)))

    # --- THIS IS THE CORE LOGIC CHANGE ---
    if not matched_audience:
        # If no clients are a good match, create a low-confidence "Insight" card instead of doing nothing.
        print(f"NUDGE ENGINE: No matching clients, creating an Insight for event {event.id}.")
        
        key_intel = {
            "address": property_item.address,
            "price": property_item.price,
        }
        if event.event_type == "price_drop":
            key_intel["price_change"] = event.payload.get('old_price', 0) - event.payload.get('new_price', 0)

        insight_briefing = CampaignBriefing(
            user_id=realtor.id,
            campaign_type=event.event_type,
            status="insight", # This special status tells the frontend to render the low-confidence card
            headline=f"Market Insight: Price Drop on {property_item.address}",
            key_intel=key_intel,
            listing_url=property_item.listing_url,
            original_draft="", # No message needed
            matched_audience=[], # Audience is empty
            triggering_event_id=event.id
        )
        crm_service.save_campaign_briefing(insight_briefing)
        return # End execution here for this path

    # If we DO have a matched audience, proceed with generating the high-confidence nudge.
    prompts = {
        "price_drop": "Draft a master SMS about a price drop on {property_address} to {price}. IMPORTANT: You MUST include this URL: {listing_url}",
        "new_listing": "Draft a master SMS about a new property on the market at {property_address} for {price}. Give them a first look. IMPORTANT: You MUST include this URL: {listing_url}"
    }

    prompt_template = prompts.get(event.event_type)
    if prompt_template:
        await _generate_campaign_briefing(event, realtor, property_item, matched_audience, prompt_template)

async def process_market_event(event: MarketEvent, realtor: User):
    """
    The main entry point for the Nudge Engine.
    """
    print(f"NUDGE ENGINE: Processing event -> {event.event_type} for entity {event.entity_id}")
    if event.event_type in ["price_drop", "new_listing"]:
        await process_event_for_audience(event, realtor)