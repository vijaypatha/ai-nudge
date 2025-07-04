# ---
# File Path: backend/data/crm.py
# Purpose: Acts as a centralized data access layer (service layer) for the application.
# All database queries and transactions are handled exclusively by the functions in this file.
# This keeps the business logic in the API endpoints and agents clean and database-agnostic.
# ---

from typing import Optional, List, Dict, Any
import uuid
from datetime import datetime, timezone
from sqlmodel import Session, select, delete
from .database import engine

# Import all necessary models
from .models.client import Client, ClientUpdate
from .models.user import User, UserUpdate
from .models.property import Property
from .models.campaign import CampaignBriefing, CampaignUpdate
from .models.message import ScheduledMessage, Message, MessageStatus


# --- User Functions ---

def get_user_by_id(user_id: uuid.UUID) -> Optional[User]:
    """Retrieves a single user by their unique ID."""
    with Session(engine) as session:
        return session.get(User, user_id)

def update_user(user_id: uuid.UUID, update_data: UserUpdate) -> Optional[User]:
    """Updates a user's record with the provided data."""
    with Session(engine) as session:
        user = session.get(User, user_id)
        if not user:
            return None
        
        # Safely update the user object with non-None values from the update_data model
        update_dict = update_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(user, key, value)
            
        session.add(user)
        session.commit()
        session.refresh(user)
        return user


# --- Client Functions ---

def get_client_by_id(client_id: uuid.UUID) -> Optional[Client]:
    """Retrieves a single client by their unique ID."""
    with Session(engine) as session:
        return session.get(Client, client_id)

def get_client_by_phone(phone_number: str) -> Optional[Client]:
    """Retrieves a single client by their phone number."""
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
    """Overwrites the entire 'preferences' JSON object for a specific client."""
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
    """Overwrites the entire 'user_tags' list for a specific client."""
    with Session(engine) as session:
        client = session.get(Client, client_id)
        if client:
            client.user_tags = tags
            session.add(client)
            session.commit()
            session.refresh(client)
            return client
        return None


# --- Property Functions ---

def get_property_by_id(property_id: uuid.UUID) -> Optional[Property]:
    """Retrieves a single property by its unique ID."""
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
        
        
# --- Campaign Briefing Functions ---

def save_campaign_briefing(briefing: CampaignBriefing):
    """Saves or updates a single CampaignBriefing in the database."""
    with Session(engine) as session:
        # merge() is used to handle both new and existing records gracefully.
        session.merge(briefing)
        session.commit()
        print(f"CRM: Saved campaign briefing -> {briefing.headline}")

def get_new_campaign_briefings_for_user(user_id: uuid.UUID) -> List[CampaignBriefing]:
    """Retrieves all 'new' or 'insight' campaign briefings for a specific user."""
    with Session(engine) as session:
        statement = select(CampaignBriefing).where(CampaignBriefing.user_id == user_id, CampaignBriefing.status.in_(["new", "insight"]))
        return session.exec(statement).all()

def get_campaign_briefing_by_id(campaign_id: uuid.UUID) -> Optional[CampaignBriefing]:
    """Retrieves a single campaign briefing by its unique ID."""
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


# --- Universal Message Log Functions ---

def save_message(message: Message):
    """Saves a single inbound or outbound message to the universal log."""
    with Session(engine) as session:
        session.add(message)
        session.commit()
        session.refresh(message)
        print(f"CRM: Saved '{message.direction}' message for client_id: {message.client_id}")

def get_conversation_history(client_id: uuid.UUID) -> List[Message]:
    """Retrieves all messages for a given client, ordered by time."""
    with Session(engine) as session:
        statement = select(Message).where(Message.client_id == client_id).order_by(Message.created_at)
        return session.exec(statement).all()

def get_conversation_summaries() -> List[Dict[str, Any]]:
    """Generates a list of conversation summaries for the main dashboard view."""
    summaries = []
    with Session(engine) as session:
        clients = session.exec(select(Client)).all()
        for client in clients:
            # Find the most recent message to display in the summary
            last_message_statement = select(Message).where(Message.client_id == client.id).order_by(Message.created_at.desc()).limit(1)
            last_message = session.exec(last_message_statement).first()
            
            summary = {
                "id": f"conv-{client.id}",
                "client_id": client.id,
                "client_name": client.full_name,
                "last_message": last_message.content if last_message else "No messages yet.",
                "last_message_time": last_message.created_at.isoformat() if last_message else datetime.now(timezone.utc).isoformat(),
                "unread_count": 0 # This is a placeholder for a future feature
            }
            summaries.append(summary)
    
    # Sort summaries so the most recent conversations appear first
    summaries.sort(key=lambda x: x['last_message_time'], reverse=True)
    return summaries


# --- Scheduled Message Functions ---

def save_scheduled_message(message: ScheduledMessage):
    """Saves a single scheduled message to the database."""
    with Session(engine) as session:
        session.add(message)
        session.commit()
        print(f"CRM: Saved scheduled message for client {message.client_id} at {message.scheduled_at}")
        
def get_all_scheduled_messages() -> List[ScheduledMessage]:
    """Gets all scheduled messages from the database across all clients."""
    with Session(engine) as session:
        statement = select(ScheduledMessage)
        return session.exec(statement).all()

def update_scheduled_message(message_id: uuid.UUID, update_data: Dict[str, Any]) -> Optional[ScheduledMessage]:
    """Updates a scheduled message, typically its content or scheduled time."""
    with Session(engine) as session:
        message = session.get(ScheduledMessage, message_id)
        if not message:
            return None
        for key, value in update_data.items():
            if value is not None:
                setattr(message, key, value)
        session.add(message)
        session.commit()
        session.refresh(message)
        return message

def delete_scheduled_message(message_id: uuid.UUID) -> bool:
    """Deletes a single scheduled message by its ID."""
    with Session(engine) as session:
        message = session.get(ScheduledMessage, message_id)
        if not message:
            return False
        session.delete(message)
        session.commit()
        return True

def get_scheduled_messages_for_client(client_id: uuid.UUID) -> List[ScheduledMessage]:
    """Retrieves all scheduled messages for a single client."""
    with Session(engine) as session:
        statement = select(ScheduledMessage).where(ScheduledMessage.client_id == client_id)
        return session.exec(statement).all()

def delete_scheduled_messages_for_client(client_id: uuid.UUID):
    """Deletes all scheduled messages for a single client. Used by the planner."""
    with Session(engine) as session:
        statement = delete(ScheduledMessage).where(ScheduledMessage.client_id == client_id)
        session.exec(statement)
        session.commit()

# --- Recurring & Background Task Functions ---

def get_all_sent_recurring_messages() -> List[ScheduledMessage]:
    """
    Retrieves all messages that have been sent and are marked as recurring.
    Used by the daily Celery task to find campaigns that need rescheduling.
    """
    with Session(engine) as session:
        statement = select(ScheduledMessage).where(
            ScheduledMessage.status == MessageStatus.SENT,
            ScheduledMessage.is_recurring == True
        )
        return session.exec(statement).all()

def has_future_recurring_message(client_id: uuid.UUID, playbook_touchpoint_id: str) -> bool:
    """
    Checks if a recurring message from a specific playbook rule is already
    pending for a client. This prevents the daily task from creating duplicates.
    """
    with Session(engine) as session:
        statement = select(ScheduledMessage).where(
            ScheduledMessage.client_id == client_id,
            ScheduledMessage.playbook_touchpoint_id == playbook_touchpoint_id,
            ScheduledMessage.status == MessageStatus.PENDING
        )
        result = session.exec(statement).first()
        return result is not None