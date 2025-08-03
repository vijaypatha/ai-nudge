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
# --- FIXED: Defer import to prevent multiple registration ---
# from data.models.campaign import CampaignBriefing, MatchedClient
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
    
    print("TEST SUITE: Creating market events...")
    
    for event_type in market_event_types:
        print(f"TEST SUITE: Creating '{event_type}' event...")
        
        # Use the resource's attributes as the event payload for realistic matching
        payload = resource_item.attributes.copy()
        
        # Add event-specific data
        if event_type == "price_drop":
            payload.update({
                "old_price": 1200000,
                "new_price": 1150000,
                "ListPrice": 1150000  # Update the current price
            })
        elif event_type == "sold_listing":
            payload.update({
                "ClosePrice": 750000,
                "ListPrice": 750000
            })
        elif event_type == "new_listing":
            # Create a new listing that would match investor preferences
            payload.update({
                "ListPrice": 850000,
                "UnparsedAddress": "456 Multi-Family Drive, St. George, UT 84770",
                "PublicRemarks": "Excellent duplex opportunity with great cash flow potential. Each unit is 2 bed, 1 bath. Perfect for investment property. Close to downtown and university. Multi-family investment opportunity with rental income potential.",
                "BedroomsTotal": 4,
                "BathroomsTotalInteger": 2,
                "BuildingAreaTotal": 2400,
                "MlsStatus": "Active"
            })
        
        event = MarketEvent(event_type=event_type, entity_id=resource_item.id, payload=payload, market_area="default")
        await nudge_engine.process_market_event(event, current_user)

    if test_client.phone:
        print(f"TEST SUITE: Simulating incoming SMS from {test_client.full_name}...")
        await twilio_incoming.process_incoming_sms(
            from_number=test_client.phone, 
            body="Thanks for the update! Do you have any more details on the kitchen?"
        )
    
    print(f"--- COMPREHENSIVE TEST SUITE COMPLETE FOR USER {current_user.id} ---")
    return {"status": "accepted", "message": "Comprehensive test suite initiated."}

@router.post("/run-market-scan", status_code=status.HTTP_202_ACCEPTED)
async def trigger_market_scan(minutes_ago: int = 60, current_user: User = Depends(get_current_user_from_token)):
    """Trigger the main opportunity pipeline for the current user"""
    from workflow.pipeline import run_main_opportunity_pipeline
    await run_main_opportunity_pipeline()
    return {"status": "accepted", "message": f"Full market scan initiated for current user, looking back {minutes_ago} minutes."}

@router.post("/run-daily-scan", status_code=status.HTTP_202_ACCEPTED)
async def trigger_daily_scan(current_user: User = Depends(get_current_user_from_token)):
    return {"status": "accepted", "message": "Daily relationship scan initiated for current user."}

@router.post("/process-event/{event_id}", status_code=status.HTTP_202_ACCEPTED)
async def process_specific_event(event_id: str, current_user: User = Depends(get_current_user_from_token)):
    """Manually process a specific market event through the nudge engine"""
    from agent_core.brain import nudge_engine
    from data.database import Session
    from data.models.event import MarketEvent
    
    with Session(engine) as session:
        # Get the specific event
        event = session.get(MarketEvent, event_id)
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        
        # Process the event
        await nudge_engine.process_market_event(event, current_user, session)
        
    return {"status": "accepted", "message": f"Event {event_id} processed successfully."}

# backend/api/rest/admin_triggers.py
# --- PRODUCTION MONITORING ENDPOINTS ---

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from data.database import engine
from data.models.message import Message, MessageStatus, ScheduledMessage
from data.models.user import User
from api.security import get_current_user_from_token

# Use the existing router from above, just add the monitoring endpoints

@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Comprehensive health check for the application."""
    try:
        # Database connectivity
        with Session(engine) as session:
            # Test basic query
            user_count = session.exec(select(User)).first()
            
            # Check recent message activity
            recent_messages = session.exec(
                select(Message).where(
                    Message.created_at >= datetime.now(timezone.utc) - timedelta(hours=1)
                )
            ).all()
            
            # Check pending scheduled messages
            pending_scheduled = session.exec(
                select(ScheduledMessage).where(ScheduledMessage.status == MessageStatus.PENDING)
            ).all()
            
            # Check failed messages
            failed_messages = session.exec(
                select(Message).where(Message.status == MessageStatus.FAILED)
            ).all()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "database": "connected",
            "recent_messages_count": len(recent_messages),
            "pending_scheduled_count": len(pending_scheduled),
            "failed_messages_count": len(failed_messages)
        }
        
    except Exception as e:
        logging.error(f"Health check failed: {e}", exc_info=True)
        return {
            "status": "unhealthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(e)
        }

@router.get("/metrics")
async def get_metrics() -> Dict[str, Any]:
    """Get key metrics for monitoring."""
    try:
        with Session(engine) as session:
            # Message metrics
            total_messages = session.exec(select(Message)).all()
            sent_messages = [m for m in total_messages if m.status == MessageStatus.SENT]
            failed_messages = [m for m in total_messages if m.status == MessageStatus.FAILED]
            
            # Scheduled message metrics
            total_scheduled = session.exec(select(ScheduledMessage)).all()
            pending_scheduled = [m for m in total_scheduled if m.status == MessageStatus.PENDING]
            sent_scheduled = [m for m in total_scheduled if m.status == MessageStatus.SENT]
            
            # User metrics
            total_users = session.exec(select(User)).all()
            
            return {
                "messages": {
                    "total": len(total_messages),
                    "sent": len(sent_messages),
                    "failed": len(failed_messages),
                    "success_rate": len(sent_messages) / len(total_messages) if total_messages else 0
                },
                "scheduled_messages": {
                    "total": len(total_scheduled),
                    "pending": len(pending_scheduled),
                    "sent": len(sent_scheduled)
                },
                "users": {
                    "total": len(total_users)
                }
            }
            
    except Exception as e:
        logging.error(f"Metrics collection failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to collect metrics")

@router.get("/alerts")
async def get_alerts() -> List[Dict[str, Any]]:
    """Get current alerts for monitoring."""
    alerts = []
    
    try:
        with Session(engine) as session:
            # Check for failed messages
            failed_messages = session.exec(
                select(Message).where(Message.status == MessageStatus.FAILED)
            ).all()
            
            if failed_messages:
                alerts.append({
                    "type": "failed_messages",
                    "severity": "high",
                    "count": len(failed_messages),
                    "message": f"{len(failed_messages)} messages failed to send"
                })
            
            # Check for stuck scheduled messages
            old_pending = session.exec(
                select(ScheduledMessage).where(
                    ScheduledMessage.status == MessageStatus.PENDING,
                    ScheduledMessage.scheduled_at_utc < datetime.now(timezone.utc) - timedelta(hours=1)
                )
            ).all()
            
            if old_pending:
                alerts.append({
                    "type": "stuck_scheduled_messages",
                    "severity": "medium",
                    "count": len(old_pending),
                    "message": f"{len(old_pending)} scheduled messages are overdue"
                })
        
        return alerts
        
    except Exception as e:
        logging.error(f"Alert collection failed: {e}", exc_info=True)
        return [{
            "type": "system_error",
            "severity": "critical",
            "message": f"Failed to collect alerts: {str(e)}"
        }]