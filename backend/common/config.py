# backend/common/config.py

from dotenv import load_dotenv # To load .env file
import os # To access environment variables

# --- Load Environment Variables ---
# This must be called at the very beginning to load variables from .env into os.environ.
load_dotenv()

# --- Configuration Settings ---
# Access environment variables using os.getenv().
# Provide empty strings as defaults if a variable might be optional or for robust startup.

# OpenAI API Key (for AI brain power)
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

# Twilio Credentials (for SMS sending)
TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_PHONE_NUMBER: str = os.getenv("TWILIO_PHONE_NUMBER", "")
TWILIO_DEFAULT_MESSAGING_SERVICE_SID: str = os.getenv("TWILIO_DEFAULT_MESSAGING_SERVICE_SID", "")
TWILIO_SUPPORT_MESSAGING_SERVICE_SID: str = os.getenv("TWILIO_SUPPORT_MESSAGING_SERVICE_SID", "")

# Database URL (for persistent data storage)
DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./test.db") # Default to sqlite for local dev if not set

# Redis URL (for caching, task queues, etc.)
REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Frontend Application URL (useful for CORS or redirects)
FRONTEND_APP_URL: str = os.getenv("FRONTEND_APP_URL", "http://localhost:3000")

# Secret Key (for security purposes like JWTs or session management)
SECRET_KEY: str = os.getenv("SECRET_KEY", "supersecretdefaultkeythatshouldbechangedinprod")

# --- Basic Validation / Warnings ---
# Print warnings if crucial environment variables are missing.
if not OPENAI_API_KEY:
    print("WARNING: OpenAI API Key not loaded. AI functionality will be limited.")
if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER]):
    print("WARNING: Twilio credentials not fully loaded. Messaging functionality may be limited.")
if not DATABASE_URL:
    print("WARNING: DATABASE_URL not set. Using default SQLite database.")
if not REDIS_URL:
    print("WARNING: REDIS_URL not set. Using default local Redis.")
if not SECRET_KEY:
    print("WARNING: SECRET_KEY not set. Using a default secret key (INSECURE FOR PRODUCTION).")