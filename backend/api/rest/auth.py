# File Path: backend/api/rest/auth.py

import os
import datetime
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session

# --- DEFINITIVE FIX ---
# Corrected all import paths to be absolute from the project root (`/app` in Docker).
# Corrected the function name import from 'get_current_user' to 'get_current_user_from_token'.
from data import crm as crm_service
from integrations import twilio
from api.security import settings, get_current_user_from_token
from data.models.user import User
from data.models.client import ClientCreate
from integrations.oauth.google import GoogleContacts


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

# --- New Models for OAuth ---
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

    # Find or create user
    with crm_service.Session(crm_service.engine) as session:
        # --- NOTE on potential logic issue ---
        # The current implementation uses `get_client_by_phone` to find a user.
        # This assumes a User and a Client are interchangeable for login, which might not be correct.
        # A more robust solution would be to implement and use a `get_user_by_phone` function
        # from the crm_service to ensure we are searching for a User, not a Client.
        # For now, leaving the logic as-is to fix the startup crash.
        user = crm_service.get_client_by_phone(payload.phone_number, user_id=None)
        if not user:
            # Creating a shell user on first login.
            new_user = User(phone_number=payload.phone_number, full_name="New User")
            session.add(new_user)
            session.commit()
            session.refresh(new_user)
            user = new_user

    access_token_expires = datetime.timedelta(days=30)
    access_token = _create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


# --- Google OAuth Endpoints ---

@router.get("/google-oauth-url", response_model=AuthURLResponse)
async def get_google_oauth_url():
    """
    Generates and returns the Google OAuth authorization URL for the user to visit.
    """
    google_contacts = GoogleContacts()
    auth_url = google_contacts.get_auth_url()
    return {"auth_url": auth_url}

@router.post("/google-callback", response_model=ImportSummaryResponse)
async def google_callback(
    request: GoogleCallbackRequest,
    # --- DEFINITIVE FIX ---
    # Corrected the dependency to use the correctly named function.
    current_user: User = Depends(get_current_user_from_token),
):
    """
    Handles the OAuth callback from Google after user consent.
    It exchanges the code for tokens, fetches contacts, and imports them
    using the deduplication logic in the CRM service.
    """
    google_contacts = GoogleContacts()

    # 1. Exchange authorization code for credentials
    try:
        credentials = google_contacts.exchange_code_for_credentials(request.code)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to exchange code for credentials: {e}"
        )

    # TODO: Securely store credentials.refresh_token mapped to current_user.id

    # 2. Fetch contacts from Google People API
    contacts: List[ClientCreate] = google_contacts.fetch_contacts(credentials)
    if not contacts:
        return ImportSummaryResponse(imported_count=0, merged_count=0)

    # 3. Orchestrate processing via CRM service
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
            print(f"Failed to process contact {contact_data.full_name}: {e}")

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
