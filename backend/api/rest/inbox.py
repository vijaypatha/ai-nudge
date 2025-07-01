# File Path: backend/api/rest/inbox.py
# Purpose: Defines the public webhook for receiving incoming SMS from Twilio.
# --- UPDATED to use the new integration module for live Twilio messages ---

from fastapi import APIRouter, status, Form, Response

# --- Import the dedicated Twilio integration module ---
from integrations import twilio_incoming

router = APIRouter(
    prefix="/inbox",
    tags=["Inbox"]
)

@router.post("/twilio_inbound", status_code=status.HTTP_204_NO_CONTENT)
async def handle_twilio_inbound_sms(
    From: str = Form(...), 
    Body: str = Form(...)
):
    """
    Handles incoming SMS messages from Twilio's webhook.
    
    This endpoint acts as a thin wrapper. It receives the request,
    passes it to the integration layer for processing, and then sends
    an empty response back to Twilio to acknowledge receipt.
    """
    # The core logic is now handled by the integration module
    await twilio_incoming.process_incoming_sms(from_number=From, body=Body)
    
    # Always respond to Twilio with an empty TwiML response to prevent errors.
    return Response(content="<Response></Response>", media_type="application/xml")
