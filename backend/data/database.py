# File Path: backend/data/database.py

import os
from sqlmodel import create_engine, SQLModel, Session
from common.config import get_settings

# --- THIS IS THE FIX ---
# The previous individual imports are replaced with this single line.
# This imports all models from the central models package (__init__.py),
# which prevents the "Table is already defined" error.
from .models import (
    User, Client, Resource, ContentResource, Message, ScheduledMessage,
    CampaignBriefing, MarketEvent, PipelineRun, Faq
)
# --- END OF FIX ---


def get_database_settings():
    """Get database-only settings for migrations."""
    os.environ['MIGRATION_MODE'] = 'true'
    return get_settings()

# Use database-only settings for database operations
settings = get_database_settings()
DATABASE_URL = settings.DATABASE_URL
DB_FILE_PATH = "ai_nudge.db"

# Create the SQLAlchemy engine.
engine = create_engine(DATABASE_URL, echo=False)

def create_db_and_tables():
    """
    Initializes the database. It creates all tables based on the registered SQLModels.
    """
    print("DATABASE: Initializing database...")
    print("DATABASE: Creating new tables...")
    SQLModel.metadata.create_all(engine)
    print("DATABASE: Tables created successfully.")

def get_session():
    """Dependency provider for getting a database session."""
    with Session(engine) as session:
        yield session