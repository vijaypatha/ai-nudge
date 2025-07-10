# backend/integrations/twilio_outgoing.py
# DEFINITIVE FIX: The `send_sms` function is updated to accept a `from_number`
# parameter, making it multi-tenant aware and capable of sending messages
# from the user's specific AI Nudge number.

import logging
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from common.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

try:
    twilio_client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    logger.info("Twilio client initialized successfully.")
except Exception as e:
    twilio_client = None
    logger.warning(f"Twilio credentials not found. SMS sending will be disabled. Error: {e}")

# --- MODIFIED: Added 'from_number' parameter ---
def send_sms(from_number: str, to_number: str, body: str) -> bool:
    """
    Sends an SMS message using the Twilio API from a specific number.
    """
    if not twilio_client:
        logger.error("Cannot send SMS: Twilio client is not configured.")
        return False
        
    # --- ADDED: Validation for the from_number ---
    if not from_number:
        logger.error(f"Cannot send SMS to {to_number}: A 'from_number' was not provided.")
        return False

    try:
        logger.info(f"Sending SMS from {from_number} to {to_number} via Twilio...")
        message = twilio_client.messages.create(
            to=to_number,
            from_=from_number, # <-- Use the provided from_number
            body=body
        )
        logger.info(f"SMS sent successfully. Message SID: {message.sid}")
        return True
    except TwilioRestException as e:
        logger.error(f"Failed to send SMS to {to_number} from {from_number}. Twilio error: {e}")
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred while sending SMS: {e}")
        return False