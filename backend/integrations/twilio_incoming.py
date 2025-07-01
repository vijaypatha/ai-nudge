# ---
# File Path: backend/integrations/twilio_incoming.py
# Purpose: Handles the business logic for processing incoming SMS from Twilio.
# ---
import uuid

from agent_core import orchestrator
from data import crm as crm_service
from data.models.message import Message, MessageDirection, MessageStatus

async def process_incoming_sms(from_number: str, body: str):
    """
    Core logic to process an incoming SMS message.
    
    This function finds the client, logs the message, and triggers the AI
    orchestrator to generate a response. It's called by the API endpoint.

    Args:
        from_number (str): The phone number the message came from.
        body (str): The content of the SMS message.
    """
    print(f"TWILIO INTEGRATION: Processing SMS from {from_number}: '{body}'")
    
    # 1. Find the client by their phone number.
    client = crm_service.get_client_by_phone(phone_number=from_number)
    if not client:
        print(f"TWILIO INTEGRATION: ERROR - No client found for phone number {from_number}. Message will be ignored.")
        # Return early if no client is found. The API layer will handle the response to Twilio.
        return

    # 2. Log the incoming message to our universal conversation log.
    try:
        incoming_message = Message(
            client_id=client.id,
            content=body,
            direction=MessageDirection.INBOUND,
            status=MessageStatus.RECEIVED
        )
        crm_service.save_message(incoming_message)
        print(f"TWILIO INTEGRATION: Logged incoming message from client {client.id}")
    except Exception as e:
        print(f"TWILIO INTEGRATION: ERROR - Failed to save message to database: {e}")
        # If saving fails, we stop processing to avoid further errors.
        return

    # 3. Trigger the AI orchestrator to process the message and generate a response draft.
    try:
        await orchestrator.handle_incoming_message(
            client_id=client.id,
            incoming_message_content=body
        )
        print(f"TWILIO INTEGRATION: AI orchestrator triggered for client {client.id}")
    except Exception as e:
        print(f"TWILIO INTEGRATION: ERROR - AI orchestrator failed for client {client.id}: {e}")

