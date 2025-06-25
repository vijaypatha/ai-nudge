# FILE: backend/integrations/twilio_outgoing.py
# PURPOSE: Handles all direct communication with the Twilio API for sending messages.

import os
import logging
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

# --- (FIX) Use absolute import for shared utilities ---
from common.config import (
    TWILIO_ACCOUNT_SID,
    TWILIO_AUTH_TOKEN,
    TWILIO_PHONE_NUMBER
)

logger = logging.getLogger(__name__)

# --- Initialize the Twilio Client ---
# We check if the credentials exist before creating the client.
if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
    twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    logger.info("Twilio client initialized successfully.")
else:
    twilio_client = None
    logger.warning("Twilio credentials not found. SMS sending will be disabled.")

def send_sms(to_number: str, body: str) -> bool:
    """
    Sends an SMS message using the Twilio API.

    Args:
        to_number (str): The recipient's phone number in E.164 format.
        body (str): The text content of the message.

    Returns:
        bool: True if the message was sent successfully, False otherwise.
    """
    if not twilio_client or not TWILIO_PHONE_NUMBER:
        logger.error("Cannot send SMS: Twilio client or phone number is not configured.")
        return False

    try:
        logger.info(f"Sending SMS to {to_number} via Twilio...")
        message = twilio_client.messages.create(
            to=to_number,
            from_=TWILIO_PHONE_NUMBER,
            body=body
        )
        logger.info(f"SMS sent successfully. Message SID: {message.sid}")
        return True
    except TwilioRestException as e:
        logger.error(f"Failed to send SMS to {to_number}. Twilio error: {e}")
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred while sending SMS: {e}")
        return False