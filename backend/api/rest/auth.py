# backend/api/rest/auth.py
import os
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from uuid import UUID
import datetime

from data import crm as crm_service
from integrations import twilio
from api.security import settings # Assuming settings are in security for now

router = APIRouter(prefix="/auth", tags=["Authentication"])

# --- Helper to create JWT ---
def _create_access_token(data: dict, expires_delta: Optional[datetime.timedelta] = None):
    from jose import jwt
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.now(datetime.timezone.utc) + expires_delta
    else:
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
        user = crm_service.get_client_by_phone(payload.phone_number)
        if not user:
            # A more robust implementation would separate user creation,
            # but for now, we create a shell user on first login.
            new_user = crm_service.User(phone_number=payload.phone_number, full_name="New User") # Placeholder name
            session.add(new_user)
            session.commit()
            session.refresh(new_user)
            user = new_user

    access_token_expires = datetime.timedelta(days=30)
    access_token = _create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


# --- Developer-Only Login Endpoint ---

# This endpoint will only be included if the app is NOT in production.
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