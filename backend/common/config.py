# File Path: backend/common/config.py
# PURPOSE: Manages all application settings from the environment.

from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional, List
import os

class Settings(BaseSettings):
    """
    Manages application settings loaded from the environment.
    Provides type validation for all settings.
    """
    LLM_PROVIDER: str = "openai"

    # OpenAI
    OPENAI_API_KEY: str

    # Google AI Settings
    GOOGLE_API_KEY: str
    GOOGLE_CSE_ID: str

    # Twilio
    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str
    TWILIO_PHONE_NUMBER: str
    TWILIO_DEFAULT_MESSAGING_SERVICE_SID: Optional[str] = None
    TWILIO_VERIFY_SERVICE_SID: str

    # Database
    DATABASE_URL: str

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Application
    ENVIRONMENT: str = "production"
    FRONTEND_APP_URL: str = "http://localhost:3000"
    SECRET_KEY: str
    RESCAN_LOOKBACK_DAYS: int = 30
    FAQ_AUTO_REPLY_ENABLED: bool = True
    
    WEBSOCKET_ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]

    # MLS Providers
    MLS_PROVIDER: str
    SPARK_API_DEMO_TOKEN: str
    RESO_API_BASE_URL: str
    RESO_API_TOKEN: str

    # Google OAuth for Contact Import
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str

    # Microsoft OAuth
    MICROSOFT_CLIENT_ID: Optional[str] = None
    MICROSOFT_CLIENT_SECRET: Optional[str] = None
    MICROSOFT_REDIRECT_URI: Optional[str] = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Only validate environment if not in migration mode
        if not self._is_migration_mode():
            self._validate_environment()

    def _is_migration_mode(self) -> bool:
        """Check if we're running in migration mode (Alembic)."""
        # Check if we're running Alembic commands
        import sys
        return (
            'alembic' in sys.argv[0] or 
            any('alembic' in arg for arg in sys.argv) or
            os.getenv('MIGRATION_MODE', 'false').lower() == 'true'
        )

    def _validate_environment(self):
        """Validates that required environment variables are properly set."""
        placeholder_values = [
            "your_openai_api_key_here",
            "your_ope************here",
            "dummy_key",
            "your_google_api_key_here",
            "your_twilio_account_sid_here",
            "your_twilio_auth_token_here",
            "your_secret_key_here"
        ]
        
        missing_keys = []
        placeholder_keys = []
        
        # Check for missing required keys
        required_keys = [
            "OPENAI_API_KEY", "GOOGLE_API_KEY", "GOOGLE_CSE_ID",
            "TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_PHONE_NUMBER",
            "DATABASE_URL", "SECRET_KEY", "MLS_PROVIDER", "SPARK_API_DEMO_TOKEN",
            "RESO_API_BASE_URL", "RESO_API_TOKEN", "GOOGLE_CLIENT_ID",
            "GOOGLE_CLIENT_SECRET", "GOOGLE_REDIRECT_URI"
        ]
        
        for key in required_keys:
            value = getattr(self, key, None)
            if not value:
                missing_keys.append(key)
            elif value in placeholder_values:
                placeholder_keys.append(key)
        
        if missing_keys:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_keys)}. "
                "Please check your .env file and ensure all required variables are set."
            )
        
        if placeholder_keys:
            raise ValueError(
                f"Environment variables contain placeholder values: {', '.join(placeholder_keys)}. "
                "Please replace placeholder values with actual API keys and credentials. "
                "Check your .env file and update with real values."
            )


@lru_cache()
def get_settings():
    """Returns a cached instance of the Settings for performance."""
    return Settings()