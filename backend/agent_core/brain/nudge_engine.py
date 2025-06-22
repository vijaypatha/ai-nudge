# ---
# File Path: backend/agent_core/brain/nudge_engine.py
# Purpose: The core engine for analyzing events and generating nudges.
# ---
from data.models.event import MarketEvent
from data.models.campaign import CampaignBriefing, MatchedClient
from data.models.user import User
from data.models.client import Client
from data.models.property import Property
from data import crm as crm_service
from agent_core.agents import conversation as conversation_agent

def _calculate_match_score(client: Client, property_item: Property) -> tuple[int, list[str]]:
    # ... (This function remains unchanged)
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
    """A helper function to create and save a campaign briefing."""
    key_intel = {
        "address": property_item.address,
        "price": f"${property_item.price:,.0f}",
    }
    if event.event_type == "price_drop":
        key_intel["price_change"] = f"-${event.payload.get('old_price', 0) - event.payload.get('new_price', 0):,}"

    prompt = prompt_template.format(property_address=property_item.address, price=key_intel["price"], listing_url=property_item.listing_url)

    ai_draft_result = await conversation_agent.generate_response(
        client_id=matched_audience[0].client_id,
        incoming_message_content=prompt,
        context={}
    )

    if ai_draft_result and ai_draft_result.get("ai_draft"):
        new_briefing = CampaignBriefing(
            user_id=realtor.id,
            campaign_type=event.event_type,
            headline=f"{event.event_type.replace('_', ' ').title()} on {property_item.address}",
            key_intel=key_intel,
            listing_url=property_item.listing_url,
            original_draft=ai_draft_result["ai_draft"],
            matched_audience=matched_audience,
            triggering_event_id=event.id
        )
        crm_service.save_campaign_briefing(new_briefing)

async def process_event_for_audience(event: MarketEvent, realtor: User):
    """Finds a matching audience for an event and generates a campaign."""
    property_item = crm_service.get_property_by_id(event.entity_id)
    if not property_item: return

    all_clients = crm_service.get_all_clients_mock()
    matched_audience = []
    for client in all_clients:
        match_score, reasons = _calculate_match_score(client, property_item)
        NUDGE_THRESHOLD = 70
        if match_score >= NUDGE_THRESHOLD:
            matched_audience.append(MatchedClient(client_id=client.id, client_name=client.full_name, match_score=match_score, match_reason=", ".join(reasons)))

    if not matched_audience:
        print(f"NUDGE ENGINE: No clients matched criteria for event {event.id}.")
        return

    # Define prompts based on event type
    prompts = {
        "price_drop": "Draft a master SMS about a price drop on {property_address} to {price}. IMPORTANT: You MUST include this URL: {listing_url}",
        "new_listing": "Draft a master SMS about a new property on the market at {property_address} for {price}. Give them a first look. IMPORTANT: You MUST include this URL: {listing_url}"
    }

    prompt_template = prompts.get(event.event_type)
    if prompt_template:
        await _generate_campaign_briefing(event, realtor, property_item, matched_audience, prompt_template)

async def process_market_event(event: MarketEvent, realtor: User):
    """Analyzes a market event and generates a Campaign Briefing."""
    print(f"NUDGE ENGINE: Processing event -> {event.event_type} for entity {event.entity_id}")
    if event.event_type in ["price_drop", "new_listing"]:
        await process_event_for_audience(event, realtor)