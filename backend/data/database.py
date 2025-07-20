# File Path: backend/data/database.py
# --- DEFINITIVE FIX: Corrects the case of the 'Faq' import to match the class name.

import os
from sqlmodel import create_engine, SQLModel, Session
from common.config import get_settings

# Correctly import all table models to ensure they are registered with SQLModel metadata.
from .models.user import User
from .models.client import Client
from .models.resource import Resource, ContentResource
from .models.message import Message, ScheduledMessage
from .models.campaign import CampaignBriefing
from .models.event import MarketEvent
# --- MODIFIED: Changed 'FAQ' to 'Faq' to match the actual class name in faq.py ---
from .models.faq import Faq

settings = get_settings()
DATABASE_URL = settings.DATABASE_URL
# Define the path for the SQLite database file (used if switching from postgres).
DB_FILE_PATH = "ai_nudge.db"

# Create the SQLAlchemy engine.
engine = create_engine(DATABASE_URL, echo=False)

def create_db_and_tables():
    """
    Initializes the database. It first DROPS ALL existing tables to ensure a
    perfectly clean state, then creates all new tables based on the registered SQLModels.
    """
    print("DATABASE: Initializing database...")
    
    print("DATABASE: Dropping all existing tables...")
    SQLModel.metadata.drop_all(engine)
    print("DATABASE: Tables dropped successfully.")

    print("DATABASE: Creating new tables...")
    SQLModel.metadata.create_all(engine)
    print("DATABASE: Tables created successfully.")

def get_session():
    """Dependency provider for getting a database session."""
    with Session(engine) as session:
        yield session