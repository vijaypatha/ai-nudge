# ---
# File Path: backend/integrations/twilio_incoming.py
# Purpose: Handles the business logic for processing incoming SMS from Twilio.
# ---
import uuid
import logging # Use logging instead of print for production code

from agent_core import orchestrator
from data import crm as crm_service
from data.models.message import Message, MessageDirection, MessageStatus
from data.models.client import Client
from data.models.user import User

async def process_incoming_sms(from_number: str, body: str):
    """
    Core logic to process an incoming SMS message.
    
    This function finds the client, logs the message, and triggers the AI
    orchestrator to generate a response. It's called by the API endpoint.

    Args:
        from_number (str): The phone number the message came from.
        body (str): The content of the SMS message.
    """
    logging.info(f"TWILIO INTEGRATION: Processing SMS from {from_number}: '{body}'")
    
    # 1. Get all users from the system.
    all_users: list[User] = crm_service.get_all_users()
    found_client: Client | None = None
    
    # 2. Check each user's contact list for the phone number.
    for user in all_users:
        client_for_user = crm_service.get_client_by_phone(phone_number=from_number, user_id=user.id)
        if client_for_user:
            found_client = client_for_user
            break # Stop searching once we find the client

    if not found_client:
        logging.error(f"TWILIO INTEGRATION: No client found for phone number {from_number}. Message will be ignored.")
        return

    # 3. Now that we have the client, we know the user/realtor.
    realtor = crm_service.get_user_by_id(found_client.user_id)
    if not realtor:
        logging.error(f"TWILIO INTEGRATION: Could not find the user owner for client {found_client.id}.")
        return

    # 4. Log the incoming message to our universal conversation log. THIS IS KEPT FOR RELIABILITY.
    incoming_message = Message(
        client_id=found_client.id,
        user_id=realtor.id,
        content=body,
        direction=MessageDirection.INBOUND,
        status=MessageStatus.RECEIVED
    )
    try:
        # The save_message function creates its own session and commits immediately.
        crm_service.save_message(incoming_message)
        logging.info(f"TWILIO INTEGRATION: Logged incoming message from client {found_client.id}")
    except Exception as e:
        logging.error(f"TWILIO INTEGRATION: Failed to save message to database: {e}")
        return

    # 5. Trigger the AI orchestrator, NOW PASSING THE SAVED MESSAGE OBJECT.
    try:
        await orchestrator.handle_incoming_message(
            client_id=found_client.id,
            # --- MODIFIED: Pass the full message object to the orchestrator ---
            incoming_message=incoming_message,
            realtor=realtor
        )
        logging.info(f"TWILIO INTEGRATION: AI orchestrator triggered for client {found_client.id}")
    except Exception as e:
        logging.error(f"TWILIO INTEGRATION: AI orchestrator failed for client {found_client.id}: {e}")