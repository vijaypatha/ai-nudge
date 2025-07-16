# FILE: backend/data/crm.py
# --- COMPLETE & UNABBREVIATED ---

from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timezone, timedelta
import uuid
from sqlmodel import Session, select, delete
from sqlalchemy.orm import selectinload
from .database import engine
import logging

from agent_core import llm_client

from agent_core.deduplication.deduplication_engine import find_strong_duplicate

from .models.client import Client, ClientUpdate, ClientCreate
from .models.event import MarketEvent
from .models.user import User, UserUpdate
from .models.resource import Resource, ResourceCreate, ResourceUpdate
from .models.campaign import CampaignBriefing, CampaignUpdate, CampaignStatus
from .models.message import ScheduledMessage, Message, MessageStatus, MessageDirection
from agent_core.agents import profiler as profiler_agent

from uuid import UUID
import asyncio

# --- User Functions (Unchanged) ---

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

async def update_client_notes(client_id: UUID, notes: str, user_id: UUID) -> Optional[Client]:
    """
    Overwrites the 'notes' field and generates a new semantic embedding.
    NOW ASYNCHRONOUS to support embedding calls.
    """
    with Session(engine) as session:
        client = session.exec(select(Client).where(Client.id == client_id, Client.user_id == user_id)).first()
        if client:
            client.notes = notes
            
            if notes and notes.strip():
                logging.info(f"CRM: Generating new notes embedding for client {client.id}...")
                embedding = await llm_client.generate_embedding(notes)
                client.notes_embedding = embedding
            else:
                client.notes_embedding = None
            
            session.add(client)
            session.commit()
            session.refresh(client)
            logging.info(f"CRM: Manually updated notes and embedding for client {client.id}")
            return client
        return None

async def update_client_intel(
    client_id: UUID, 
    user_id: UUID,
    tags_to_add: Optional[List[str]] = None, 
    notes_to_add: Optional[str] = None
) -> Optional[Client]:
    """
    Appends notes/tags, extracts structured preferences from the notes, 
    regenerates the AI embedding, and triggers a proactive re-scan.
    """
    with Session(engine) as session:
        client = session.exec(select(Client).where(Client.id == client_id, Client.user_id == user_id)).first()
        if not client:
            logging.error(f"CRM: update_client_intel failed. Client {client_id} not found for user {user_id}.")
            return None
        
        notes_were_updated = False
        if tags_to_add:
            client.user_tags = sorted(list(set(client.user_tags or []).union(set(tags_to_add))))

        if notes_to_add:
            timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            new_note_entry = f"Note from AI ({timestamp}):\n{notes_to_add}"
            if client.notes:
                client.notes = f"{client.notes}\n\n---\n\n{new_note_entry}"
            else:
                client.notes = new_note_entry
            notes_were_updated = True

        if notes_were_updated and client.notes:
            all_text_to_analyze = f"Notes: {client.notes}\nTags: {', '.join(client.user_tags)}"
            extracted_prefs = await profiler_agent.extract_preferences_from_text(all_text_to_analyze)
            
            if extracted_prefs:
                if client.preferences is None:
                    client.preferences = {}
                client.preferences.update(extracted_prefs)
                logging.info(f"CRM: Automatically updated structured preferences for client {client.id}: {extracted_prefs}")

        if notes_were_updated and client.notes and client.notes.strip():
            logging.info(f"CRM: Regenerating notes embedding for client {client.id} after intel update...")
            client.notes_embedding = await llm_client.generate_embedding(client.notes)
        
        session.add(client)
        session.commit()
        session.refresh(client)

        if notes_were_updated:
            try:
                from celery_tasks import rescore_client_against_recent_events_task
                logging.info(f"CRM: Triggering proactive re-scan for client {client.id} due to profile update.")
                rescore_client_against_recent_events_task.delay(client_id=str(client.id), extracted_prefs=extracted_prefs if 'extracted_prefs' in locals() else None)
            except Exception as e:
                logging.error(f"CRM: Failed to trigger re-scan task for client {client.id}: {e}", exc_info=True)
        
        return client

