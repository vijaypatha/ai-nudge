# ---
# File Path: backend/api/rest/admin_triggers.py
# Purpose: Developer endpoints to manually trigger backend processes.
# --- CORRECTED to fix TypeError in /run-daily-scan endpoint ---

from fastapi import APIRouter, status, HTTPException
from typing import Optional
import uuid

# --- Core Service Imports ---
from data import crm as crm_service
from agent_core.brain import nudge_engine

# --- Model Imports ---
from data.models.campaign import CampaignBriefing, MatchedClient
from data.models.event import MarketEvent
from data.models.property import Property
from data.models.user import User


router = APIRouter(
    prefix="/admin/triggers",
    tags=["Admin: Triggers"]
)


def _get_realtor_and_property(property_id: Optional[uuid.UUID] = None) -> tuple[User, Property]:
    """
    Helper to fetch the default realtor USER and a specific or default property.
    """
    realtor_id = uuid.UUID("a8c6f1d7-8f7a-4b6e-8b0f-9e5a7d6c5b4a")
    realtor = crm_service.get_user_by_id(realtor_id)
    if not realtor:
        raise HTTPException(status_code=404, detail=f"Realtor user with ID {realtor_id} not found.")

    if property_id:
        property_item = crm_service.get_property_by_id(property_id)
        if not property_item:
            raise HTTPException(status_code=404, detail=f"Property with id {property_id} not found.")
    else:
        properties = crm_service.get_all_properties()
        if not properties:
            raise HTTPException(status_code=404, detail="No properties found in the database.")
        property_item = properties[0]
    
    return realtor, property_item


@router.post("/run-market-scan", status_code=status.HTTP_202_ACCEPTED)
async def trigger_market_scan(minutes_ago: int = 60):
    """
    Manually triggers the full, autonomous market scan for market-based events.
    """
    realtor, _ = _get_realtor_and_property()
    await nudge_engine.scan_for_all_market_events(realtor=realtor, minutes_ago=minutes_ago)
    return {"status": "accepted", "message": f"Full market scan initiated, looking back {minutes_ago} minutes."}


@router.post("/run-daily-scan", status_code=status.HTTP_202_ACCEPTED)
async def trigger_daily_scan():
    """
    Manually triggers the daily scan for relationship-based nudges (recency).
    """
    # --- FIX: Fetches the realtor user first. ---
    realtor, _ = _get_realtor_and_property()
    # --- FIX: Passes the required 'realtor' argument to the function call. ---
    await nudge_engine.generate_recency_nudges(realtor=realtor) 
    return {"status": "accepted", "message": "Daily relationship scan for recency nudges initiated."}


# --- Individual Event Triggers for Testing ---

@router.post("/create-sold-event", status_code=status.HTTP_202_ACCEPTED)
async def trigger_sold_event(property_id: Optional[uuid.UUID] = None):
    """(DEBUG) Manually triggers a 'sold_listing' event."""
    realtor, property_item = _get_realtor_and_property(property_id)
    event = MarketEvent(event_type="sold_listing", entity_id=property_item.id, payload={"sold_price": property_item.price})
    await nudge_engine.process_market_event(event, realtor)
    return {"status": "accepted", "message": f"'Sold Listing' event triggered for property: {property_item.address}"}


@router.post("/create-back-on-market-event", status_code=status.HTTP_202_ACCEPTED)
async def trigger_back_on_market_event(property_id: Optional[uuid.UUID] = None):
    """(DEBUG) Manually triggers a 'back_on_market' event."""
    realtor, property_item = _get_realtor_and_property(property_id)
    event = MarketEvent(event_type="back_on_market", entity_id=property_item.id, payload={})
    await nudge_engine.process_market_event(event, realtor)
    return {"status": "accepted", "message": f"'Back on Market' event triggered for property: {property_item.address}"}


@router.post("/create-expired-event", status_code=status.HTTP_202_ACCEPTED)
async def trigger_expired_event(property_id: Optional[uuid.UUID] = None):
    """(DEBUG) Manually triggers an 'expired_listing' event."""
    realtor, property_item = _get_realtor_and_property(property_id)
    event = MarketEvent(event_type="expired_listing", entity_id=property_item.id, payload={})
    await nudge_engine.process_market_event(event, realtor)
    return {"status": "accepted", "message": f"'Expired Listing' event triggered for property: {property_item.address}"}


@router.post("/create-coming-soon-event", status_code=status.HTTP_202_ACCEPTED)
async def trigger_coming_soon_event(property_id: Optional[uuid.UUID] = None):
    """(DEBUG) Manually triggers a 'coming_soon' event."""
    realtor, property_item = _get_realtor_and_property(property_id)
    event = MarketEvent(event_type="coming_soon", entity_id=property_item.id, payload={})
    await nudge_engine.process_market_event(event, realtor)
    return {"status": "accepted", "message": f"'Coming Soon' event triggered for property: {property_item.address}"}


@router.post("/create-withdrawn-event", status_code=status.HTTP_202_ACCEPTED)
async def trigger_withdrawn_event(property_id: Optional[uuid.UUID] = None):
    """(DEBUG) Manually triggers a 'withdrawn_listing' event."""
    realtor, property_item = _get_realtor_and_property(property_id)
    event = MarketEvent(event_type="withdrawn_listing", entity_id=property_item.id, payload={})
    await nudge_engine.process_market_event(event, realtor)
    return {"status": "accepted", "message": f"'Withdrawn Listing' event triggered for property: {property_item.address}"}


@router.post("/create-test-nudge", status_code=status.HTTP_201_CREATED)
async def create_test_nudge(count: int = 1):
    """(DEBUG) Creates one or more hardcoded 'price_drop' CampaignBriefings."""
    realtor, property_item = _get_realtor_and_property()
    clients = crm_service.get_all_clients()
    if not clients:
        raise HTTPException(status_code=404, detail="No clients found to create audience.")

    for i in range(count):
        key_intel = {"Price Change": "-$50,000", "Address": property_item.address}
        headline = f"Price Drop: {property_item.address}"
        matched_client_data = [MatchedClient(client_id=c.id, client_name=c.full_name, match_score=95, match_reason="Test Audience") for c in clients[:1]]
        test_briefing = CampaignBriefing(
            user_id=realtor.id,
            campaign_type="price_drop",
            headline=headline,
            key_intel=key_intel,
            original_draft=f"Hi [Client Name], a test property at {property_item.address} just had a price drop.",
            matched_audience=[m.model_dump(mode='json') for m in matched_client_data],
            triggering_event_id=property_item.id,
            status="new"
        )
        crm_service.save_campaign_briefing(test_briefing)
    
    return {"message": f"Successfully created {count} test nudge(s)."}
