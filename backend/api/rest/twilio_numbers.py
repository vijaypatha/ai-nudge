# File Path: backend/api/rest/twilio_numbers.py
# Purpose: Provides API endpoints for searching and assigning Twilio phone numbers.

import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

from common.config import get_settings
from data.models.user import User, UserUpdate
from api.security import get_current_user_from_token
from data import crm as crm_service

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
        "voice_enabled": False, # Assuming we only need SMS/MMS
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
    """
    if not twilio_client:
        raise HTTPException(status_code=503, detail="Twilio service is not available.")

    try:
        logger.info(f"Assigning number {payload.phone_number} to user {current_user.id}")
        
        # This step "purchases" the number and adds it to your Twilio account.
        incoming_phone_number = twilio_client.incoming_phone_numbers.create(
            phone_number=payload.phone_number
        )
        
        # Update the user's profile with their new Twilio number.
        # NOTE: This assumes you have a 'twilio_phone_number' field on your User model.
        # If not, you must add it to backend/data/models/user.py
        update_data = UserUpdate(twilio_phone_number=incoming_phone_number.phone_number)
        updated_user = crm_service.update_user(user_id=current_user.id, user_data=update_data)
        
        logger.info(f"Successfully assigned {updated_user.twilio_phone_number} to user {current_user.id}")
        return updated_user

    except TwilioRestException as e:
        logger.error(f"Twilio API error during number assignment: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to assign number: {e.message}")
    except Exception as e:
        logger.error(f"Unexpected error during number assignment: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred during assignment.")

