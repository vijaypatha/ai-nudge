# ---
# File Path: backend/data/crm.py
# Purpose: Acts as a centralized data access layer (service layer) for the application.
# All database queries and transactions are handled exclusively by the functions in this file.
# This keeps the business logic in the API endpoints and agents clean and database-agnostic.
# ---

from typing import Optional, List, Dict, Any, Tuple
import uuid
from datetime import datetime, timezone
from sqlmodel import Session, select, delete
from .database import engine
import logging

# --- DEFINITIVE FIX ---
# Corrected the import path to be absolute from the project root (`/app` in Docker).
# This resolves the ModuleNotFoundError.
from agent_core.deduplication.deduplication_engine import find_strong_duplicate

# Import all necessary models
from .models.client import Client, ClientUpdate, ClientCreate
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

def get_client_by_id(client_id: uuid.UUID, user_id: uuid.UUID) -> Optional[Client]:
    """Retrieves a single client by their unique ID, ensuring it belongs to the user."""
    with Session(engine) as session:
        statement = select(Client).where(Client.id == client_id, Client.user_id == user_id)
        return session.exec(statement).first()

def get_client_by_phone(phone_number: str, user_id: uuid.UUID) -> Optional[Client]:
    """Retrieves a single client by their phone number, ensuring it belongs to the user."""
    with Session(engine) as session:
        statement = select(Client).where(Client.phone == phone_number, Client.user_id == user_id)
        return session.exec(statement).first()

def get_all_clients(user_id: uuid.UUID) -> List[Client]:
    """Retrieves all clients from the database for a specific user."""
    with Session(engine) as session:
        statement = select(Client).where(Client.user_id == user_id)
        return session.exec(statement).all()
    
def create_or_update_client(user_id: uuid.UUID, client_data: ClientCreate) -> Tuple[Client, bool]:
    """
    Creates a new client or updates an existing one based on deduplication logic.
    This function orchestrates the check for duplicates and performs a "merge by enrichment" strategy.

    Args:
        user_id: The UUID of the user.
        client_data: The data for the new client to be imported.

    Returns:
        A tuple containing the final Client object and a boolean, where True indicates
        a new client was created and False indicates an existing client was updated.
    """
    with Session(engine) as session:
        logging.info(f"CRM: Processing contact '{client_data.full_name}' for user {user_id}")

        # 1. Find potential duplicates using the deduplication engine
        existing_client = find_strong_duplicate(db=session, user_id=user_id, new_contact=client_data)

        if existing_client:
            # 2. A strong duplicate was found, merge by enrichment
            logging.info(f"CRM: Found duplicate. Merging '{client_data.full_name}' into existing client ID {existing_client.id}")

            is_updated = False

            if not existing_client.email and client_data.email:
                existing_client.email = client_data.email
                is_updated = True

            if not existing_client.phone and client_data.phone:
                existing_client.phone = client_data.phone
                is_updated = True

            if is_updated:
                session.add(existing_client)
                session.commit()
                session.refresh(existing_client)
                logging.info(f"CRM: Successfully enriched client ID {existing_client.id}.")

            return existing_client, False
        else:
            # 3. No duplicate found, create a new client record
            logging.info(f"CRM: No duplicate found. Creating new client '{client_data.full_name}' for user {user_id}.")

            new_client_data = client_data.model_dump()
            new_client = Client(**new_client_data, user_id=user_id)

            session.add(new_client)
            session.commit()
            session.refresh(new_client)
            logging.info(f"CRM: Successfully created new client with ID {new_client.id}")

            return new_client, True

def update_last_interaction(client_id: uuid.UUID, user_id: uuid.UUID) -> Optional[Client]:
    """Updates the last_interaction timestamp for a client to the current time."""
    with Session(engine) as session:
        client = session.exec(select(Client).where(Client.id == client_id, Client.user_id == user_id)).first()
        if client:
            client.last_interaction = datetime.now(timezone.utc).isoformat()
            session.add(client)
            session.commit()
            session.refresh(client)
            print(f"CRM: Updated last_interaction for client_id: {client_id}")
            return client
        return None

