# backend/common/config.py
# --- UPDATED: Added LLM_PROVIDER setting.

from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    """
    Manages application settings loaded from the .env file.
    Provides type validation for all settings.
    """
    # --- NEW: Setting to choose the AI provider ---
    LLM_PROVIDER: str = "openai" # Default to 'openai', can be switched to 'gemini'

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

    # Application
    ENVIRONMENT: str = "production"
    FRONTEND_APP_URL: str = "http://localhost:3000"
    SECRET_KEY: str

    # FAQ Auto-Reply
    FAQ_AUTO_REPLY_ENABLED: bool = True

    # MLS Providers
    MLS_PROVIDER: str

    # Demo Spark API Credentials
    SPARK_API_DEMO_TOKEN: str

    # Live RESO API Credentials
    RESO_API_BASE_URL: str
    RESO_API_TOKEN: str

    # Google OAuth for Contact Import
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str

    # Microsoft OAuth
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