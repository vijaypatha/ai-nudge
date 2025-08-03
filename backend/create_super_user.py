# File Path: backend/create_super_user.py

#!/usr/bin/env python3
"""
Script to create an All-Access Standard Account.
This script reads sensitive user details from environment variables for security.
"""
# --- ADD THESE TWO LINES AT THE VERY TOP ---
from dotenv import load_dotenv
load_dotenv()
# -----------------------------------------

import sys
from sqlmodel import Session
from data.database import engine
from data.models.user import User, UserType
from common.config import get_settings

# Load settings, which includes environment variables from .env file
settings = get_settings()

def create_all_access_user():
    """Create a standard user account with access to all verticals."""

    # --- Securely load user details from environment variables ---
    admin_name = settings.ADMIN_FULL_NAME
    admin_email = settings.ADMIN_EMAIL
    admin_phone = settings.ADMIN_PHONE_NUMBER
    admin_twilio_phone = settings.ADMIN_TWILIO_PHONE_NUMBER

    # --- Validate that all required environment variables are set ---
    if not all([admin_name, admin_email, admin_phone, admin_twilio_phone]):
        print("⚠️  Warning: One or more required ADMIN environment variables are not set.")
        print("ADMIN_FULL_NAME, ADMIN_EMAIL, ADMIN_PHONE_NUMBER, and ADMIN_TWILIO_PHONE_NUMBER are required.")
        print("Skipping all-access user creation. Database will be seeded with test users only.")
        return None

    all_access_user_data = {
        "full_name": admin_name,
        "email": admin_email,
        "phone_number": admin_phone,
        "twilio_phone_number": admin_twilio_phone,
        "user_type": UserType.REALTOR,
        "vertical": None,  # This gives access to all verticals
        "super_user": True,  # This marks as super user
        "onboarding_complete": True,
        "timezone": "UTC",
        "faq_auto_responder_enabled": True,
        "strategy": {"nudge_format": "ready-to-send"},
        "onboarding_state": {
            "phone_verified": True,
            "work_style_set": True,
            "contacts_imported": True,
            "first_nudges_seen": True,
            "google_sync_complete": True,
            "mls_connected": True  # Add this for realtors
        }
    }

    with Session(engine) as session:
        existing_user = session.query(User).filter(User.phone_number == admin_phone).first()
        if existing_user:
            print(f"User with phone number {admin_phone} already exists: {existing_user.full_name}")
            return existing_user

        user = User(**all_access_user_data)
        session.add(user)
        session.commit()
        session.refresh(user)

        print("✅ All-Access user created successfully!")
        print(f"   Name: {user.full_name}")
        print(f"   Email: {user.email}")
        print(f"   Phone: {user.phone_number}")
        print("\nYou can now log in with this account to experience all verticals.")

        return user

if __name__ == "__main__":
    print("Creating All-Access Standard Account...")
    try:
        user = create_all_access_user()
        if user:
            print("\n🎉 All-Access account ready!")
        else:
            print("\n⚠️  All-Access account creation skipped (missing environment variables).")
    except Exception as e:
        print(f"⚠️  Warning: An unexpected error occurred during user creation: {e}")
        print("Continuing with deployment...")
        # Don't exit with error code - let deployment continue