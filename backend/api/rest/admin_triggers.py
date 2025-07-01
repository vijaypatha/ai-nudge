# ---
# File Path: backend/api/rest/admin_triggers.py
# Purpose: Developer endpoints to manually trigger backend processes.
# --- UPDATED with a comprehensive test suite endpoint ---

from fastapi import APIRouter, status, HTTPException
from typing import Optional, List
import uuid
import asyncio

# --- Core Service Imports ---
from data import crm as crm_service
from agent_core.brain import nudge_engine
from integrations import twilio_incoming

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
    """Helper to fetch the default realtor USER and a specific or default property."""
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


# --- NEW: Comprehensive Test Suite Trigger ---
@router.post("/run-comprehensive-test", status_code=status.HTTP_202_ACCEPTED)
async def trigger_comprehensive_test_suite():
    """
    (DEBUG) Triggers a full suite of events to test all features at once.
    This single endpoint will populate the UI with one of every nudge type
    and simulate an incoming client message.
    """
    print("--- COMPREHENSIVE TEST SUITE INITIATED ---")
    realtor, property_item = _get_realtor_and_property()
    clients = crm_service.get_all_clients()
    if not clients:
        raise HTTPException(status_code=404, detail="Cannot run test suite without seeded clients.")
    
    test_client = clients[0]

    # 1. Trigger all market event nudges
    market_event_types = [
        "new_listing", "price_drop", "sold_listing", "back_on_market", 
        "expired_listing", "coming_soon", "withdrawn_listing"
    ]
    
    event_creation_tasks = []
    for event_type in market_event_types:
        print(f"TEST SUITE: Creating '{event_type}' event...")
        # Create a unique payload for price drop to ensure it's realistic
        payload = {"old_price": 1200000, "new_price": 1150000} if event_type == "price_drop" else {}
        event = MarketEvent(event_type=event_type, entity_id=property_item.id, payload=payload)
        event_creation_tasks.append(nudge_engine.process_market_event(event, realtor))
    
    # 2. Trigger relationship (recency) nudge
    print("TEST SUITE: Creating 'Recency' nudge...")
    event_creation_tasks.append(nudge_engine.generate_recency_nudges(realtor))

    # 3. Simulate an incoming SMS message
    if test_client.phone:
        print(f"TEST SUITE: Simulating incoming SMS from {test_client.full_name}...")
        event_creation_tasks.append(
            twilio_incoming.process_incoming_sms(
                from_number=test_client.phone, 
                body="Thanks for the update! Do you have any more details on the kitchen?"
            )
        )
    
    # Run all test events concurrently for speed
    await asyncio.gather(*event_creation_tasks)
    
    print("--- COMPREHENSIVE TEST SUITE COMPLETE ---")
    return {"status": "accepted", "message": "Comprehensive test suite initiated. Check UI for new nudges and messages."}


# --- Existing Triggers (can be used for individual testing) ---

@router.post("/run-market-scan", status_code=status.HTTP_202_ACCEPTED)
async def trigger_market_scan(minutes_ago: int = 60):
    """Manually triggers the full, autonomous market scan for market-based events."""
    realtor, _ = _get_realtor_and_property()
    await nudge_engine.scan_for_all_market_events(realtor=realtor, minutes_ago=minutes_ago)
    return {"status": "accepted", "message": f"Full market scan initiated, looking back {minutes_ago} minutes."}


@router.post("/run-daily-scan", status_code=status.HTTP_202_ACCEPTED)
async def trigger_daily_scan():
    """Manually triggers the daily scan for relationship-based nudges (recency)."""
    realtor, _ = _get_realtor_and_property()
    await nudge_engine.generate_recency_nudges(realtor=realtor) 
    return {"status": "accepted", "message": "Daily relationship scan for recency nudges initiated."}

# ... (all other individual create_*_event triggers remain unchanged) ...
