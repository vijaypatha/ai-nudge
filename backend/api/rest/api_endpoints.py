# File Path: backend/api/rest/api_endpoints.py
# --- CORRECTED: Removed references to the obsolete 'properties' router.

from fastapi import APIRouter
from datetime import datetime, timezone
import os

# --- MODIFIED: Removed 'properties' from the import list ---
from . import admin_triggers, auth, campaigns, clients, conversations, faqs, inbox, nudges, users, scheduled_messages, community, twilio_numbers, websockets, content_resources, mls

api_router = APIRouter()

# Include all the individual routers
api_router.include_router(admin_triggers.router)
api_router.include_router(auth.router)
api_router.include_router(campaigns.router)
api_router.include_router(clients.router)
api_router.include_router(conversations.router)
api_router.include_router(faqs.router)
api_router.include_router(inbox.router)
api_router.include_router(nudges.router)
api_router.include_router(users.router)
api_router.include_router(scheduled_messages.router)
api_router.include_router(community.router)
api_router.include_router(twilio_numbers.router)
api_router.include_router(websockets.router)
api_router.include_router(content_resources.router, prefix="/content-resources", tags=["content-resources"])

api_router.include_router(mls.router)

# --- ADDED: Simple properties endpoint to prevent 404 errors ---
@api_router.get("/properties")
async def get_properties():
    """Temporary endpoint to prevent 404 errors. Returns empty array."""
    return []

# --- ADDED: Market events endpoint ---
@api_router.get("/market-events")
async def get_market_events():
    """Get market events for the current user."""
    try:
        from data.database import get_session
        from data.models.event import MarketEvent
        from sqlmodel import select
        
        with next(get_session()) as session:
            # For now, get all market events (in production this would be filtered by user)
            events = session.exec(
                select(MarketEvent)
                .order_by(MarketEvent.created_at.desc())
                .limit(10)
            ).all()
            
            return [
                {
                    "id": str(event.id),
                    "event_type": event.event_type,
                    "entity_id": event.entity_id,
                    "payload": event.payload,
                    "created_at": event.created_at.isoformat(),
                    "status": event.status
                }
                for event in events
            ]
    except Exception as e:
        return {"error": str(e)}

# --- ADDED: Pipeline status endpoint (public, no auth required) ---
@api_router.get("/pipeline-status")
async def get_pipeline_status():
    """Get the status of the automated pipeline and last run time."""
    try:
        from data.database import get_session
        from data.models.event import PipelineRun
        from sqlmodel import select, func
        
        with next(get_session()) as session:
            # Get the most recent completed pipeline run
            latest_run = session.exec(
                select(PipelineRun)
                .where(PipelineRun.status == "completed")
                .order_by(PipelineRun.completed_at.desc())
            ).first()
            
            if latest_run:
                # Calculate hours ago
                now = datetime.now(timezone.utc)
                # Ensure completed_at is timezone-aware
                completed_at = latest_run.completed_at
                if completed_at.tzinfo is None:
                    completed_at = completed_at.replace(tzinfo=timezone.utc)
                hours_ago = (now - completed_at).total_seconds() / 3600
                
                return {
                    "status": "active",
                    "last_run": latest_run.completed_at.isoformat(),
                    "hours_ago": round(hours_ago, 1),
                    "next_run": "every 2 hours",
                    "events_processed": latest_run.events_processed,
                    "campaigns_created": latest_run.campaigns_created
                }
            else:
                return {
                    "status": "unknown",
                    "last_run": None,
                    "hours_ago": None,
                    "next_run": "every 2 hours",
                    "events_processed": 0,
                    "campaigns_created": 0
                }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "last_run": None,
            "hours_ago": None,
            "next_run": "every 2 hours",
            "events_processed": 0,
            "campaigns_created": 0
        }

# --- ADDED: Market activity endpoint ---
@api_router.get("/market-activity")
async def get_market_activity(limit: int = 1000):
    """Get shared market activity and business opportunity data for all users."""
    try:
        from data.database import get_session
        from data.models.event import MarketEvent
        from sqlmodel import select
        
        with next(get_session()) as session:
            # Get market events and business opportunities from all users (shared data)
            # Default to 1000 to get all properties, but allow custom limit
            events = session.exec(
                select(MarketEvent)
                .order_by(MarketEvent.created_at.desc())
                .limit(limit)
            ).all()
            
            return [
                {
                    "id": str(event.id),
                    "event_type": event.event_type,
                    "entity_id": event.entity_id,
                    "payload": event.payload,
                    "created_at": event.created_at.isoformat(),
                    "status": event.status,
                    "market_area": event.market_area
                }
                for event in events
            ]
    except Exception as e:
        return {"error": str(e)} 