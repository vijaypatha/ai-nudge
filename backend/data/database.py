# ---
# File Path: backend/data/database.py
# Purpose: Manages database connection and creates tables based on SQLModels.
# ---
from sqlmodel import create_engine, SQLModel, Session
from common.config import get_settings

# CORRECTED: Explicitly import all Table models to ensure they are registered.
# This avoids the circular dependency issue from the previous __init__.py.
from data.models.user import User
from data.models.client import Client
from data.models.property import Property
from data.models.message import ScheduledMessage
from data.models.campaign import CampaignBriefing
from data.models.event import MarketEvent


settings = get_settings()
DATABASE_URL = settings.DATABASE_URL

engine = create_engine(DATABASE_URL, echo=True)

def create_db_and_tables():
    print("DATABASE: Initializing database and creating tables...")
    SQLModel.metadata.create_all(engine)
    print("DATABASE: Tables created successfully.")

def get_session():
    with Session(engine) as session:
        yield session