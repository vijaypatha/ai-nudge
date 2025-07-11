# backend/data/crm.py
# --- MODIFIED: Added functions to manage the Recommendation Slate lifecycle.

from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timezone
import uuid
from sqlmodel import Session, select, delete
from sqlalchemy.orm import selectinload
from .database import engine
import logging

from agent_core.deduplication.deduplication_engine import find_strong_duplicate

from .models.client import Client, ClientUpdate, ClientCreate
from .models.user import User, UserUpdate
from .models.resource import Resource, ResourceCreate, ResourceUpdate
from .models.campaign import CampaignBriefing, CampaignUpdate
from .models.message import ScheduledMessage, Message, MessageStatus, MessageDirection



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
    """
    with Session(engine) as session:
        logging.info(f"CRM: Processing contact '{client_data.full_name}' for user {user_id}")

        existing_client = find_strong_duplicate(db=session, user_id=user_id, new_contact=client_data)

        if existing_client:
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
            logging.info(f"CRM: No duplicate found. Creating new client '{client_data.full_name}' for user {user_id}.")
            new_client_data = client_data.model_dump()
            new_client = Client(**new_client_data, user_id=user_id)
            session.add(new_client)
            session.commit()
            session.refresh(new_client)
            logging.info(f"CRM: Successfully created new client with ID {new_client.id}")
            return new_client, True

def update_last_interaction(client_id: uuid.UUID, user_id: uuid.UUID, session: Optional[Session] = None) -> Optional[Client]:
    """
    Updates the last_interaction timestamp for a client to the current time.
    Can operate within a provided session or create its own.
    """
    def _update(db_session: Session):
        client = db_session.exec(select(Client).where(Client.id == client_id, Client.user_id == user_id)).first()
        if client:
            client.last_interaction = datetime.now(timezone.utc).isoformat()
            db_session.add(client)
            logging.info(f"CRM: Queued last_interaction update for client_id: {client_id}")
        return client

    if session:
        return _update(session)
    else:
        with Session(engine) as new_session:
            client = _update(new_session)
            if client:
                new_session.commit()
                new_session.refresh(client)
            return client

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
    
def add_client_tags(client_id: uuid.UUID, tags_to_add: List[str], user_id: uuid.UUID) -> Optional[Client]:
    """
    Appends new tags to a client's user_tags list, ensuring no duplicates.
    """
    with Session(engine) as session:
        client = session.exec(select(Client).where(Client.id == client_id, Client.user_id == user_id)).first()
        
        if client:
            existing_tags = set(client.user_tags)
            new_tags = set(tags_to_add)
            updated_tags = sorted(list(existing_tags.union(new_tags)))
            
            client.user_tags = updated_tags
            session.add(client)
            session.commit()
            session.refresh(client)
            logging.info(f"CRM: Added tags {tags_to_add} to client {client_id}. New tags: {updated_tags}")
            return client
            
        return None


# --- Resource Functions ---

def get_resource_by_id(resource_id: uuid.UUID, user_id: uuid.UUID) -> Optional[Resource]:
    """Retrieves a single resource by its unique ID, ensuring it belongs to the user."""
    with Session(engine) as session:
        statement = select(Resource).where(Resource.id == resource_id, Resource.user_id == user_id)
        return session.exec(statement).first()

def get_all_resources_for_user(user_id: uuid.UUID) -> List[Resource]:
    """Retrieves all resources from the database for a specific user."""
    with Session(engine) as session:
        statement = select(Resource).where(Resource.user_id == user_id)
        return session.exec(statement).all()

def create_resource(user_id: uuid.UUID, resource_data: ResourceCreate) -> Resource:
    """Creates a new resource for a user."""
    with Session(engine) as session:
        new_resource = Resource.model_validate(resource_data, update={"user_id": user_id})
        session.add(new_resource)
        session.commit()
        session.refresh(new_resource)
        return new_resource

def update_resource(resource_id: uuid.UUID, update_data: ResourceUpdate, user_id: uuid.UUID) -> Optional[Resource]:
    """Updates a resource's status or attributes."""
    with Session(engine) as session:
        resource = session.exec(select(Resource).where(Resource.id == resource_id, Resource.user_id == user_id)).first()
        if not resource:
            return None
        
        update_dict = update_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(resource, key, value)
            
        session.add(resource)
        session.commit()
        session.refresh(resource)
        return resource
        
        