def update_client_preferences(client_id: uuid.UUID, preferences: Dict[str, Any], user_id: uuid.UUID) -> Optional[Client]:
    """Overwrites the entire 'preferences' JSON object for a specific client."""
    with Session(engine) as session:
        client = session.exec(select(Client).where(Client.id == client_id, Client.user_id == user_id)).first()
        if client:
            client.preferences = preferences
            session.add(client)
            session.commit()
            session.refresh(client)
            return client
        return None

def update_client_tags(client_id: uuid.UUID, tags: List[str], user_id: uuid.UUID) -> Optional[Client]:
    """Overwrites the entire 'user_tags' list for a specific client."""
    with Session(engine) as session:
        client = session.exec(select(Client).where(Client.id == client_id, Client.user_id == user_id)).first()
        if client:
            client.user_tags = tags
            session.add(client)
            session.commit()
            session.refresh(client)
            return client
        return None


# --- Property Functions (No changes needed, properties are shared data) ---

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
        session.merge(briefing)
        session.commit()
        print(f"CRM: Saved campaign briefing -> {briefing.headline}")

def get_new_campaign_briefings_for_user(user_id: uuid.UUID) -> List[CampaignBriefing]:
    """Retrieves all 'new' or 'insight' campaign briefings for a specific user."""
    with Session(engine) as session:
        statement = select(CampaignBriefing).where(CampaignBriefing.user_id == user_id, CampaignBriefing.status.in_(["new", "insight"]))
        return session.exec(statement).all()

def get_campaign_briefing_by_id(campaign_id: uuid.UUID, user_id: uuid.UUID) -> Optional[CampaignBriefing]:
    """Retrieves a single campaign briefing by its unique ID, ensuring it belongs to the user."""
    with Session(engine) as session:
        statement = select(CampaignBriefing).where(CampaignBriefing.id == campaign_id, CampaignBriefing.user_id == user_id)
        return session.exec(statement).first()

def update_campaign_briefing(campaign_id: uuid.UUID, update_data: CampaignUpdate, user_id: uuid.UUID) -> Optional[CampaignBriefing]:
    """Updates a campaign briefing with new data, ensuring it belongs to the user."""
    with Session(engine) as session:
        briefing = session.exec(select(CampaignBriefing).where(CampaignBriefing.id == campaign_id, CampaignBriefing.user_id == user_id)).first()
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

def get_conversation_history(client_id: uuid.UUID, user_id: uuid.UUID) -> List[Message]:
    """Retrieves all messages for a given client, ensuring it belongs to the user."""
    with Session(engine) as session:
        client_check = session.exec(select(Client.id).where(Client.id == client_id, Client.user_id == user_id)).first()
        if not client_check:
            return []
            
        statement = select(Message).where(Message.client_id == client_id).order_by(Message.created_at)
        return session.exec(statement).all()

def get_conversation_summaries(user_id: uuid.UUID) -> List[Dict[str, Any]]:
    """Generates a list of conversation summaries for a specific user."""
    summaries = []
    with Session(engine) as session:
        clients = session.exec(select(Client).where(Client.user_id == user_id)).all()
        for client in clients:
            last_message_statement = select(Message).where(Message.client_id == client.id).order_by(Message.created_at.desc()).limit(1)
            last_message = session.exec(last_message_statement).first()
            
            summary = {
                "id": f"conv-{client.id}",
                "client_id": client.id,
                "client_name": client.full_name,
                "last_message": last_message.content if last_message else "No messages yet.",
                "last_message_time": last_message.created_at.isoformat() if last_message else datetime.now(timezone.utc).isoformat(),
                "unread_count": 0
            }
            summaries.append(summary)
    
    summaries.sort(key=lambda x: x['last_message_time'], reverse=True)
    return summaries


