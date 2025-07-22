# File Path: backend/api/webhooks/router.py
# Purpose: Central router for webhook endpoints

from fastapi import APIRouter

# Create the webhooks router
webhooks_router = APIRouter()

# Import webhook endpoints
from . import twilio, calendar, mls

# Include webhook routes
webhooks_router.include_router(twilio.router, prefix="/twilio", tags=["Twilio Webhooks"])
webhooks_router.include_router(calendar.router, prefix="/calendar", tags=["Calendar Webhooks"])
webhooks_router.include_router(mls.router, prefix="/mls", tags=["MLS Webhooks"])

@webhooks_router.get("/")
async def webhooks_root():
    """Root endpoint for webhooks"""
    return {"message": "Webhooks endpoint is working"} 