# backend/common/config.py
# --- DEFINITIVE FIX ---
# Adds the 'ENVIRONMENT' field to the Settings model. This tells Pydantic
# that this environment variable is expected, resolving the ValidationError
# on startup. A safe default of "production" is included.

from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    """
    Manages application settings loaded from the .env file.
    Provides type validation for all settings.
    """
    # OpenAI
    OPENAI_API_KEY: str

    # Google AI Settings
    GOOGLE_API_KEY: str

    # Twilio
    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str
    TWILIO_PHONE_NUMBER: str
    TWILIO_DEFAULT_MESSAGING_SERVICE_SID: Optional[str] = None
    TWILIO_SUPPORT_MESSAGING_SERVICE_SID: Optional[str] = None
    TWILIO_VERIFY_SERVICE_SID: str

    # Database
    DATABASE_URL: str

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # --- ADDED: The missing ENVIRONMENT variable ---
    # Application
    ENVIRONMENT: str = "production" # Defaults to production for safety
    FRONTEND_APP_URL: str = "http://localhost:3000"
    SECRET_KEY: str

    # FAQ Auto-Reply
    FAQ_AUTO_REPLY_ENABLED: bool = True        # Global kill-switch for automatic FAQ replies
    FAQ_SIMILARITY_THRESHOLD: float = 0.70     # Cosine similarity (0–1). Raise to silence, lower to loosen
    FAQ_MAX_AUTO_REPLIES_PER_CLIENT: int = 3   # Daily safety cap per client

    # MLS Providers
    MLS_PROVIDER: str # e.g., "flexmls_spark" or "flexmls_reso"

    # --- Demo Spark API Credentials ---
    SPARK_API_DEMO_TOKEN: str

    # --- Live RESO API Credentials ---
    RESO_API_BASE_URL: str
    RESO_API_TOKEN: str

    # Google OAuth for Contact Import
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str

    # Microsoft OAuth (placeholders for future implementation)
    MICROSOFT_CLIENT_ID: str
    MICROSOFT_CLIENT_SECRET: str
    MICROSOFT_REDIRECT_URI: str


    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

@lru_cache()
def get_settings():
    """Returns a cached instance of the Settings for performance."""
    return Settings()