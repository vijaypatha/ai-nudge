# backend/api/rest/twilio_numbers.py
# DEFINITIVE FIX: Adds a check for the development environment to simulate
# the Twilio number purchase, preventing real charges during testing.

import logging
import os  # Import the 'os' module
from urllib.parse import parse_qs
from types import SimpleNamespace  # Import SimpleNamespace for mocking
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from typing import List, Optional
from pydantic import BaseModel
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from twilio.base.exceptions import TwilioRestException

from common.config import get_settings
from data.models.user import User, UserUpdate
from api.security import get_current_user_from_token
from data import crm as crm_service
from integrations import twilio_incoming # Import the processing logic

# --- Router and Logger Setup ---
router = APIRouter(prefix="/twilio", tags=["Twilio"])
logger = logging.getLogger(__name__)
settings = get_settings()

# --- Initialize Twilio Client ---
try:
    twilio_client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    logger.info("Twilio client initialized for number services.")
except Exception as e:
    twilio_client = None
    logger.error(f"Failed to initialize Twilio client: {e}")

# --- Pydantic Models ---
class AvailableNumber(BaseModel):
    phone_number: str
    friendly_name: str

class NumberSearchResponse(BaseModel):
    numbers: List[AvailableNumber]

class AssignNumberPayload(BaseModel):
    phone_number: str

# --- API Endpoints ---

@router.get("/numbers", response_model=NumberSearchResponse)
def search_available_numbers(
    area_code: Optional[str] = Query(None, min_length=3, max_length=3),
    zip_code: Optional[str] = Query(None, min_length=5, max_length=5),
    current_user: User = Depends(get_current_user_from_token)
):
    """
    Searches for available Twilio phone numbers by area code or ZIP code.
    """
    if not twilio_client:
        raise HTTPException(status_code=503, detail="Twilio service is not available.")
    if not area_code and not zip_code:
        raise HTTPException(status_code=400, detail="Either area_code or zip_code must be provided.")

    search_params = {
        "sms_enabled": True,
        "mms_enabled": True,
    }
    
    if area_code:
        search_params["area_code"] = area_code
    if zip_code:
        search_params["in_postal_code"] = zip_code

    try:
        logger.info(f"Searching for Twilio numbers with params: {search_params}")
        available_numbers = twilio_client.available_phone_numbers("US").local.list(**search_params, limit=10)
        
        formatted_numbers = [
            AvailableNumber(phone_number=num.phone_number, friendly_name=num.friendly_name)
            for num in available_numbers
        ]
        return NumberSearchResponse(numbers=formatted_numbers)

    except TwilioRestException as e:
        logger.error(f"Twilio API error during number search: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to search for numbers: {e.message}")
    except Exception as e:
        logger.error(f"Unexpected error during number search: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")


@router.post("/assign", response_model=User)
def assign_phone_number(
    payload: AssignNumberPayload,
    current_user: User = Depends(get_current_user_from_token)
):
    """
    Assigns a new Twilio phone number to the user's account.
    In development mode, this simulates the purchase to avoid charges.
    """
    if not twilio_client:
        raise HTTPException(status_code=503, detail="Twilio service is not available.")

    try:
        logger.info(f"Attempting to assign number {payload.phone_number} to user {current_user.id}")
        
        # --- MODIFIED: Added check for development environment ---
        if os.getenv("ENVIRONMENT") == "development":
            logger.warning("DEVELOPMENT MODE: Simulating Twilio number purchase. No real purchase will be made.")
            # Create a mock object that mimics the real Twilio response object.
            # The only attribute we use from it is .phone_number.
            incoming_phone_number = SimpleNamespace(phone_number=payload.phone_number)
        else:
            # This is the original logic that runs in production
            incoming_phone_number = twilio_client.incoming_phone_numbers.create(
                phone_number=payload.phone_number
            )
        
        # The rest of the function proceeds as normal, using the real or mock object
        update_data = UserUpdate(twilio_phone_number=incoming_phone_number.phone_number)
        updated_user = crm_service.update_user(user_id=current_user.id, update_data=update_data)
        
        logger.info(f"Successfully assigned {updated_user.twilio_phone_number} to user {current_user.id}")
        return updated_user

    except TwilioRestException as e:
        logger.error(f"Twilio API error during number assignment: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to assign number: {e.message}")
    except Exception as e:
        logger.error(f"Unexpected error during number assignment: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred during assignment.")
    
@router.post("/incoming-sms", response_class=Response, status_code=200)
async def handle_incoming_sms(request: Request):
    """
    Receives incoming SMS messages from Twilio via webhook.
    Parses the Twilio POST request and triggers message processing.
    """
    logger.info("Received incoming SMS webhook from Twilio.")
    try:
        # Twilio sends data as application/x-www-form-urlencoded
        body = await request.body()
        form_data = parse_qs(body.decode('utf-8'))

        from_number = form_data.get('From', [None])[0]
        to_number = form_data.get('To', [None])[0]
        message_body = form_data.get('Body', [None])[0]

        if not all([from_number, to_number, message_body]):
            logger.error(f"Missing required Twilio parameters. From: {from_number}, To: {to_number}, Body: {message_body}")
            # Return an empty TwiML response even on error, so Twilio doesn't retry endlessly
            return Response(content=str(MessagingResponse()), media_type="application/xml")

        logger.info(f"Incoming SMS from {from_number} to {to_number}: '{message_body}'")

        # Hand off to the core processing logic
        await twilio_incoming.process_incoming_sms(from_number=from_number, body=message_body)

        # Return an empty TwiML response to Twilio to acknowledge receipt
        # This prevents Twilio from retrying the webhook due to an HTTP error.
        return Response(content=str(MessagingResponse()), media_type="application/xml")

    except Exception as e:
        logger.error(f"Error processing incoming Twilio SMS: {e}")
        # Always return a 200 OK with empty TwiML to Twilio to prevent retries
        return Response(content=str(MessagingResponse()), media_type="application/xml")