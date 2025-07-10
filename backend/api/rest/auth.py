# File Path: backend/api/rest/auth.py
# DEFINITIVE FIX: Updates user's onboarding_state after a successful Google import.

import os
import datetime
import logging
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from sqlmodel import Session, select

from data import crm as crm_service
from integrations import twilio_otp as twilio
from api.security import settings, get_current_user_from_token
from data.models.user import User, UserUpdate # Import UserUpdate
from data.models.client import ClientCreate
from integrations.oauth.google import GoogleContacts


# --- Logger ---
logger = logging.getLogger(__name__)

# --- Router Setup ---
router = APIRouter(prefix="/auth", tags=["Authentication"])


# --- Helper to create JWT ---
def _create_access_token(data: dict, expires_delta: Optional[datetime.timedelta] = None):
    from jose import jwt
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.now(datetime.timezone.utc) + expires_delta
    else:
        # Default expiration
        expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


# --- Pydantic Models ---
class PhonePayload(BaseModel):
    phone_number: str

class OtpPayload(BaseModel):
    phone_number: str
    otp_code: str

class DevLoginPayload(BaseModel):
    user_id: UUID

class AuthURLResponse(BaseModel):
    auth_url: str

class GoogleCallbackRequest(BaseModel):
    code: str

class ImportSummaryResponse(BaseModel):
    imported_count: int
    merged_count: int


# --- Regular OTP Endpoints ---

@router.post("/otp/send")
async def send_otp(payload: PhonePayload):
    """Sends an OTP to the user's phone number via Twilio Verify."""
    success = twilio.send_verification_token(payload.phone_number)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to send OTP.")
    return {"message": "OTP sent successfully."}

@router.post("/otp/verify")
async def verify_otp(payload: OtpPayload):
    """Verifies the OTP and returns a JWT on success."""
    is_valid = twilio.check_verification_token(payload.phone_number, payload.otp_code)
    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid OTP code.")

    with Session(crm_service.engine) as session:
        statement = select(User).where(User.phone_number == payload.phone_number)
        user = session.exec(statement).first()

        if not user:
            # When creating a new user, explicitly set onboarding_complete to False.
            user = User(
                phone_number=payload.phone_number,
                full_name="New User",
                onboarding_complete=False 
            )
            session.add(user)
            session.commit()
            session.refresh(user)

    access_token_expires = datetime.timedelta(days=30)
    access_token = _create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


# --- Google OAuth Endpoints ---

@router.get("/google-oauth-url", response_model=AuthURLResponse)
async def get_google_oauth_url(request: Request):
    """
    Generates the Google OAuth URL, including the 'state' parameter
    to maintain the user's session across the redirect.
    """
    state = request.query_params.get("state")
    google_contacts = GoogleContacts()
    auth_url = google_contacts.get_auth_url(state=state)
    return {"auth_url": auth_url}

@router.post("/google-callback", response_model=ImportSummaryResponse)
async def google_callback(
    request: GoogleCallbackRequest,
    current_user: User = Depends(get_current_user_from_token),
):
    """
    Handles the OAuth callback from Google, imports contacts,
    and updates the user's onboarding progress.
    """
    google_contacts = GoogleContacts()

    try:
        credentials = google_contacts.exchange_code_for_credentials(request.code)
    except Exception as e:
        logger.error(f"Failed to exchange code for credentials for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to exchange code for credentials: {e}"
        )

    contacts: List[ClientCreate] = google_contacts.fetch_contacts(credentials)
    if not contacts:
        return ImportSummaryResponse(imported_count=0, merged_count=0)

    imported_count = 0
    merged_count = 0
    for contact_data in contacts:
        try:
            _, is_new = crm_service.create_or_update_client(
                user_id=current_user.id, client_data=contact_data
            )
            if is_new:
                imported_count += 1
            else:
                merged_count += 1
        except Exception as e:
            logger.error(f"Failed to process contact {contact_data.full_name} for user {current_user.id}: {e}")

    # --- ADDED: Update onboarding state after import ---
    try:
        logger.info(f"Updating onboarding state for user {current_user.id} after contact import.")
        # Ensure we have the latest state object to avoid overwriting other keys
        updated_state = current_user.onboarding_state.copy()
        updated_state['contacts_imported'] = True
        
        # Create an update model and save it via the CRM service
        update_data = UserUpdate(onboarding_state=updated_state)
        crm_service.update_user(user_id=current_user.id, update_data=update_data)
        logger.info(f"Successfully updated onboarding state for user {current_user.id}.")
    except Exception as e:
        # Log an error but don't fail the entire request, as the import itself succeeded.
        logger.error(f"Could not update onboarding_state for user {current_user.id}: {e}")
    # --- END OF ADDED CODE ---

    return ImportSummaryResponse(imported_count=imported_count, merged_count=merged_count)


# --- Developer-Only Login Endpoint ---

if os.getenv("ENVIRONMENT") == "development":
    @router.post("/dev-login")
    async def developer_login(payload: DevLoginPayload):
        """
        [DEV ONLY] Bypasses OTP for a given user_id and returns a JWT.
        """
        user = crm_service.get_user_by_id(payload.user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Demo user not found.")

        access_token_expires = datetime.timedelta(days=1)
        access_token = _create_access_token(
            data={"sub": str(user.id)}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}