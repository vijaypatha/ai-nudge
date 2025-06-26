# ---
# File Path: backend/common/config.py
# Purpose: Loads and manages all environment variables for the application using Pydantic.
# ---
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

    # Twilio
    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str
    TWILIO_PHONE_NUMBER: str
    TWILIO_DEFAULT_MESSAGING_SERVICE_SID: str
    # CORRECTED: Made this field optional as it's not in your .env
    TWILIO_SUPPORT_MESSAGING_SERVICE_SID: Optional[str] = None

    # Database
    DATABASE_URL: str

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Application
    FRONTEND_APP_URL: str = "http://localhost:3000"
    SECRET_KEY: str

    # CORRECTED: Added missing MLS fields from your .env
    MLS_PROVIDER: str
    SPARK_API_DEMO_TOKEN: str

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

@lru_cache()
def get_settings():
    """Returns a cached instance of the Settings for performance."""
    return Settings()