# backend/integrations/twilio_incoming.py
# --- FINAL VERSION: Broadcasts to both client and user channels ---

import logging
from typing import List

from agent_core import orchestrator
from common.config import get_settings
from data import crm as crm_service
from data.database import engine
from data.models.message import (
    Message,
    MessageDirection,
    MessageStatus,
    MessageSource,
    MessageSenderType,
)
from data.models.faq import Faq
from integrations import twilio_outgoing
from integrations.gemini import match_faq_with_gemini
from sqlmodel import Session, select
from api.websocket_manager import manager as websocket_manager

settings = get_settings()

async def get_user_faqs(user_id: str) -> List[dict]:
    """Get all enabled FAQs for a user as simple dict list"""
    with Session(engine) as session:
        faqs = session.exec(
            select(Faq).where(Faq.user_id == user_id, Faq.is_enabled == True)
        ).all()

        return [
            {
                "question": faq.question,
                "answer": faq.answer,
            }
            for faq in faqs
        ]

async def process_incoming_sms(from_number: str, to_number: str, body: str):
    """
    Process incoming SMS, log it, and broadcast a real-time notification.
    """
    logging.info(f"TWILIO: Processing SMS from '{from_number}' to '{to_number}': '{body}'")

    user = crm_service.get_user_by_twilio_number(to_number)
    if not user:
        logging.error(f"TWILIO: No user found for destination number {to_number}. Discarding message.")
        return

    found_client = crm_service.get_client_by_phone(phone_number=from_number, user_id=user.id)
    if not found_client:
        logging.error(f"TWILIO: No client with number {from_number} found for user {user.id}. Discarding message.")
        return

    logging.info(f"TWILIO: Matched to user '{user.full_name}' (ID: {user.id}) and client '{found_client.full_name}' (ID: {found_client.id}).")

    incoming_message = Message(
        client_id=found_client.id,
        user_id=user.id,
        content=body,
        direction=MessageDirection.INBOUND,
        status=MessageStatus.RECEIVED,
        source=MessageSource.MANUAL, # Source is manual as it's from the client
        sender_type=MessageSenderType.USER, # Sender is the client (a type of user)
    )
    
    try:
        # Use a variable to capture the saved message with its generated ID and timestamps
        saved_message = crm_service.save_message(incoming_message)
        logging.info(f"TWILIO: Logged incoming message from client {found_client.id}")

        # --- BEGIN FIX: Broadcast the full message to BOTH client and user channels ---
        try:
            # Pydantic models need to be converted to dicts for JSON serialization.
            # .model_dump(mode='json') handles types like UUID and datetime correctly.
            message_payload = saved_message.model_dump(mode='json')
            
            notification = {
                "type": "NEW_MESSAGE",
                "payload": message_payload
            }
            
            # 1. Broadcast to the specific client channel (for detailed conversation views)
            await websocket_manager.broadcast_json_to_client(
                client_id=str(found_client.id),
                data=notification
            )
            
            # 2. Broadcast to the general user channel (for list views and global notifications)
            await websocket_manager.broadcast_to_user(
                user_id=str(user.id),
                data=notification
            )
            logging.info(f"TWILIO: Broadcasted WebSocket notifications for client {found_client.id} to user {user.id}")

        except Exception as e:
            logging.error(f"TWILIO: Failed to broadcast WebSocket notification. Error: {e}", exc_info=True)
        # --- END FIX ---

    except Exception as e:
        logging.error(f"TWILIO: Failed to save incoming message: {e}", exc_info=True)
        return

    # 4. FAQ AUTO-REPLY (Original functionality preserved)
    if settings.FAQ_AUTO_REPLY_ENABLED:
        try:
            user_faqs = await get_user_faqs(user.id)
            if user_faqs:
                logging.info(f"TWILIO: Checking {len(user_faqs)} FAQs for user {user.id}")
                faq_response = await match_faq_with_gemini(body, user_faqs)

                if faq_response:
                    logging.info(f"TWILIO: FAQ matched, sending response: '{faq_response}'")

                    sms_sent_successfully = twilio_outgoing.send_sms(
                        to_number=from_number,
                        body=faq_response[:320],
                        from_number=to_number,
                    )
                    
                    if sms_sent_successfully:
                        outgoing_message = Message(
                            client_id=found_client.id,
                            user_id=user.id,
                            content=faq_response[:320],
                            direction=MessageDirection.OUTBOUND,
                            status=MessageStatus.SENT,
                            source=MessageSource.FAQ_AUTO_RESPONSE,
                            sender_type=MessageSenderType.SYSTEM,
                        )
                        crm_service.save_message(outgoing_message)
                        logging.info(f"TWILIO: Logged outgoing FAQ response for client {found_client.id}")
                    return
        except Exception as e:
            logging.error(f"TWILIO: FAQ processing error: {e}", exc_info=True)

    # 5. Fallback to AI orchestrator (Original functionality preserved)
    try:
        await orchestrator.handle_incoming_message(
            client_id=found_client.id, incoming_message=saved_message, user=user
        )
        logging.info(f"TWILIO: AI orchestrator triggered for client {found_client.id}")
    except Exception as e:
        logging.error(f"TWILIO: AI orchestrator failed: {e}", exc_info=True)