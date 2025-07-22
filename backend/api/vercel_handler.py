# -----------
# File Path: backend/api/vercel_handler.py
# Purpose: Vercel-specific handler for FastAPI application
# This file is used by Vercel to handle serverless function requests
# ---

from mangum import Mangum
from api.main import app

# Create a handler for Vercel
handler = Mangum(app, lifespan="off") 