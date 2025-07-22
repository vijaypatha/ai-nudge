# File Path: backend/api/webhooks/calendar.py
# Purpose: Calendar webhook endpoints

from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class CalendarWebhookPayload(BaseModel):
    """Calendar webhook payload model"""
    event_id: Optional[str] = None
    event_type: Optional[str] = None
    user_id: Optional[str] = None

@router.post("/events")
async def calendar_events_webhook(request: Request):
    """Handle calendar events from external calendar services"""
    try:
        body = await request.json()
        # Process calendar events
        return {"status": "success", "message": "Calendar event processed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing calendar webhook: {str(e)}")

@router.post("/availability")
async def calendar_availability_webhook(request: Request):
    """Handle availability updates from calendar services"""
    try:
        body = await request.json()
        # Process availability updates
        return {"status": "success", "message": "Availability update processed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing availability: {str(e)}")

@router.get("/health")
async def calendar_webhook_health():
    """Health check for calendar webhooks"""
    return {"status": "healthy", "service": "calendar-webhooks"}
