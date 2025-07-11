# File Path: backend/api/rest/admin_triggers.py
# --- CORRECTED: Refactored to use the generic Resource model instead of the deleted Property model.

from fastapi import APIRouter, status, HTTPException, Depends
from typing import Optional, List
import uuid
import asyncio

from data.models.user import User
from api.security import get_current_user_from_token
from data import crm as crm_service
from agent_core.brain import nudge_engine
from integrations import twilio_incoming
from data.models.campaign import CampaignBriefing, MatchedClient
from data.models.event import MarketEvent
# --- MODIFIED: Import Resource instead of Property ---
from data.models.resource import Resource

router = APIRouter(
    prefix="/admin/triggers",
    tags=["Admin: Triggers"]
)

# --- MODIFIED: Helper function now gets a 'property' type Resource ---
def _get_resource_for_test(user_id: uuid.UUID, resource_id: Optional[uuid.UUID] = None) -> Resource:
    """Helper to fetch a specific or default resource of type 'property' for testing."""
    if resource_id:
        resource_item = crm_service.get_resource_by_id(resource_id, user_id)
        if not resource_item:
            raise HTTPException(status_code=404, detail=f"Resource with id {resource_id} not found.")
        if resource_item.resource_type != 'property':
             raise HTTPException(status_code=400, detail=f"Resource {resource_id} is not a 'property' type.")
    else:
        resources = crm_service.get_all_resources_for_user(user_id)
        # Filter for property resources specifically for this test suite
        property_resources = [r for r in resources if r.resource_type == 'property']
        if not property_resources:
            raise HTTPException(status_code=404, detail="No 'property' type resources found in the database for this user.")
        resource_item = property_resources[0]
    
    return resource_item

# --- MODIFIED: Uses the new _get_resource_for_test helper ---
@router.post("/run-comprehensive-test", status_code=status.HTTP_202_ACCEPTED)
async def trigger_comprehensive_test_suite(current_user: User = Depends(get_current_user_from_token)):
    print(f"--- COMPREHENSIVE TEST SUITE INITIATED FOR USER {current_user.id} ---")
    resource_item = _get_resource_for_test(user_id=current_user.id)
    clients = crm_service.get_all_clients(user_id=current_user.id)
    if not clients:
        raise HTTPException(status_code=404, detail=f"Cannot run test suite without seeded clients for user {current_user.id}.")
    
    test_client = clients[0]

    market_event_types = [
        "new_listing", "price_drop", "sold_listing", "back_on_market", 
        "expired_listing", "coming_soon", "withdrawn_listing"
    ]
    
    event_creation_tasks = []
    for event_type in market_event_types:
        print(f"TEST SUITE: Creating '{event_type}' event...")
        payload = {"old_price": 1200000, "new_price": 1150000} if event_type == "price_drop" else {}
        event = MarketEvent(event_type=event_type, entity_id=resource_item.id, payload=payload, market_area="default")
        event_creation_tasks.append(nudge_engine.process_market_event(event, current_user))
    
    print("TEST SUITE: Creating 'Recency' nudge...")
    event_creation_tasks.append(nudge_engine.generate_recency_nudges(current_user))

    if test_client.phone:
        print(f"TEST SUITE: Simulating incoming SMS from {test_client.full_name}...")
        event_creation_tasks.append(
            twilio_incoming.process_incoming_sms(
                from_number=test_client.phone, 
                body="Thanks for the update! Do you have any more details on the kitchen?"
            )
        )
    
    await asyncio.gather(*event_creation_tasks)
    
    print(f"--- COMPREHENSIVE TEST SUITE COMPLETE FOR USER {current_user.id} ---")
    return {"status": "accepted", "message": "Comprehensive test suite initiated."}

@router.post("/run-market-scan", status_code=status.HTTP_202_ACCEPTED)
async def trigger_market_scan(minutes_ago: int = 60, current_user: User = Depends(get_current_user_from_token)):
    await nudge_engine.scan_for_all_market_events(realtor=current_user, minutes_ago=minutes_ago)
    return {"status": "accepted", "message": f"Full market scan initiated for current user, looking back {minutes_ago} minutes."}

@router.post("/run-daily-scan", status_code=status.HTTP_202_ACCEPTED)
async def trigger_daily_scan(current_user: User = Depends(get_current_user_from_token)):
    await nudge_engine.generate_recency_nudges(realtor=current_user) 
    return {"status": "accepted", "message": "Daily relationship scan for recency nudges initiated for current user."}