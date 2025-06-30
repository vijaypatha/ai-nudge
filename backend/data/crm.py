# File Path: backend/data/crm.py
# This version is UPDATED to use session.merge() for saving campaigns for better stability.

from typing import Optional, List, Dict, Any
import uuid
from datetime import datetime, timezone
from sqlmodel import Session, select, delete
from .database import engine

from .models.client import Client
from .models.user import User
from .models.property import Property
from .models.campaign import CampaignBriefing, CampaignUpdate
from .models.message import ScheduledMessage

# --- User Functions ---
def get_user_by_id(user_id: uuid.UUID) -> Optional[User]:
    with Session(engine) as session:
        return session.get(User, user_id)

# --- Client Functions ---
def update_last_interaction(client_id: uuid.UUID) -> Optional[Client]:
    with Session(engine) as session:
        client = session.get(Client, client_id)
        if client:
            client.last_interaction = datetime.now(timezone.utc).isoformat()
            session.add(client)
            session.commit()
            session.refresh(client)
            print(f"CRM: Updated last_interaction for client_id: {client_id}")
            return client
        return None

def get_client_by_id(client_id: uuid.UUID) -> Optional[Client]:
    with Session(engine) as session:
        return session.get(Client, client_id)

def get_all_clients() -> List[Client]:
    with Session(engine) as session:
        return session.exec(select(Client)).all()
# ... (other functions like update_client_preferences, update_client_tags are unchanged)
def update_client_preferences(client_id: uuid.UUID, preferences: Dict[str, Any]) -> Optional[Client]:
    with Session(engine) as session:
        client = session.get(Client, client_id)
        if client:
            client.preferences = preferences
            session.add(client)
            session.commit()
            session.refresh(client)
            return client
        return None

def update_client_tags(client_id: uuid.UUID, tags: List[str]) -> Optional[Client]:
    with Session(engine) as session:
        client = session.get(Client, client_id)
        if client:
            client.tags = tags
            session.add(client)
            session.commit()
            session.refresh(client)
            return client
        return None

# --- Property Functions ---
def get_property_by_id(property_id: uuid.UUID) -> Optional[Property]:
    with Session(engine) as session:
        return session.get(Property, property_id)

def get_all_properties() -> List[Property]:
    with Session(engine) as session:
        return session.exec(select(Property)).all()

def update_property_price(property_id: uuid.UUID, new_price: float) -> Optional[Property]:
    with Session(engine) as session:
        prop = session.get(Property, property_id)
        if prop:
            prop.price = new_price
            session.add(prop)
            session.commit()
            session.refresh(prop)
            return prop
        return None
        
# --- Campaign Functions ---
def save_campaign_briefing(briefing: CampaignBriefing):
    """Saves or updates a campaign briefing in the database."""
    with Session(engine) as session:
        # Using merge() is more robust for saving, as it handles both inserts and updates.
        session.merge(briefing)
        session.commit()
        print(f"CRM: Saved campaign briefing -> {briefing.headline}")

def get_new_campaign_briefings_for_user(user_id: uuid.UUID) -> List[CampaignBriefing]:
    with Session(engine) as session:
        statement = select(CampaignBriefing).where(CampaignBriefing.user_id == user_id, CampaignBriefing.status.in_(["new", "insight"]))
        return session.exec(statement).all()

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

def delete_scheduled_messages_for_client(client_id: uuid.UUID):
    with Session(engine) as session:
        statement = delete(ScheduledMessage).where(ScheduledMessage.client_id == client_id)
        session.exec(statement)
        session.commit()