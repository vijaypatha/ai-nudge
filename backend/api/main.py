# ---
# File Path: backend/api/main.py
# Purpose: This version is UPDATED to initialize the Audience Builder search index on startup.
# ---

from fastapi import FastAPI
from fastapi.routing import APIRoute
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from api.rest import clients, properties, inbox, nudges, admin_triggers, scheduled_messages, users, campaigns
from data.database import create_db_and_tables
from data.seed import seed_database
from agent_core import audience_builder # Import the audience builder

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles application startup events.
    """
    print("--- Application Startup ---")
    create_db_and_tables()
    await seed_database()
    # NEW: Initialize the semantic search index once on startup.
    await audience_builder.initialize_client_index()
    print("--- Startup Complete ---")
    yield
    print("--- Application Shutdown ---")

app = FastAPI(
    title="AI Nudge Backend API",
    description="The core API for the AI Nudge intelligent assistant.",
    version="0.1.0",
    lifespan=lifespan)

origins = ["http://localhost:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],)

# Include all the API routers
app.include_router(clients.router)
app.include_router(campaigns.router)
app.include_router(properties.router)
app.include_router(inbox.router)
app.include_router(nudges.router)
app.include_router(admin_triggers.router)
app.include_router(scheduled_messages.router)
app.include_router(users.router)

# --- Add this temporary endpoint for testing ---
from agent_core.brain import nudge_engine
import asyncio

@app.post("/_debug/trigger-recency-nudge", tags=["Debug"])
async def trigger_recency_nudge_endpoint():
    """
    A temporary debugging endpoint to manually trigger the recency nudge generation.
    """
    print("DEBUG ENDPOINT: Manually triggering recency nudge generation...")
    try:
        # We must run the async function from our synchronous endpoint
        await nudge_engine.generate_recency_nudges()
        return {"message": "Recency nudge generation triggered successfully."}
    except Exception as e:
        print(f"DEBUG ENDPOINT ERROR: {e}")
        return {"message": f"An error occurred: {e}"}
# --- End of temporary endpoint code ---

@app.get("/")
async def read_root():
    """A simple root endpoint to confirm the API is running."""
    return {"message": "Welcome to AI Nudge Backend API!"}