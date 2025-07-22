# File Path: backend/api/webhooks/router.py
# Purpose: Central router for webhook endpoints

from fastapi import APIRouter

# Create the webhooks router
webhooks_router = APIRouter()

# NOTE: Actual webhook endpoints are implemented in the REST API files:
# - Twilio webhooks: /api/twilio/incoming-sms and /api/inbox/twilio_inbound
# - MLS integration: Uses scheduled polling, not webhooks
# - Calendar: Not implemented

@webhooks_router.get("/")
async def webhooks_root():
    """Root endpoint for webhooks"""
    return {"message": "Webhooks endpoint is working", "note": "Actual webhooks are in REST API files"} 