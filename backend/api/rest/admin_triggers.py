# ---
# File Path: backend/api/rest/admin_triggers.py
# Purpose: Developer endpoints to manually trigger backend processes.
# --- COMPREHENSIVELY FIXED ---

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
    This is the core fix for the ForeignKeyViolation error.
    """
    # --- FIX: Fetch the specific User (realtor) instead of a Client ---
    # The system relies on a known, hardcoded user for these operations.
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


@router.post("/run-daily-scan", status_code=status.HTTP_202_ACCEPTED)
async def trigger_daily_scan():
    """
    Manually triggers the daily scan for relationship-based nudges (recency).
    """
    # This function correctly calls the nudge_engine which handles fetching its own user.
    await nudge_engine.generate_recency_nudges()
    return {"status": "accepted", "message": "Daily relationship scan initiated."}


@router.post("/create-sold-event", status_code=status.HTTP_202_ACCEPTED)
async def trigger_sold_event(property_id: Optional[uuid.UUID] = None):
    """
    (DEBUG ENDPOINT) Manually triggers a 'sold_listing' event for a property.
    """
    realtor, property_item = _get_realtor_and_property(property_id)

    # --- FIX: Removed 'neighborhood' to prevent AttributeError ---
    sold_event = MarketEvent(
        event_type="sold_listing",
        entity_id=property_item.id,
        payload={"sold_price": property_item.price}
    )
    
    await nudge_engine.process_market_event(sold_event, realtor)
    
    return {"status": "accepted", "message": f"'Sold Listing' event triggered for property: {property_item.address}"}


@router.post("/create-back-on-market-event", status_code=status.HTTP_202_ACCEPTED)
async def trigger_back_on_market_event(property_id: Optional[uuid.UUID] = None):
    """
    (DEBUG ENDPOINT) Manually triggers a 'back_on_market' event for a property.
    """
    realtor, property_item = _get_realtor_and_property(property_id)

    back_on_market_event = MarketEvent(
        event_type="back_on_market",
        entity_id=property_item.id,
        payload={"previous_status": "Pending", "current_status": "Active"}
    )
    
    await nudge_engine.process_market_event(back_on_market_event, realtor)
    
    return {"status": "accepted", "message": f"'Back on Market' event triggered for property: {property_item.address}"}


@router.post("/create-test-nudge", status_code=status.HTTP_201_CREATED)
async def create_test_nudge(count: int = 1):
    """
    (DEBUG ENDPOINT) Creates one or more hardcoded 'price_drop' CampaignBriefings.
    """
    # Uses the robust helper to get a real user and property.
    realtor, property_item = _get_realtor_and_property()
    
    clients = crm_service.get_all_clients()
    if not clients:
        raise HTTPException(status_code=404, detail="No clients found to create audience.")

    for i in range(count):
        key_intel = {"Price Change": "-$50,000", "Address": property_item.address}
        headline = f"Price Drop: {property_item.address}"

        matched_client_data = [
            MatchedClient(client_id=c.id, client_name=c.full_name, match_score=95, match_reason="Test Audience")
            for c in clients[:1]
        ]

        test_briefing = CampaignBriefing(
            user_id=realtor.id, # Uses the correct realtor ID
            campaign_type="price_drop",
            headline=headline,
            key_intel=key_intel,
            original_draft=f"Hi [Client Name], a test property at {property_item.address} just had a price drop. This is nudge #{i+1}.",
            matched_audience=[m.model_dump(mode='json') for m in matched_client_data],
            triggering_event_id=property_item.id,
            status="new"
        )
        crm_service.save_campaign_briefing(test_briefing)
    
    return {"message": f"Successfully created {count} test nudge(s)."}
