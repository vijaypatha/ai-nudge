# ---
# File Path: backend/data/database.py
# Purpose: Manages database connection and session creation.
# This version is UPDATED to delete the old database on startup for a clean test environment.
# ---
import os
from sqlmodel import create_engine, SQLModel, Session
from common.config import get_settings

# Correctly import all table models to ensure they are registered with SQLModel metadata.
from .models.user import User
from .models.client import Client
# --- MODIFIED: Replaced the obsolete 'Property' import with our new 'Resource' model. ---
from .models.resource import Resource
# --- MODIFIED: Added 'Message' which is a dependency for CampaignBriefing relationships. ---
from .models.message import Message, ScheduledMessage
from .models.campaign import CampaignBriefing
from .models.event import MarketEvent

settings = get_settings()
DATABASE_URL = settings.DATABASE_URL
# Define the path for the SQLite database file.
DB_FILE_PATH = "ai_nudge.db"

# Create the SQLAlchemy engine.
engine = create_engine(DATABASE_URL, echo=False) # Set echo=False to clean up logs

def create_db_and_tables():
    """
    Initializes the database. It first deletes the old DB file to ensure a clean state,
    then creates all new tables based on the registered SQLModels.
    """
    print("DATABASE: Initializing database...")
    # Delete the database file if it exists to ensure a fresh start
    if os.path.exists(DB_FILE_PATH):
        os.remove(DB_FILE_PATH)
        print(f"DATABASE: Removed old database file '{DB_FILE_PATH}'.")

    # Create all tables
    SQLModel.metadata.create_all(engine)
    print("DATABASE: Tables created successfully.")

def get_session():
    """Dependency provider for getting a database session."""
    with Session(engine) as session:
        yield session