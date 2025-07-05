# -----------
# File Path: backend/api/main.py
# Purpose: This version is UPDATED to remove the temporary debug endpoint
#          and enable a dark theme for the API documentation.
# ---

from fastapi import FastAPI
from fastapi.routing import APIRoute
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from api.rest import clients, properties, inbox, nudges, admin_triggers, scheduled_messages, users, campaigns, conversations, faqs, auth
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

# --- CHANGE: Added swagger_ui_parameters to enable dark mode ---
# This uses a popular dark theme for Swagger UI from a public CDN.
swagger_ui_parameters = {
    "customCssUrl": "https://cdn.jsdelivr.net/npm/swagger-ui-themes@3.0.1/themes/3.x/theme-material.css"
}

app = FastAPI(
    title="AI Nudge Backend API",
    description="The core API for the AI Nudge intelligent assistant.",
    version="0.1.0",
    lifespan=lifespan,
    swagger_ui_parameters=swagger_ui_parameters  # <-- This enables the dark theme
)

origins = ["http://localhost:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all the API routers
app.include_router(clients.router)
app.include_router(campaigns.router)
app.include_router(properties.router)
app.include_router(inbox.router)
app.include_router(nudges.router)
app.include_router(admin_triggers.router)
app.include_router(scheduled_messages.router)
app.include_router(users.router)
app.include_router(conversations.router)
app.include_router(faqs.router)
app.include_router(auth.router)

@app.get("/")
async def read_root():
    """A simple root endpoint to confirm the API is running."""
    return {"message": "Welcome to AI Nudge Backend API!"}
