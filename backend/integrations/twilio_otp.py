# ---
# File Path: backend/integrations/twilio_otp.py
# Purpose: Handles Twilio Verify v2 API for sending and checking OTPs.
# ---
import logging
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from common.config import get_settings

logger = logging.getLogger(__name__)

# --- Get the settings object once ---
settings = get_settings()

# --- Initialize the Twilio Client ---
if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
    twilio_client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    logger.info("Twilio client initialized for Verify V2 service.")
else:
    twilio_client = None
    logger.warning("Twilio credentials not found. OTP verification will be disabled.")

# --- Helper function to get the Verify Service SID ---
def _get_verify_service_sid():
    """
    Retrieves the Twilio Verify Service SID from settings.
    This is required for all Verify v2 API calls.
    """
    if not settings.TWILIO_VERIFY_SERVICE_SID:
        logger.critical("CRITICAL: TWILIO_VERIFY_SERVICE_SID is not configured in settings.")
        return None
    return settings.TWILIO_VERIFY_SERVICE_SID

# --- DEFINITIVE IMPLEMENTATION of send_verification_token ---
def send_verification_token(phone_number: str) -> bool:
    """
    Sends a verification token (OTP) to the given phone number using Twilio Verify V2.
    """
    verify_sid = _get_verify_service_sid()
    if not twilio_client or not verify_sid:
        logger.error("Cannot send verification: Twilio client or Verify Service SID is not configured.")
        return False

    try:
        logger.info(f"Sending verification token to {phone_number} using service {verify_sid}")
        verification = twilio_client.verify.v2.services(verify_sid).verifications.create(
            to=phone_number,
            channel='sms'
        )
        logger.info(f"Verification sent successfully. Status: {verification.status}")
        return True
    except TwilioRestException as e:
        logger.error(f"Failed to send verification to {phone_number}. Twilio error: {e}")
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred while sending verification: {e}")
        return False

# --- DEFINITIVE IMPLEMENTATION of check_verification_token ---
def check_verification_token(phone_number: str, code: str) -> bool:
    """
    Checks if the provided verification code is valid for the phone number.
    """
    verify_sid = _get_verify_service_sid()
    if not twilio_client or not verify_sid:
        logger.error("Cannot check verification: Twilio client or Verify Service SID is not configured.")
        return False

    try:
        logger.info(f"Checking verification token for {phone_number}")
        verification_check = twilio_client.verify.v2.services(verify_sid).verification_checks.create(
            to=phone_number,
            code=code
        )
        logger.info(f"Verification check for {phone_number} status: {verification_check.status}")
        return verification_check.status == 'approved'
    except TwilioRestException as e:
        # A 404 error from Twilio means the code was incorrect. This is not a server error.
        if e.status == 404:
            logger.warning(f"Incorrect OTP code provided for {phone_number}.")
        else:
            logger.error(f"Failed to check verification for {phone_number}. Twilio error: {e}")
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred during verification check: {e}")
        return False