# --- Scheduled Message Functions ---

def save_scheduled_message(message: ScheduledMessage):
    """Saves a single scheduled message to the database."""
    with Session(engine) as session:
        session.add(message)
        session.commit()
        print(f"CRM: Saved scheduled message for client {message.client_id} at {message.scheduled_at}")

def get_all_scheduled_messages(user_id: uuid.UUID) -> List[ScheduledMessage]:
    """Gets all scheduled messages from the database for a specific user."""
    with Session(engine) as session:
        statement = select(ScheduledMessage).where(ScheduledMessage.user_id == user_id)
        return session.exec(statement).all()

def update_scheduled_message(message_id: uuid.UUID, update_data: Dict[str, Any], user_id: uuid.UUID) -> Optional[ScheduledMessage]:
    """Updates a scheduled message, typically its content or scheduled time."""
    with Session(engine) as session:
        message = session.exec(select(ScheduledMessage).where(ScheduledMessage.id == message_id, ScheduledMessage.user_id == user_id)).first()
        if not message:
            return None
        for key, value in update_data.items():
            if value is not None:
                setattr(message, key, value)
        session.add(message)
        session.commit()
        session.refresh(message)
        return message

def delete_scheduled_message(message_id: uuid.UUID, user_id: uuid.UUID) -> bool:
    """Deletes a single scheduled message by its ID."""
    with Session(engine) as session:
        message = session.exec(select(ScheduledMessage).where(ScheduledMessage.id == message_id, ScheduledMessage.user_id == user_id)).first()
        if not message:
            return False
        session.delete(message)
        session.commit()
        return True

def get_scheduled_messages_for_client(client_id: uuid.UUID, user_id: uuid.UUID) -> List[ScheduledMessage]:
    """Retrieves all scheduled messages for a single client."""
    with Session(engine) as session:
        client_check = session.exec(select(Client.id).where(Client.id == client_id, Client.user_id == user_id)).first()
        if not client_check:
            return []
            
        statement = select(ScheduledMessage).where(ScheduledMessage.client_id == client_id)
        return session.exec(statement).all()

def delete_scheduled_messages_for_client(client_id: uuid.UUID, user_id: uuid.UUID):
    """Deletes all scheduled messages for a single client. Used by the planner."""
    with Session(engine) as session:
        client_check = session.exec(select(Client.id).where(Client.id == client_id, Client.user_id == user_id)).first()
        if not client_check:
            return
            
        statement = delete(ScheduledMessage).where(ScheduledMessage.client_id == client_id)
        session.exec(statement)
        session.commit()

# --- Recurring & Background Task Functions ---

def get_all_sent_recurring_messages() -> List[ScheduledMessage]:
    """
    Retrieves all messages that have been sent and are marked as recurring.
    This function remains global as the background task iterates through all users.
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
    (No user_id needed as client_id is globally unique and this is an internal check)
    """
    with Session(engine) as session:
        statement = select(ScheduledMessage).where(
            ScheduledMessage.client_id == client_id,
            ScheduledMessage.playbook_touchpoint_id == playbook_touchpoint_id,
            ScheduledMessage.status == MessageStatus.PENDING
        )
        result = session.exec(statement).first()
        return result is not None

def get_all_users() -> List[User]:
    """Retrieves all users from the database. For use by system-wide background tasks."""
    with Session(engine) as session:
        return session.exec(select(User)).all()

# --- ADDED: New function for system-level indexing tasks ---
def _get_all_clients_for_system_indexing() -> List[Client]:
    """
    Retrieves ALL clients from the database, across all users.
    USE WITH CAUTION: This is only for system-level processes like building a
    search index at startup. Do NOT use this in user-facing API endpoints.
    """
    with Session(engine) as session:
        statement = select(Client)
        return session.exec(statement).all()
