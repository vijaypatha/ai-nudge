# ---
# File Path: backend/integrations/twilio_outgoing.py
# Purpose: Handles Twilio messaging using the new config pattern.
# ---
import logging
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from common.config import get_settings # <-- CHANGED: Import the get_settings function

logger = logging.getLogger(__name__)

# --- Get the settings object once ---
settings = get_settings()

# --- Initialize the Twilio Client ---
if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
    # <-- CHANGED: Use settings object for credentials
    twilio_client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    logger.info("Twilio client initialized successfully.")
else:
    twilio_client = None
    logger.warning("Twilio credentials not found. SMS sending will be disabled.")

def send_sms(to_number: str, body: str) -> bool:
    """
    Sends an SMS message using the Twilio API.
    """
    # <-- CHANGED: Use settings object for phone number
    if not twilio_client or not settings.TWILIO_PHONE_NUMBER:
        logger.error("Cannot send SMS: Twilio client or phone number is not configured.")
        return False

    try:
        logger.info(f"Sending SMS to {to_number} via Twilio...")
        message = twilio_client.messages.create(
            to=to_number,
            from_=settings.TWILIO_PHONE_NUMBER, # <-- CHANGED: Use settings object
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