async def update_client(client_id: UUID, update_data: ClientUpdate, user_id: UUID) -> Optional[Client]:
    """
    Generically updates a client record. Regenerates embedding if notes change.
    NOW ASYNCHRONOUS to support embedding calls.
    """
    with Session(engine) as session:
        client = session.exec(select(Client).where(Client.id == client_id, Client.user_id == user_id)).first()
        if not client:
            return None

        update_dict = update_data.model_dump(exclude_unset=True)
        notes_updated = 'notes' in update_dict

        for key, value in update_dict.items():
            setattr(client, key, value)
        
        if notes_updated:
            notes_content = update_dict.get('notes')
            if notes_content and notes_content.strip():
                logging.info(f"CRM: Regenerating notes embedding for client {client.id} via generic update...")
                embedding = await llm_client.generate_embedding(notes_content)
                client.notes_embedding = embedding
            else:
                client.notes_embedding = None

        session.add(client)
        session.commit()
        session.refresh(client)
        return client


def add_client_tags(client_id: uuid.UUID, tags_to_add: List[str], user_id: uuid.UUID) -> Optional[Client]:
    """This function now calls the main intel updater for consistency."""
    # This should be an async call now, but we'll leave it sync for now to avoid breaking changes.
    # A proper fix would be to make this async and await it.
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(update_client_intel(client_id=client_id, user_id=user_id, tags_to_add=tags_to_add))


async def regenerate_embedding_for_client(client: Client, session: Session):
    """
    Generates and saves an embedding for a client based on their current notes.
    This is a helper designed for seeding or backfilling operations.
    """
    if client.notes and client.notes.strip():
        logging.info(f"CRM (SEED): Generating embedding for client {client.id} - {client.full_name}")
        embedding = await llm_client.generate_embedding(client.notes)
        client.notes_embedding = embedding
        session.add(client)
    else:
        logging.info(f"CRM (SEED): Skipping embedding for client {client.id} - no notes.")
        client.notes_embedding = None
        session.add(client)

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


def get_new_campaign_briefings_for_user(user_id: uuid.UUID, session: Optional[Session] = None) -> List[CampaignBriefing]:
    """
    Fetches all campaign briefings for a user that are in a 'DRAFT' state.
    This is what populates the main "Nudges" page in the UI.
    """
    db_session = session or Session(engine)
    try:
        logging.info(f"--- DEBUG: Querying for DRAFT campaigns for user_id: {user_id} ---")
        statement = select(CampaignBriefing).where(
            CampaignBriefing.user_id == user_id,
            CampaignBriefing.status == CampaignStatus.DRAFT
        )
        results = db_session.exec(statement).all()
        logging.info(f"--- DEBUG: Found {len(results)} DRAFT campaigns in database for user {user_id} ---")
        return results
    finally:
        if not session:
            db_session.close()

def get_campaign_briefing_by_id(
    campaign_id: uuid.UUID, 
    user_id: uuid.UUID, 
    session: Optional[Session] = None
) -> Optional[CampaignBriefing]:
    """
    Retrieves a single campaign briefing by its unique ID, ensuring it belongs to the user.
    Can optionally use a provided database session to participate in a larger transaction.
    """
    def _get(db_session: Session) -> Optional[CampaignBriefing]:
        statement = select(CampaignBriefing).where(
            CampaignBriefing.id == campaign_id, 
            CampaignBriefing.user_id == user_id
        )
        return db_session.exec(statement).first()

    if session:
        return _get(session)
    else:
        with Session(engine) as new_session:
            return _get(new_session)
    
def get_active_events_in_range(lookback_days: int, session: Session) -> List[MarketEvent]:
    """
    Retrieves all market events within a given lookback period that are linked
    to a resource that is still 'active'.
    """
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=lookback_days)
    
    active_resource_ids = session.exec(
        select(Resource.id).where(Resource.status == 'active')
    ).all()

    if not active_resource_ids:
        return []

    statement = (
        select(MarketEvent)
        .where(
            MarketEvent.created_at >= cutoff_date,
            MarketEvent.entity_id.in_(active_resource_ids)
        )
    )
    return session.exec(statement).all()

