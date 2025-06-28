# ---
# File Path: backend/api/main.py
# Purpose: The main entry point for the FastAPI application.
# This version is UPDATED to initialize the real database on startup.
# ---

from fastapi import FastAPI
from fastapi.routing import APIRoute
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from api.rest import clients, properties, inbox, nudges, admin_triggers, scheduled_messages, users, campaigns
# Import the functions to create and seed the database
from data.database import create_db_and_tables
from data.seed import seed_database

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles application startup events.
    - On startup: It creates the database and tables, then seeds it with data.
    """
    print("--- Application Startup ---")
    create_db_and_tables()
    seed_database()
    print("--- Startup Complete ---")
    yield
    print("--- Application Shutdown ---")

# Initialize the FastAPI application
app = FastAPI(
    title="AI Nudge Backend API",
    description="The core API for the AI Nudge intelligent assistant.",
    version="0.1.0",
    lifespan=lifespan)

# Define allowed origins for Cross-Origin Resource Sharing (CORS)
origins = ["http://localhost:3000"]

# Add CORS middleware to the application
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

@app.get("/")
async def read_root():
    """A simple root endpoint to confirm the API is running."""
    return {"message": "Welcome to AI Nudge Backend API!"}