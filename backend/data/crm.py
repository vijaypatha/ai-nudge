# File Path: backend/data/crm.py
# Purpose: Acts as a data access layer (DAL) for the application.
# This version is REWRITTEN to use SQLModel and a SQLite database instead of in-memory lists.

from typing import Optional, List, Dict, Any
import uuid
from sqlmodel import Session, select, delete
from .database import engine # Import the shared engine

# Import all data models
from .models.client import Client, ClientUpdate, ClientTagUpdate
from .models.user import User
from .models.property import Property
from .models.campaign import CampaignBriefing, MatchedClient, CampaignUpdate
from .models.message import ScheduledMessage, ScheduledMessageUpdate

# --- User Functions ---
def get_user_by_id(user_id: uuid.UUID) -> Optional[User]:
    with Session(engine) as session:
        return session.get(User, user_id)

def get_all_users() -> List[User]:
    """Get all users from the database."""
    with Session(engine) as session:
        return session.exec(select(User)).all()

# --- Client Functions ---
def get_client_by_id(client_id: uuid.UUID) -> Optional[Client]:
    with Session(engine) as session:
        return session.get(Client, client_id)

def get_all_clients() -> List[Client]:
    with Session(engine) as session:
        return session.exec(select(Client)).all()

def get_all_clients_mock() -> List[Client]:
    """Legacy function name for backward compatibility."""
    return get_all_clients()

def update_client_preferences(client_id: uuid.UUID, preferences: Dict[str, Any]) -> Optional[Client]:
    with Session(engine) as session:
        client = session.get(Client, client_id)
        if client:
            client.preferences = preferences
            session.add(client)
            session.commit()
            session.refresh(client)
        return client

def update_client_tags(client_id: uuid.UUID, tags: List[str]) -> Optional[Client]:
    with Session(engine) as session:
        client = session.get(Client, client_id)
        if client:
            client.tags = tags
            session.add(client)
            session.commit()
            session.refresh(client)
        return client

# --- Property Functions ---
def get_property_by_id(property_id: uuid.UUID) -> Optional[Property]:
    with Session(engine) as session:
        return session.get(Property, property_id)

def get_all_properties() -> List[Property]:
    with Session(engine) as session:
        return session.exec(select(Property)).all()

def get_all_properties_mock() -> List[Property]:
    """Legacy function name for backward compatibility."""
    return get_all_properties()

def update_property_price(property_id: uuid.UUID, new_price: float) -> Optional[Property]:
    with Session(engine) as session:
        prop = session.get(Property, property_id)
        if prop:
            prop.price = new_price
            session.add(prop)
            session.commit()
            session.refresh(prop)
        return prop

# --- Campaign Functions ---
def get_new_campaign_briefings_for_user(user_id: uuid.UUID) -> List[CampaignBriefing]:
    with Session(engine) as session:
        statement = select(CampaignBriefing).where(
            CampaignBriefing.user_id == user_id, 
            CampaignBriefing.status.in_(["new", "insight"])
        )
        return session.exec(statement).all()

def get_all_campaigns() -> List[CampaignBriefing]:
    """Get all campaigns from the database."""
    with Session(engine) as session:
        return session.exec(select(CampaignBriefing)).all()

def get_campaign_briefing_by_id(campaign_id: uuid.UUID) -> Optional[CampaignBriefing]:
    with Session(engine) as session:
        return session.get(CampaignBriefing, campaign_id)

def update_campaign_briefing(campaign_id: uuid.UUID, update_data: CampaignUpdate) -> Optional[CampaignBriefing]:
    with Session(engine) as session:
        briefing = session.get(CampaignBriefing, campaign_id)
        if not briefing:
            return None
        
        update_dict = update_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(briefing, key, value)
        
        session.add(briefing)
        session.commit()
        session.refresh(briefing)
        return briefing

# --- Scheduled Message Functions ---
def get_scheduled_messages_for_client(client_id: uuid.UUID) -> List[ScheduledMessage]:
    with Session(engine) as session:
        statement = select(ScheduledMessage).where(ScheduledMessage.client_id == client_id)
        return session.exec(statement).all()

def get_all_scheduled_messages() -> List[ScheduledMessage]:
    """Get all scheduled messages from the database."""
    with Session(engine) as session:
        return session.exec(select(ScheduledMessage)).all()

def update_scheduled_message(message_id: uuid.UUID, update_data: dict) -> Optional[ScheduledMessage]:
    with Session(engine) as session:
        message = session.get(ScheduledMessage, message_id)
        if message:
            for key, value in update_data.items():
                setattr(message, key, value)
            session.add(message)
            session.commit()
            session.refresh(message)
        return message

def delete_scheduled_messages_for_client(client_id: uuid.UUID):
    with Session(engine) as session:
        statement = delete(ScheduledMessage).where(ScheduledMessage.client_id == client_id)
        session.exec(statement)
        session.commit()

# --- Legacy Compatibility Functions ---
# These functions maintain backward compatibility with old API endpoints

# Mock database references for legacy compatibility
mock_users_db = []  # Empty list to prevent AttributeError
mock_clients_db = []  # Empty list to prevent AttributeError
mock_properties_db = []  # Empty list to prevent AttributeError

def get_mock_users_db() -> List[User]:
    """Legacy compatibility function."""
    return get_all_users()

def get_mock_clients_db() -> List[Client]:
    """Legacy compatibility function."""
    return get_all_clients()

def get_mock_properties_db() -> List[Property]:
    """Legacy compatibility function."""
    return get_all_properties()

def delete_scheduled_message(message_id: uuid.UUID) -> bool:
    """Delete a scheduled message by ID."""
    with Session(engine) as session:
        message = session.get(ScheduledMessage, message_id)
        if message:
            session.delete(message)
            session.commit()
            return True
        return False
