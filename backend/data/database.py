# FILE: backend/data/database.py

import os
from sqlmodel import create_engine, SQLModel, Session
from common.config import get_settings

# This single, clean import statement uses the __init__.py file as the single
# source of truth for all models. This is the fix that prevents the
# "Table is already defined" error.
from .models import (
    User, Client, Resource, ContentResource, Message, ScheduledMessage,
    CampaignBriefing, MarketEvent, PipelineRun, Faq, NegativePreference
)

def get_database_settings():
    """Get database-only settings for migrations."""
    os.environ['MIGRATION_MODE'] = 'true'
    return get_settings()

settings = get_database_settings()
DATABASE_URL = settings.DATABASE_URL
engine = create_engine(DATABASE_URL, echo=False)

def create_db_and_tables():
    """Initializes the database by creating all tables."""
    SQLModel.metadata.create_all(engine)

def get_session():
    """Dependency provider for getting a database session."""
    with Session(engine) as session:
        yield session