# ---
# File Path: backend/integrations/twilio_incoming.py
# Purpose: Handles the business logic for processing incoming SMS from Twilio.
# ---
import uuid

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
    print(f"TWILIO INTEGRATION: Processing SMS from {from_number}: '{body}'")
    
    # --- MODIFIED: Securely find the client in a multi-tenant way ---
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
        print(f"TWILIO INTEGRATION: ERROR - No client found for phone number {from_number}. Message will be ignored.")
        return

    # 3. Now that we have the client, we know the user/realtor.
    realtor = crm_service.get_user_by_id(found_client.user_id)
    if not realtor:
        print(f"TWILIO INTEGRATION ERROR: Could not find the user owner for client {found_client.id}.")
        return

    # 4. Log the incoming message to our universal conversation log.
    try:
        incoming_message = Message(
            client_id=found_client.id,
            user_id=realtor.id, # Also log the user_id on the message
            content=body,
            direction=MessageDirection.INBOUND,
            status=MessageStatus.RECEIVED
        )
        crm_service.save_message(incoming_message)
        print(f"TWILIO INTEGRATION: Logged incoming message from client {found_client.id}")
    except Exception as e:
        print(f"TWILIO INTEGRATION: ERROR - Failed to save message to database: {e}")
        return

    # 5. Trigger the AI orchestrator to process the message and generate a response draft.
    try:
        await orchestrator.handle_incoming_message(
            client_id=found_client.id,
            incoming_message_content=body,
            realtor=realtor # Pass the full realtor object
        )
        print(f"TWILIO INTEGRATION: AI orchestrator triggered for client {found_client.id}")
    except Exception as e:
        print(f"TWILIO INTEGRATION: ERROR - AI orchestrator failed for client {found_client.id}: {e}")