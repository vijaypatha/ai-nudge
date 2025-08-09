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
from backend.api.websocket_manager import manager as websocket_manager

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
    Process incoming SMS, log it, and publish a notification to Redis for
    real-time broadcasting.
    """
    logging.info(f"TWILIO: Processing SMS from '{from_number}' to '{to_number}': '{body}'")

    # --- THIS IS THE FIX ---
    # Initialize the Redis client and channel name once at the top level
    # to ensure a stable connection is used.
    import redis
    import json
    from common.config import get_settings
    settings = get_settings()
    redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    USER_NOTIFICATION_CHANNEL = "user-notifications"
    # --- END OF FIX ---

    with Session(engine) as session:
        user = crm_service.get_user_by_twilio_number(to_number, session=session)
        if not user:
            logging.error(f"TWILIO: No user found for destination number {to_number}. Discarding message.")
            return

        found_client = crm_service.get_client_by_phone(phone_number=from_number, user_id=user.id, session=session)
        if not found_client:
            logging.error(f"TWILIO: No client with number {from_number} found for user {user.id}. Discarding message.")
            return

        logging.info(f"TWILIO: Matched to user '{user.full_name}' and client '{found_client.full_name}'.")

        incoming_message = Message(
            client_id=found_client.id,
            user_id=user.id,
            content=body,
            direction=MessageDirection.INBOUND,
            status=MessageStatus.RECEIVED,
            source=MessageSource.MANUAL,
            sender_type=MessageSenderType.USER,
        )
        
        try:
            saved_message = crm_service.save_message(incoming_message, session=session)
            # Ensure the message is actually committed so downstream readers see it
            session.commit()
            session.refresh(saved_message)
            logging.info(f"TWILIO: Logged and committed incoming message from client {found_client.id}")

            # Publish the NEW_MESSAGE event to the Redis channel AFTER commit
            message_payload = json.loads(saved_message.model_dump_json())
            notification_payload = {
                "user_id": str(user.id),
                "payload": {"type": "NEW_MESSAGE", "payload": message_payload}
            }
            redis_client.publish(USER_NOTIFICATION_CHANNEL, json.dumps(notification_payload))
            logging.info(f"TWILIO: Published 'NEW_MESSAGE' event to Redis for user {user.id}")

            # Also broadcast directly to any WebSocket connections in this process for instant UI updates
            try:
                await websocket_manager.send_to_user_connections(
                    str(user.id), {"type": "NEW_MESSAGE", "payload": message_payload}
                )
                logging.info(f"TWILIO: Also broadcasted 'NEW_MESSAGE' directly to user {user.id} connections.")
            except Exception as ws_err:
                logging.warning(f"TWILIO: Direct WS broadcast failed (will rely on Redis): {ws_err}")

        except Exception as e:
            logging.error(f"TWILIO: Failed to save or publish incoming message: {e}", exc_info=True)
            session.rollback()
            return

    # FAQ AUTO-REPLY (This logic remains unchanged)
    if settings.FAQ_AUTO_REPLY_ENABLED and user.faq_auto_responder_enabled:
        try:
            user_faqs = await get_user_faqs(user.id)
            if user_faqs:
                logging.info(f"TWILIO: Checking {len(user_faqs)} FAQs for user {user.id}")
                faq_response = await match_faq_with_gemini(body, user_faqs)

                if faq_response:
                    logging.info(f"TWILIO: FAQ matched, sending response: '{faq_response}'")

                    if twilio_outgoing.send_sms(to_number=from_number, body=faq_response[:320], from_number=to_number):
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

    # Fallback to AI orchestrator (This logic remains unchanged)
    try:
        await orchestrator.handle_incoming_message(
            client_id=found_client.id, incoming_message=saved_message, user=user
        )
        logging.info(f"TWILIO: AI orchestrator triggered for client {found_client.id}")
    except Exception as e:
        logging.error(f"TWILIO: AI orchestrator failed: {e}", exc_info=True)