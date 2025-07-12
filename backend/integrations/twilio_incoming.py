# backend/integrations/twilio_incoming.py
import logging
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


async def process_incoming_sms(from_number: str, body: str):
    """
    Process incoming SMS with simplified FAQ matching using Gemini
    """
    logging.info(f"TWILIO: Processing SMS from {from_number}: '{body}'")

    # 1. Find client
    all_users: list[User] = crm_service.get_all_users()
    found_client: Client | None = None

    for user in all_users:
        client_for_user = crm_service.get_client_by_phone(
            phone_number=from_number, user_id=user.id
        )
        if client_for_user:
            found_client = client_for_user
            break

    if not found_client:
        logging.error(f"TWILIO: No client found for {from_number}")
        return

    # 2. Get realtor
    realtor = crm_service.get_user_by_id(found_client.user_id)
    if not realtor:
        logging.error(f"TWILIO: No realtor found for client {found_client.id}")
        return

    # 3. Log incoming message
    incoming_message = Message(
        client_id=found_client.id,
        user_id=realtor.id,
        content=body,
        direction=MessageDirection.INBOUND,
        status=MessageStatus.RECEIVED,
    )

    try:
        crm_service.save_message(incoming_message)
        logging.info(f"TWILIO: Logged incoming message from client {found_client.id}")
    except Exception as e:
        logging.error(f"TWILIO: Failed to save incoming message: {e}")
        return

    # 4. FAQ AUTO-REPLY with Gemini
    if settings.FAQ_AUTO_REPLY_ENABLED:
        try:
            user_faqs = await get_user_faqs(realtor.id)
            if user_faqs:
                logging.info(f"TWILIO: Checking {len(user_faqs)} FAQs for user {realtor.id}")
                faq_response = await match_faq_with_gemini(body, user_faqs)
                
                if faq_response:
                    logging.info(f"TWILIO: FAQ matched, sending response: '{faq_response}'")
                    
                    # --- FIX 1: REMOVED 'await' from the synchronous function call ---
                    sms_sent_successfully = twilio_outgoing.send_sms(
                        to_number=from_number,
                        body=faq_response[:320], # Truncate to 320 characters
                        from_number=settings.TWILIO_PHONE_NUMBER,
                    )

                    # Only proceed if the SMS was confirmed as sent
                    if sms_sent_successfully:
                        # --- FIX 2: ADDED logic to log the outgoing message ---
                        outgoing_message = Message(
                            client_id=found_client.id,
                            user_id=realtor.id,
                            content=faq_response[:320], # Log the same truncated content
                            direction=MessageDirection.OUTBOUND,
                            status=MessageStatus.SENT,
                        )
                        try:
                            crm_service.save_message(outgoing_message)
                            logging.info(
                                f"TWILIO: Logged outgoing FAQ response for client {found_client.id}"
                            )
                        except Exception as e:
                            logging.error(f"TWILIO: Failed to save outgoing FAQ message: {e}")
                    
                    # --- FIX 3: CRITICAL early return to prevent orchestrator ---
                    return

        except Exception as e:
            logging.error(f"TWILIO: FAQ processing error: {e}")
            # Don't return here - let it fall through to orchestrator only on a true failure
    # 5. Fallback to AI orchestrator
    try:
        await orchestrator.handle_incoming_message(
            client_id=found_client.id, incoming_message=incoming_message, realtor=realtor
        )
        logging.info(f"TWILIO: AI orchestrator triggered for client {found_client.id}")
    except Exception as e:
        logging.error(f"TWILIO: AI orchestrator failed: {e}")