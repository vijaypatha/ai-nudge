# -----------
# File Path: backend/api/main.py
# Purpose: This is the main entry point for the FastAPI application.
# It now uses a central API router for cleaner, more scalable route management.
# ---

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# --- MODIFIED: Import the central router instead of all individual routers ---
from api.rest.router import api_router
from common.config import get_settings
settings = get_settings()
from data.database import create_db_and_tables
from data.seed import seed_database
from agent_core import audience_builder

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles application startup events.
    """
    print("--- Application Startup ---")
    create_db_and_tables()
    await seed_database()
    await audience_builder.initialize_client_index()
    print("--- Startup Complete ---")
    yield
    print("--- Application Shutdown ---")

swagger_ui_parameters = {
    "customCssUrl": "https://cdn.jsdelivr.net/npm/swagger-ui-themes@3.0.1/themes/3.x/theme-material.css"
}

app = FastAPI(
    title="AI Nudge Backend API",
    description="The core API for the AI Nudge intelligent assistant.",
    version="0.1.0",
    lifespan=lifespan,
    swagger_ui_parameters=swagger_ui_parameters
)

origins = settings.WEBSOCKET_ALLOWED_ORIGINS

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- MODIFIED: Include the single central router with the /api prefix ---
# This one line replaces the 10+ lines that were here before.
app.include_router(api_router, prefix="/api")


@app.get("/")
async def read_root():
    """A simple root endpoint to confirm the API is running."""
    return {"message": "Welcome to AI Nudge Backend API!"}