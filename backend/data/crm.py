# File Path: backend/data/crm.py
# --- UPDATED to support the new Message log and finding clients by phone ---

from typing import Optional, List, Dict, Any
import uuid
from datetime import datetime, timezone
from sqlmodel import Session, select, delete
from .database import engine

from .models.client import Client
from .models.user import User
from .models.property import Property
from .models.campaign import CampaignBriefing, CampaignUpdate
from .models.message import ScheduledMessage, Message # <-- Import new Message model

# --- User Functions ---
def get_user_by_id(user_id: uuid.UUID) -> Optional[User]:
    """Retrieves a user by their unique ID."""
    with Session(engine) as session:
        return session.get(User, user_id)
    
# --- NEW: Function to update a user's details ---
def update_user(user_id: uuid.UUID, update_data: User) -> Optional[User]:
    """Updates a user's record in the database."""
    with Session(engine) as session:
        user = session.get(User, user_id)
        if not user:
            return None
        
        # Using model_dump to get a dictionary of the fields to update
        update_dict = update_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(user, key, value)
            
        session.add(user)
        session.commit()
        session.refresh(user)
        return user

# --- Client Functions ---
def get_client_by_id(client_id: uuid.UUID) -> Optional[Client]:
    """Retrieves a client by their unique ID."""
    with Session(engine) as session:
        return session.get(Client, client_id)

def get_client_by_phone(phone_number: str) -> Optional[Client]:
    """Retrieves a client by their phone number."""
    with Session(engine) as session:
        statement = select(Client).where(Client.phone == phone_number)
        return session.exec(statement).first()

def get_all_clients() -> List[Client]:
    """Retrieves all clients from the database."""
    with Session(engine) as session:
        return session.exec(select(Client)).all()

def update_last_interaction(client_id: uuid.UUID) -> Optional[Client]:
    """Updates the last_interaction timestamp for a client to the current time."""
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

def update_client_preferences(client_id: uuid.UUID, preferences: Dict[str, Any]) -> Optional[Client]:
    """Updates the preferences for a specific client."""
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
    """Updates the tags for a specific client."""
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
    """Retrieves a property by its unique ID."""
    with Session(engine) as session:
        return session.get(Property, property_id)

def get_all_properties() -> List[Property]:
    """Retrieves all properties from the database."""
    with Session(engine) as session:
        return session.exec(select(Property)).all()

def update_property_price(property_id: uuid.UUID, new_price: float) -> Optional[Property]:
    """Updates the price for a specific property."""
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
        session.merge(briefing)
        session.commit()
        print(f"CRM: Saved campaign briefing -> {briefing.headline}")

def get_new_campaign_briefings_for_user(user_id: uuid.UUID) -> List[CampaignBriefing]:
    """Retrieves all new or insight-status campaign briefings for a user."""
    with Session(engine) as session:
        statement = select(CampaignBriefing).where(CampaignBriefing.user_id == user_id, CampaignBriefing.status.in_(["new", "insight"]))
        return session.exec(statement).all()

def get_campaign_briefing_by_id(campaign_id: uuid.UUID) -> Optional[CampaignBriefing]:
    """Retrieves a campaign briefing by its unique ID."""
    with Session(engine) as session:
        return session.get(CampaignBriefing, campaign_id)

def update_campaign_briefing(campaign_id: uuid.UUID, update_data: CampaignUpdate) -> Optional[CampaignBriefing]:
    """Updates a campaign briefing with new data."""
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

# --- Message Log Functions ---
def save_message(message: Message):
    """Saves a message to the universal conversation log."""
    with Session(engine) as session:
        session.add(message)
        session.commit()
        session.refresh(message)
        print(f"CRM: Saved '{message.direction}' message for client_id: {message.client_id}")

def get_conversation_history(client_id: uuid.UUID) -> List[Message]:
    """Retrieves all messages for a given client, ordered by creation time."""
    with Session(engine) as session:
        statement = select(Message).where(Message.client_id == client_id).order_by(Message.created_at)
        return session.exec(statement).all()

def get_conversation_summaries() -> List[Dict[str, Any]]:
    """
    Generates a list of conversation summaries for the dashboard.
    """
    summaries = []
    with Session(engine) as session:
        clients = session.exec(select(Client)).all()
        for client in clients:
            # Find the most recent message for this client
            last_message_statement = select(Message).where(Message.client_id == client.id).order_by(Message.created_at.desc()).limit(1)
            last_message = session.exec(last_message_statement).first()
            
            summary = {
                "id": f"conv-{client.id}",
                "client_id": client.id,
                "client_name": client.full_name,
                "last_message": last_message.content if last_message else "No messages yet.",
                "last_message_time": last_message.created_at.isoformat() if last_message else datetime.now(timezone.utc).isoformat(),
                "unread_count": 0 # Placeholder for future feature
            }
            summaries.append(summary)
    
    # Sort summaries so the most recent conversations are first
    summaries.sort(key=lambda x: x['last_message_time'], reverse=True)
    return summaries


# --- Scheduled Message Functions ---
def get_scheduled_messages_for_client(client_id: uuid.UUID) -> List[ScheduledMessage]:
    """Retrieves all scheduled messages for a client."""
    with Session(engine) as session:
        statement = select(ScheduledMessage).where(ScheduledMessage.client_id == client_id)
        return session.exec(statement).all()

def delete_scheduled_messages_for_client(client_id: uuid.UUID):
    """Deletes all scheduled messages for a client."""
    with Session(engine) as session:
        statement = delete(ScheduledMessage).where(ScheduledMessage.client_id == client_id)
        session.exec(statement)
        session.commit()