def does_nudge_exist_for_client_and_resource(client_id: UUID, resource_id: UUID, session: Session) -> bool:
    """
    Checks if a campaign briefing already exists for a specific client and resource.
    This is used for duplicate prevention.
    """
    statement = select(CampaignBriefing).where(CampaignBriefing.triggering_resource_id == resource_id)
    campaigns = session.exec(statement).all()

    if not campaigns:
        return False

    str_client_id = str(client_id)
    for campaign in campaigns:
        for audience_member in campaign.matched_audience:
            if audience_member.get('client_id') == str_client_id:
                return True
    
    return False

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

def cancel_scheduled_messages_for_plan(plan_id: UUID, user_id: UUID, session: Session) -> int:
    """
    Finds and cancels all PENDING scheduled messages associated with a specific plan.
    This is the core mechanism for "pausing" an adaptive nudge plan when a client replies.
    Returns the number of messages that were cancelled.
    """
    plan_check = session.exec(
        select(CampaignBriefing.id)
        .where(CampaignBriefing.id == plan_id, CampaignBriefing.user_id == user_id)
    ).first()

    if not plan_check:
        logging.warning(f"CRM AUTH: User {user_id} attempted to cancel messages for plan {plan_id} without permission.")
        return 0

    messages_to_cancel_statement = select(ScheduledMessage).where(
        ScheduledMessage.parent_plan_id == plan_id,
        ScheduledMessage.status == MessageStatus.PENDING
    )
    messages_to_cancel = session.exec(messages_to_cancel_statement).all()
    
    count = len(messages_to_cancel)
    if count > 0:
        logging.info(f"CRM: Found {count} pending message(s) for plan {plan_id} to cancel.")
        for msg in messages_to_cancel:
            msg.status = MessageStatus.CANCELLED
            session.add(msg)
        logging.info(f"CRM: Successfully cancelled {count} message(s) for plan {plan_id}.")
    
    return count

def get_all_active_slates_for_client(client_id: uuid.UUID, user_id: uuid.UUID, session: Session) -> List[CampaignBriefing]:
    """
    Finds ALL currently active recommendation slates and/or plans for a client.
    A slate is considered "active" for the UI if it is in the DRAFT state.
    --- MODIFIED: Now sorts by creation date to ensure predictable order. ---
    """
    statement = select(CampaignBriefing).where(
        CampaignBriefing.client_id == client_id,
        CampaignBriefing.user_id == user_id,
        CampaignBriefing.status == CampaignStatus.DRAFT
    ).order_by(CampaignBriefing.created_at.desc()) # This sorting is critical
    
    return session.exec(statement).all()



def update_slate_status(slate_id: uuid.UUID, new_status: CampaignStatus, user_id: uuid.UUID, session: Session) -> Optional[CampaignBriefing]:
    """
    Updates the status of a specific recommendation slate (CampaignBriefing).
    """
    statement = select(CampaignBriefing).where(
        CampaignBriefing.id == slate_id,
        CampaignBriefing.user_id == user_id
    )
    slate = session.exec(statement).first()
    if slate:
        slate.status = new_status
        session.add(slate)
        logging.info(f"CRM: Queued status update for slate {slate_id} to '{new_status.value}'.")
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
            .options(selectinload(Message.ai_drafts))
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