# --- Campaign Briefing & Recommendation Slate Functions ---

def save_campaign_briefing(briefing: CampaignBriefing, session: Optional[Session] = None):
    """
    Saves or updates a single CampaignBriefing/RecommendationSlate in the database.
    Can operate within a provided session or create its own.
    """
    def _save(db_session: Session):
        db_session.add(briefing)
        logging.info(f"CRM: Queued save for campaign/slate -> {briefing.headline}")

    if session:
        _save(session)
    else:
        with Session(engine) as new_session:
            _save(new_session)
            new_session.commit()
            logging.info(f"CRM: Committed campaign/slate -> {briefing.headline}")


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

# --- NEW: Function to get the active recommendation slate for the UI ---
def get_active_recommendation_slate_for_client(client_id: uuid.UUID, user_id: uuid.UUID, session: Session) -> Optional[CampaignBriefing]:
    """
    Finds the currently active recommendation slate for a client.
    This is used by the orchestrator to find slates that need to be marked 'stale'
    and by the API to deliver the active slate to the UI.
    Operates within a provided session.
    """
    statement = select(CampaignBriefing).where(
        CampaignBriefing.client_id == client_id,
        CampaignBriefing.user_id == user_id,
        CampaignBriefing.status == 'active'
    )
    return session.exec(statement).first()

# --- NEW: Function to update the status of a recommendation slate ---
def update_slate_status(slate_id: uuid.UUID, new_status: str, user_id: uuid.UUID, session: Session) -> Optional[CampaignBriefing]:
    """
    Updates the status of a specific recommendation slate (CampaignBriefing).
    Ensures the slate belongs to the current user for security.
    Operates within a provided session.
    """
    statement = select(CampaignBriefing).where(
        CampaignBriefing.id == slate_id,
        CampaignBriefing.user_id == user_id
    )
    slate = session.exec(statement).first()
    
    if slate:
        slate.status = new_status
        session.add(slate)
        logging.info(f"CRM: Queued status update for slate {slate_id} to '{new_status}'.")
        return slate
    return None

# --- Universal Message Log Functions ---

def save_message(message: Message, session: Optional[Session] = None):
    """
    Saves a single inbound or outbound message to the universal log.
    Can operate within a provided session or create its own.
    """
    def _save(db_session: Session):
        db_session.add(message)
        logging.info(f"CRM: Queued save for '{message.direction}' message for client_id: {message.client_id}")

    if session:
        _save(session)
    else:
        with Session(engine) as new_session:
            _save(new_session)
            new_session.commit()
            logging.info(f"CRM: Committed '{message.direction}' message for client_id: {message.client_id}")


def get_conversation_history(client_id: uuid.UUID, user_id: uuid.UUID) -> List[Message]:
    """
    Retrieves all messages for a given client, ensuring it belongs to the user.
    This is used for displaying the full conversation history in the UI.
    """
    with Session(engine) as session:
        client_check = session.exec(select(Client.id).where(Client.id == client_id, Client.user_id == user_id)).first()
        if not client_check:
            logging.warning(f"CRM AUTH: User {user_id} attempted to access messages for client {client_id} without permission.")
            return []
            
        statement = (
            select(Message)
            .where(Message.client_id == client_id)
            .options(selectinload(Message.ai_draft))
            .order_by(Message.created_at)
        )
        return session.exec(statement).all()

