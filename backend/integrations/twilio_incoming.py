# backend/integrations/twilio_incoming.py
# --- UPDATED: Now broadcasts a WebSocket event on new messages ---

import logging
import json
from typing import List

from agent_core import orchestrator
from common.config import get_settings
from data import crm as crm_service
from data.database import engine
from data.models.client import Client
from data.models.faq import Faq
from data.models.message import Message, MessageDirection, MessageStatus
from data.models.user import User
from integrations import twilio_outgoing
from integrations.gemini import match_faq_with_gemini
from sqlmodel import Session, select
from api.websocket_manager import manager as websocket_manager # Import the manager

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

    # 1. Find the user (agent) being texted via their dedicated Twilio number.
    user = crm_service.get_user_by_twilio_number(to_number)
    if not user:
        logging.error(f"TWILIO: No user found for destination number {to_number}. Discarding message.")
        return

    # 2. Find the client associated with that specific user.
    found_client = crm_service.get_client_by_phone(phone_number=from_number, user_id=user.id)
    if not found_client:
        logging.error(f"TWILIO: No client with number {from_number} found for user {user.id}. Discarding message.")
        return

    logging.info(f"TWILIO: Matched to user '{user.full_name}' (ID: {user.id}) and client '{found_client.full_name}' (ID: {found_client.id}).")

    # 3. Log incoming message and then broadcast
    incoming_message = Message(
        client_id=found_client.id,
        user_id=user.id,
        content=body,
        direction=MessageDirection.INBOUND,
        status=MessageStatus.RECEIVED,
    )
    try:
        crm_service.save_message(incoming_message)
        logging.info(f"TWILIO: Logged incoming message from client {found_client.id}")

        # --- NEW: Broadcast a notification after successfully saving. ---
        try:
            notification = {
                "type": "NEW_MESSAGE",
                "clientId": str(found_client.id)
            }
            await websocket_manager.broadcast_to_client(
                client_id=str(found_client.id),
                message=json.dumps(notification)
            )
        except Exception as e:
            logging.error(f"TWILIO: Failed to broadcast WebSocket notification for client {found_client.id}. Error: {e}")

    except Exception as e:
        logging.error(f"TWILIO: Failed to save incoming message: {e}")
        return

    # 4. FAQ AUTO-REPLY (logic is unchanged)
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
                        from_number=to_number, # Reply from the number that was texted
                    )

                    if sms_sent_successfully:
                        outgoing_message = Message(
                            client_id=found_client.id,
                            user_id=user.id,
                            content=faq_response[:320],
                            direction=MessageDirection.OUTBOUND,
                            status=MessageStatus.SENT,
                        )
                        crm_service.save_message(outgoing_message)
                        logging.info(f"TWILIO: Logged outgoing FAQ response for client {found_client.id}")

                    return
        except Exception as e:
            logging.error(f"TWILIO: FAQ processing error: {e}", exc_info=True)


    # 5. Fallback to AI orchestrator (logic is unchanged)
    try:
        await orchestrator.handle_incoming_message(
            client_id=found_client.id, incoming_message=incoming_message, user=user
        )
        logging.info(f"TWILIO: AI orchestrator triggered for client {found_client.id}")
    except Exception as e:
        logging.error(f"TWILIO: AI orchestrator failed: {e}", exc_info=True)