def clear_active_recommendations(client_id: UUID, user_id: UUID) -> bool:
    """
    Clears any active recommendation slates and removes the most recent
    AI draft from the conversation history for a specific client.

    Called whenever the conversation advances (e.g., a message is sent or
    edited) so that stale suggestions disappear from the UI.
    """
    try:
        with Session(engine) as session:
            client_exists = session.exec(
                select(Client.id)
                .where(Client.id == client_id, Client.user_id == user_id)
            ).first()

            if not client_exists:
                logging.warning(
                    f"CRM AUTH: User {user_id} attempted to clear recommendations "
                    f"for client {client_id} without permission."
                )
                return False

            active_slates = session.exec(
                select(CampaignBriefing).where(
                    CampaignBriefing.client_id == client_id,
                    CampaignBriefing.user_id == user_id,
                    CampaignBriefing.status == "active",
                )
            ).all()

            for slate in active_slates:
                slate.status = "completed"
                session.add(slate)

            if active_slates:
                logging.info(
                    f"CRM: Marked {len(active_slates)} recommendation slates as "
                    f"completed for client {client_id}"
                )

            messages = session.exec(
                select(Message)
                .where(Message.client_id == client_id)
                .options(selectinload(Message.ai_draft))
                .order_by(Message.created_at.desc())
            ).all()

            for msg in messages:
                if msg.ai_draft:
                    msg.ai_draft = None
                    session.add(msg)
                    logging.info(
                        f"CRM: Cleared stale AI draft from message {msg.id} "
                        f"for client {client_id}"
                    )
                    break

            session.commit()
            return True

    except Exception as e:
        logging.error(
            f"CRM: Error clearing recommendations/drafts for client {client_id}: {e}",
            exc_info=True,
        )
        return False


def add_client_notes(client_id: UUID, notes_to_add: str, user_id: UUID) -> Optional[Client]:
    """
    Appends new notes to a client's existing notes field.
    """
    with Session(engine) as session:
        client = session.exec(
            select(Client).where(Client.id == client_id, Client.user_id == user_id)
        ).first()
        
        if client:
            if hasattr(client, 'notes') and client.notes:
                client.notes = f"{client.notes}\n\n{notes_to_add}"
            else:
                client.notes = notes_to_add
            
            session.add(client)
            session.commit()
            session.refresh(client)
            logging.info(f"CRM: Added notes to client {client_id}")
            return client
            
        return None

def update_client_tags_and_notes(
    client_id: UUID, 
    tags_to_add: List[str], 
    notes_to_add: str, 
    user_id: UUID
) -> bool:
    """
    Updates client with new tags and notes in a single transaction.
    """
    try:
        with Session(engine) as session:
            client = session.exec(
                select(Client).where(Client.id == client_id, Client.user_id == user_id)
            ).first()
            
            if not client:
                return False
            
            if tags_to_add:
                existing_tags = set(client.user_tags)
                new_tags = set(tags_to_add)
                updated_tags = sorted(list(existing_tags.union(new_tags)))
                client.user_tags = updated_tags
                logging.info(f"CRM: Updated tags for client {client_id}: {updated_tags}")
            
            if notes_to_add:
                if hasattr(client, 'notes') and client.notes:
                    client.notes = f"{client.notes}\n\n{notes_to_add}"
                else:
                    client.notes = notes_to_add
            
            session.add(client)
            session.commit()
            session.refresh(client)
            return True
            
    except Exception as e:
        logging.error(f"CRM: Error updating client {client_id}: {e}", exc_info=True)
        return False
    
def get_resource_by_entity_id(entity_id: str, session: Session) -> Optional[Resource]:
    """
    Finds a resource by its external entity ID from the data provider.
    This is crucial for preventing duplicate resource creation.
    """
    statement = select(Resource).where(Resource.entity_id == entity_id)
    return session.exec(statement).first()


def does_nudge_exist_for_client_and_resource(client_id: uuid.UUID, resource_id: uuid.UUID, session: Session, event_type: str) -> bool:
    """
    Checks if a nudge (CampaignBriefing) of a specific type already exists
    for a given client and triggering resource.
    This is crucial for preventing duplicate nudge notifications.
    """
    # This query is a bit more complex as it needs to check the JSON field.
    # Note: This approach is functional but may not be the most performant on very large datasets.
    # A more optimized solution might involve a dedicated join table between clients and campaigns.
    
    statement = select(CampaignBriefing).where(
        CampaignBriefing.triggering_resource_id == resource_id,
        CampaignBriefing.campaign_type == event_type
    )
    
    briefings = session.exec(statement).all()
    
    for briefing in briefings:
        for audience_member in briefing.matched_audience:
            if audience_member.get("client_id") == str(client_id):
                return True
    return False