def get_recent_messages(client_id: uuid.UUID, user_id: uuid.UUID, limit: int = 10) -> List[Message]:
    """
    Retrieves the most recent N messages for a client to provide context to the AI.
    """
    with Session(engine) as session:
        client_check = session.exec(select(Client.id).where(Client.id == client_id, Client.user_id == user_id)).first()
        if not client_check:
            logging.warning(f"CRM AUTH: User {user_id} attempted to access messages for client {client_id} without permission.")
            return []

        statement = (
            select(Message)
            .where(Message.client_id == client_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        
        recent_messages = session.exec(statement).all()
        return recent_messages[::-1]


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
    with Session(engine) as session:
        session.add(message)
        session.commit()

def get_scheduled_message_by_id(message_id: uuid.UUID) -> Optional[ScheduledMessage]:
    with Session(engine) as session:
        return session.get(ScheduledMessage, message_id)

def get_all_scheduled_messages(user_id: uuid.UUID) -> List[ScheduledMessage]:
    with Session(engine) as session:
        statement = select(ScheduledMessage).where(ScheduledMessage.user_id == user_id)
        return session.exec(statement).all()

def update_scheduled_message(message_id: uuid.UUID, update_data: Dict[str, Any], user_id: uuid.UUID) -> Optional[ScheduledMessage]:
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
    with Session(engine) as session:
        message = session.exec(select(ScheduledMessage).where(ScheduledMessage.id == message_id, ScheduledMessage.user_id == user_id)).first()
        if not message:
            return False
        session.delete(message)
        session.commit()
        return True

def get_scheduled_messages_for_client(client_id: uuid.UUID, user_id: uuid.UUID) -> List[ScheduledMessage]:
    with Session(engine) as session:
        client_check = session.exec(select(Client.id).where(Client.id == client_id, Client.user_id == user_id)).first()
        if not client_check:
            return []
        statement = select(ScheduledMessage).where(ScheduledMessage.client_id == client_id)
        return session.exec(statement).all()

def delete_scheduled_messages_for_client(client_id: uuid.UUID, user_id: uuid.UUID):
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
    pending for a client.
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

def _get_all_clients_for_system_indexing() -> List[Client]:
    """
    Retrieves ALL clients from the database, across all users.
    USE WITH CAUTION.
    """
    with Session(engine) as session:
        statement = select(Client)
        return session.exec(statement).all()

# Community 

def get_community_overview(user_id: uuid.UUID) -> List[Dict[str, Any]]:
    """
    Retrieves all clients for a user and calculates health metrics for each.
    """
    logging.info(f"CRM: Calculating community overview for user_id: {user_id}")
    
    with Session(engine) as session:
        statement = select(Client).where(Client.user_id == user_id)
        clients = session.exec(statement).all()
        
        community_list = []
        for client in clients:
            health_score = 0
            
            last_interaction_days = None
            if client.last_interaction:
                try:
                    last_interaction_dt = datetime.fromisoformat(client.last_interaction).replace(tzinfo=timezone.utc)
                    delta = datetime.now(timezone.utc) - last_interaction_dt
                    last_interaction_days = delta.days
                    if last_interaction_days <= 7:
                        health_score += 50
                    elif last_interaction_days <= 30:
                        health_score += 30
                    elif last_interaction_days <= 90:
                        health_score += 10
                except (ValueError, TypeError):
                    logging.warning(f"CRM: Could not parse last_interaction for client {client.id}: {client.last_interaction}")

            if client.email and client.phone:
                health_score += 30
            elif client.email or client.phone:
                health_score += 15

            tag_count = len(client.user_tags) + len(client.ai_tags)
            if tag_count > 5:
                health_score += 20
            elif tag_count > 0:
                health_score += 10
            
            member_data = {
                "client_id": client.id,
                "full_name": client.full_name,
                "email": client.email,
                "phone": client.phone,
                "user_tags": client.user_tags,
                "ai_tags": client.ai_tags,
                "last_interaction_days": last_interaction_days,
                "health_score": min(health_score, 100)
            }
            community_list.append(member_data)
            
        community_list.sort(key=lambda x: x['health_score'], reverse=True)
        return community_list