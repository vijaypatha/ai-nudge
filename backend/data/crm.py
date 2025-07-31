# FILE: backend/data/crm.py
# --- MODIFIED FOR COMPOSITE CLIENT EMBEDDINGS ---

from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timezone, timedelta
import uuid
from uuid import UUID
import json 
from sqlmodel import Session, select, delete
from sqlalchemy.orm import selectinload
from .database import engine
import logging
from sqlalchemy.orm.attributes import flag_modified 

from agent_core import semantic_service
from .models.feedback import NegativePreference

from agent_core.deduplication.deduplication_engine import find_strong_duplicate

from .models.client import Client, ClientUpdate, ClientCreate
from .models.event import MarketEvent
from .models.user import User, UserUpdate
from .models.resource import Resource, ResourceCreate, ContentResource, ContentResourceCreate, ContentResourceUpdate, ResourceStatus
from .models.campaign import CampaignBriefing, CampaignUpdate, CampaignStatus
from .models.message import ScheduledMessage, Message, MessageStatus, MessageDirection, ScheduledMessageCreate
import uuid
from agent_core.agents import profiler as profiler_agent


import asyncio
import os

# --- User Functions ---

def get_user_by_id(user_id: uuid.UUID, session: Optional[Session] = None) -> Optional[User]:
    """
    Retrieves a single user by their unique ID.
    Can operate within a provided session or create its own.
    """
    def _get(db_session: Session):
        return db_session.get(User, user_id)

    if session:
        return _get(session)
    else:
        with Session(engine) as new_session:
            return _get(new_session)
    
def get_user_by_twilio_number(phone_number: str) -> Optional[User]:
    """Retrieves a single user by their assigned Twilio phone number."""
    with Session(engine) as session:
        statement = select(User).where(User.twilio_phone_number == phone_number)
        return session.exec(statement).first()

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

# --- NEW FUNCTION TO FIX PIPELINE CRASH ---
def get_first_onboarded_user() -> Optional[User]:
    """
    Retrieves the first user who has completed onboarding.
    Used by the system pipeline to get credentials for a global API client.
    """
    with Session(engine) as session:
        statement = (
            select(User)
            .where(User.onboarding_complete == True)
            .limit(1)
        )
        return session.exec(statement).first()
# -----------------------------------------

# --- Client Functions ---

def format_phone_number(phone: str) -> str:
    """
    Formats a phone number to international format for US numbers.
    Assumes US numbers and adds +1 prefix if not already present.
    """
    if not phone:
        return phone
    
    cleaned = ''.join(filter(str.isdigit, phone))
    
    if len(cleaned) == 10:
        return f"+1{cleaned}"
    
    if len(cleaned) == 11 and cleaned.startswith('1'):
        return f"+{cleaned}"
    
    if phone.startswith('+'):
        return phone
    
    return phone

async def create_or_update_client(user_id: uuid.UUID, client_data: ClientCreate) -> Tuple[Client, bool]:
    """
    Creates a new client or updates an existing one, then calls the semantic_service
    to generate the initial composite embedding for the client.
    """
    with Session(engine) as session:
        if client_data.phone:
            client_data.phone = format_phone_number(client_data.phone)
        
        existing_client = find_strong_duplicate(session, user_id, client_data)
        
        target_client, is_new = (None, False)

        if existing_client:
            update_dict = client_data.model_dump(exclude_unset=True)
            for key, value in update_dict.items():
                if hasattr(existing_client, key):
                    setattr(existing_client, key, value)
            target_client, is_new = existing_client, False
        else:
            new_client = Client(id=uuid.uuid4(), user_id=user_id, **client_data.model_dump())
            target_client, is_new = new_client, True

        session.add(target_client)
        session.commit()
        session.refresh(target_client)
        
        logging.info(f"CRM: {'Created new' if is_new else 'Updated existing'} client {target_client.id}. Now generating initial embedding.")
        
        await semantic_service.update_client_embedding(target_client, session)
        session.commit()
        session.refresh(target_client)

        if is_new:
            skip_immediate_processing = os.getenv("SKIP_IMMEDIATE_CONTACT_PROCESSING", "false").lower() == "true"
            if not skip_immediate_processing:
                try:
                    from celery_tasks import process_new_contact_async
                    process_new_contact_async.delay(str(target_client.id), str(user_id))
                    logging.info(f"CRM: Queued async processing for new client {target_client.full_name}")
                except Exception as e:
                    logging.error(f"CRM: Error queuing async processing for new client {target_client.id}: {e}")
            
        return target_client, is_new

def get_client_by_id(client_id: uuid.UUID, user_id: uuid.UUID, session: Optional[Session] = None) -> Optional[Client]:
    """
    Retrieves a single client by their unique ID, ensuring it belongs to the user.
    Can operate within a provided session or create its own.
    """
    def _get(db_session: Session):
        statement = select(Client).where(Client.id == client_id, Client.user_id == user_id)
        return db_session.exec(statement).first()

    if session:
        return _get(session)
    else:
        with Session(engine) as new_session:
            return _get(new_session)

def get_clients_by_ids(client_ids: List[UUID], user_id: UUID) -> List[Client]:
    """
    Retrieves a list of clients by their unique IDs, ensuring they belong to the user.
    """
    if not client_ids:
        return []
    with Session(engine) as session:
        statement = select(Client).where(
            Client.id.in_(client_ids),
            Client.user_id == user_id
        )
        return session.exec(statement).all()

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
    
async def update_client(client_id: UUID, update_data: ClientUpdate, user_id: UUID) -> tuple[Optional[Client], bool]:
    """
    Generically updates a client record and calls semantic_service to regenerate
    the embedding if any relevant data changes.
    """
    embedding_updated = False
    fields_that_trigger_embedding = {'notes', 'user_tags', 'preferences'}

    with Session(engine) as session:
        client = session.exec(select(Client).where(Client.id == client_id, Client.user_id == user_id)).first()
        if not client:
            return None, False

        update_dict = update_data.model_dump(exclude_unset=True)
        if any(field in update_dict for field in fields_that_trigger_embedding):
            embedding_updated = True

        for key, value in update_dict.items():
            if key == 'phone' and value:
                value = format_phone_number(value)
            setattr(client, key, value)
        
        session.add(client)

        if embedding_updated:
            logging.info(f"CRM: Calling semantic_service to regenerate embedding for client {client.id}.")
            await semantic_service.update_client_embedding(client, session)
            # --- ADD TRIGGER HERE ---
            try:
                from celery_tasks import rescore_client_against_recent_events_task
                rescore_client_against_recent_events_task.delay(client_id=str(client.id), user_id=str(user_id))
                logging.info(f"CRM: Queued re-score task for client {client.id}")
            except Exception as e:
                logging.error(f"CRM: Failed to trigger re-score task for client {client.id}: {e}")
            # --- END TRIGGER ---

        session.commit()
        session.refresh(client)
        return client, embedding_updated

async def delete_client(client_id: UUID, user_id: UUID) -> bool:
    """
    Deletes a client and all associated data.
    Returns True if the client was found and deleted, False otherwise.
    """
    with Session(engine) as session:
        client = session.exec(select(Client).where(Client.id == client_id, Client.user_id == user_id)).first()
        if not client:
            return False

        session.exec(delete(ScheduledMessage).where(ScheduledMessage.client_id == client_id))
        
        session.delete(client)
        session.commit()
        
        logging.info(f"CRM: Deleted client {client_id} and all associated data for user {user_id}")
        return True

def delete_draft_campaigns_for_client(client_id: UUID, user_id: UUID, session: Session) -> int:
    """
    Deletes all campaign briefings for a specific client that are in 'draft' status.
    This is used to clear out old, irrelevant nudges before a client is re-scored.
    """
    statement = delete(CampaignBriefing).where(
        CampaignBriefing.client_id == client_id,
        CampaignBriefing.user_id == user_id,
        CampaignBriefing.status == CampaignStatus.DRAFT
    )
    results = session.exec(statement)
    deleted_count = results.rowcount
    
    if deleted_count > 0:
        logging.info(f"NUDGE_ENGINE (CLEANUP): Deleted {deleted_count} stale draft nudge(s) for client {client_id}.")
        
    return deleted_count

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

async def update_client_preferences(client_id: uuid.UUID, preferences: Dict[str, Any], user_id: uuid.UUID) -> Optional[Client]:
    """Overwrites the 'preferences' and calls semantic_service to regenerate the embedding."""
    with Session(engine) as session:
        client = session.exec(select(Client).where(Client.id == client_id, Client.user_id == user_id)).first()
        if client:
            client.preferences = preferences
            session.add(client)
            await semantic_service.update_client_embedding(client, session)
            session.commit()
            session.refresh(client)
            return client
        return None

async def update_client_tags(client_id: uuid.UUID, tags: List[str], user_id: uuid.UUID) -> Optional[Client]:
    """Overwrites 'user_tags' and calls semantic_service to regenerate the embedding."""
    with Session(engine) as session:
        client = session.exec(select(Client).where(Client.id == client_id, Client.user_id == user_id)).first()
        if client:
            client.user_tags = tags
            session.add(client)
            await semantic_service.update_client_embedding(client, session)
            # --- ADD TRIGGER HERE ---
            try:
                from celery_tasks import rescore_client_against_recent_events_task
                rescore_client_against_recent_events_task.delay(client_id=str(client.id), user_id=str(user_id))
                logging.info(f"CRM: Queued re-score task for client {client.id} after tag update.")
            except Exception as e:
                logging.error(f"CRM: Failed to trigger re-score task for client {client.id}: {e}")
            # --- END TRIGGER ---
            session.commit()
            session.refresh(client)
            return client
        return None

async def update_client_notes(client_id: UUID, notes: str, user_id: UUID) -> Optional[Client]:
    """Overwrites 'notes' and calls semantic_service to regenerate the embedding."""
    with Session(engine) as session:
        client = session.exec(select(Client).where(Client.id == client_id, Client.user_id == user_id)).first()
        if client:
            client.notes = notes
            session.add(client)
            await semantic_service.update_client_embedding(client, session)
            session.commit()
            session.refresh(client)
            return client
        return None

async def update_client_intel(client_id: UUID, user_id: UUID, tags_to_add: Optional[List[str]] = None, notes_to_add: Optional[str] = None) -> Optional[Client]:
    """
    Appends notes/tags, extracts preferences, and calls semantic_service to regenerate the embedding.
    --- MODIFIED: Uses flag_modified to ensure JSON preference changes are persisted to the database. ---
    """
    with Session(engine) as session:
        client = session.exec(select(Client).where(Client.id == client_id, Client.user_id == user_id)).first()
        if not client:
            logging.warning(f"CRM: update_client_intel called for non-existent client {client_id}")
            return None
        
        user = session.get(User, user_id)
        if not user:
            logging.error(f"CRM: Could not find user {user_id} during intel update for client {client_id}")
            return None # Or handle as appropriate
            
        user_vertical = user.vertical or "general"
        profile_was_updated = False

        if tags_to_add:
            # Using ai_tags as per our discussion about automating AI-suggested tags
            client.ai_tags = sorted(list(set(client.ai_tags or []).union(set(tags_to_add))))
            flag_modified(client, "ai_tags") # Also flag the tags list as modified
            profile_was_updated = True
            logging.info(f"CRM: Updated AI tags for client {client.id}")

        if notes_to_add:
            timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            new_note_entry = f"Note from AI ({timestamp}):\n{notes_to_add}"
            client.notes = f"{client.notes}\n\n---\n\n{new_note_entry}" if client.notes else new_note_entry
            
            # Use the full client context for the best possible preference extraction
            all_text_to_analyze = f"Notes: {client.notes}\nTags: {', '.join(client.user_tags or [])} {', '.join(client.ai_tags or [])}"
            
            extracted_prefs = await profiler_agent.extract_preferences_from_text(all_text_to_analyze, user_vertical)
            
            if extracted_prefs:
                logging.info(f"CRM: Profiler extracted preferences: {extracted_prefs}")
                
                # Initialize preferences if they are None
                if client.preferences is None:
                    client.preferences = {}
                
                # Update the dictionary in place
                client.preferences.update(extracted_prefs)
                
                # --- THIS IS THE FIX ---
                # Explicitly mark the 'preferences' field as modified.
                flag_modified(client, "preferences")
                logging.info(f"CRM: Marked 'preferences' as modified for client {client.id}. New state: {client.preferences}")

            profile_was_updated = True

        if profile_was_updated:
            # The session will now track all changes to client.notes, client.ai_tags, and client.preferences
            session.add(client)
            
            # Regenerate the semantic embedding since the client's data has changed
            await semantic_service.update_client_embedding(client, session)
            
            # Queue a re-score task since preferences may have changed
            try:
                from celery_tasks import rescore_client_against_recent_events_task
                rescore_client_against_recent_events_task.delay(client_id=str(client.id), user_id=str(user_id))
                logging.info(f"CRM: Queued re-score task for client {client.id} after intel update.")
            except Exception as e:
                logging.error(f"CRM: Failed to trigger re-score task for client {client.id}: {e}")
        
        # A single commit at the end of the transaction handles all changes.
        session.commit()
        session.refresh(client)
        
        logging.info(f"CRM: Intel update complete and committed for client {client.id}. Final preferences: {client.preferences}")
        return client

async def add_client_tags(client_id: uuid.UUID, tags_to_add: List[str], user_id: uuid.UUID) -> Optional[Client]:
    """This function now calls the main intel updater for consistency."""
    return await update_client_intel(client_id=client_id, user_id=user_id, tags_to_add=tags_to_add)

async def regenerate_embedding_for_client(client: Client, session: Session):
    """Calls semantic_service to generate an embedding for a client."""
    await semantic_service.update_client_embedding(client, session)


def add_negative_preference(client_id: UUID, campaign_id: UUID, resource_embedding: List[float], user_id: UUID, session: Session) -> None:
    """
    Saves a negative preference to the database for a specific client.
    This is triggered when a user dismisses a nudge.
    """
    client = session.exec(select(Client).where(Client.id == client_id, Client.user_id == user_id)).first()
    if not client:
        logging.warning(f"CRM (FEEDBACK): User {user_id} attempted to add negative preference for unauthorized client {client_id}.")
        return

    from .models.feedback import NegativePreference
    
    new_preference = NegativePreference(
        client_id=client_id,
        source_campaign_id=campaign_id,
        dismissed_embedding=resource_embedding
    )
    session.add(new_preference)
    logging.info(f"CRM (FEEDBACK): Added negative preference for client {client_id} from campaign {campaign_id}.")


def get_negative_preferences(client_id: UUID, session: Session) -> List[List[float]]:
    """
    Retrieves all dismissed embeddings for a given client.
    """
    from .models.feedback import NegativePreference

    statement = select(NegativePreference.dismissed_embedding).where(NegativePreference.client_id == client_id)
    results = session.exec(statement).all()
    return results


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

def update_resource(resource_id: uuid.UUID, update_data: ContentResourceUpdate, user_id: uuid.UUID) -> Optional[Resource]:
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
    --- DECISIVE FIX: Correctly joins MarketEvent and Resource on entity_id ---
    """
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=lookback_days)

    # Step 1: Get the entity_ids (e.g., ListingKeys) of all active resources.
    # This is the corrected logic.
    active_resource_entity_ids = session.exec(
        select(Resource.entity_id).where(Resource.status == ResourceStatus.ACTIVE)
    ).all()

    if not active_resource_entity_ids:
        return []

    # Step 2: Use those external entity_ids to find all corresponding market events.
    statement = (
        select(MarketEvent)
        .where(
            MarketEvent.created_at >= cutoff_date,
            MarketEvent.entity_id.in_(active_resource_entity_ids)
        )
    )
    return session.exec(statement).all()

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
    Saves a single inbound or outbound message to the universal log with transaction safety.
    """
    def _save(db_session: Session):
        try:
            db_session.add(message)
            db_session.flush()  # Ensure ID is generated
            db_session.refresh(message)
            logging.info(f"CRM: Message saved successfully - ID: {message.id}, Client: {message.client_id}, Direction: {message.direction}")
        except Exception as e:
            logging.error(f"CRM: Failed to save message: {e}", exc_info=True)
            db_session.rollback()
            raise

    if session:
        _save(session)
    else:
        with Session(engine) as new_session:
            try:
                _save(new_session)
                new_session.commit()
                logging.info(f"CRM: Message committed successfully for client_id: {message.client_id}")
            except Exception as e:
                logging.error(f"CRM: Failed to commit message: {e}", exc_info=True)
                new_session.rollback()
                raise


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
            # Get the last message for this client
            last_message_statement = select(Message).where(Message.client_id == client.id).order_by(Message.created_at.desc()).limit(1)
            last_message = session.exec(last_message_statement).first()
            
            # Get unread count (messages from client that haven't been read)
            unread_statement = select(Message).where(
                Message.client_id == client.id,
                Message.direction == 'inbound',
                Message.status == 'received'  # Assuming unread messages have 'received' status
            )
            unread_messages = session.exec(unread_statement).all()
            unread_count = len(unread_messages)
            
            # Determine if client is online (simple heuristic: active in last 5 minutes)
            is_online = False
            if last_message and last_message.direction == 'inbound':
                # Ensure both datetimes are timezone-aware
                message_time = last_message.created_at.replace(tzinfo=timezone.utc) if last_message.created_at.tzinfo is None else last_message.created_at
                current_time = datetime.now(timezone.utc)
                time_diff = current_time - message_time
                is_online = time_diff.total_seconds() < 300  # 5 minutes
            
            # Get message preview
            if last_message:
                message_preview = last_message.content[:50] + "..." if len(last_message.content) > 50 else last_message.content
                # Ensure timestamp is timezone-aware UTC
                if last_message.created_at.tzinfo is None:
                    last_message_time = last_message.created_at.replace(tzinfo=timezone.utc)
                else:
                    last_message_time = last_message.created_at
            else:
                message_preview = "No messages yet"
                last_message_time = datetime.now(timezone.utc)
            
            # Only include clients who have messages (like iMessage behavior)
            if last_message:
                summary = {
                    "id": f"conv-{client.id}",
                    "client_id": client.id,
                    "client_name": client.full_name,
                    "client_phone": client.phone,
                    "last_message": message_preview,
                    "last_message_time": last_message_time.isoformat(),
                    "unread_count": unread_count,
                    "is_online": is_online,
                    "has_messages": last_message is not None,
                    "last_message_direction": last_message.direction if last_message else None,
                    "last_message_source": last_message.source if last_message else None
                }
                summaries.append(summary)
    
    # Sort by: 1) Has messages, 2) Last message time, 3) Client name
    summaries.sort(key=lambda x: (
        not x['has_messages'],  # Clients with messages first
        x['last_message_time'],  # Most recent first
        x['client_name'].lower()  # Alphabetical by name
    ), reverse=True)
    return summaries

def get_conversation_summaries_for_clients(client_ids: List[UUID], user_id: UUID) -> List[Dict[str, Any]]:
    """
    Generates a list of conversation summaries for a specific list of clients.
    """
    if not client_ids:
        return []
        
    summaries = []
    with Session(engine) as session:
        # Ensure the requested clients belong to the user for security.
        clients = session.exec(
            select(Client).where(Client.user_id == user_id, Client.id.in_(client_ids))
        ).all()
        
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

def find_clients_by_name_keyword(query: str, user_id: UUID) -> List[Client]:
    """
    Finds clients by a case-insensitive match on their full name.
    """
    with Session(engine) as session:
        statement = select(Client).where(
            Client.user_id == user_id,
            Client.full_name.ilike(f"%{query}%")
        )
        return session.exec(statement).all()


# --- Scheduled Message Functions ---

def save_scheduled_message(message: ScheduledMessage):
    with Session(engine) as session:
        session.add(message)
        session.commit()
        
def create_scheduled_message(message_data: ScheduledMessageCreate, user_id: UUID) -> ScheduledMessage:
    """
    Creates and saves a new scheduled message record in the database.
    """
    with Session(engine) as session:
        new_message = ScheduledMessage.model_validate(message_data, update={"user_id": user_id})
        session.add(new_message)
        session.commit()
        session.refresh(new_message)
        return new_message

def get_scheduled_message_by_id(message_id: uuid.UUID) -> Optional[ScheduledMessage]:
    with Session(engine) as session:
        return session.get(ScheduledMessage, message_id)

def get_all_scheduled_messages(user_id: uuid.UUID) -> List[ScheduledMessage]:
    with Session(engine) as session:
        statement = select(ScheduledMessage).where(ScheduledMessage.user_id == user_id)
        return session.exec(statement).all()

def update_scheduled_message(message_id: uuid.UUID, update_data: Dict[str, Any], user_id: uuid.UUID, session: Optional[Session] = None) -> Optional[ScheduledMessage]:
    def _update(db_session: Session):
        message = db_session.exec(select(ScheduledMessage).where(ScheduledMessage.id == message_id, ScheduledMessage.user_id == user_id)).first()
        if not message:
            return None
        for key, value in update_data.items():
            if value is not None:
                setattr(message, key, value)
        db_session.add(message)
        db_session.commit()
        db_session.refresh(message)
        return message
    
    if session:
        return _update(session)
    else:
        with Session(engine) as db_session:
            return _update(db_session)

def cancel_scheduled_message(message_id: uuid.UUID, user_id: uuid.UUID) -> Optional[ScheduledMessage]:
    """
    Cancels a scheduled message by updating its status. Does not delete the record.
    """
    with Session(engine) as session:
        message = session.exec(select(ScheduledMessage).where(ScheduledMessage.id == message_id, ScheduledMessage.user_id == user_id)).first()
        if not message or message.status != MessageStatus.PENDING:
            return None

        message.status = MessageStatus.CANCELLED
        session.add(message)
        session.commit()
        session.refresh(message)
        logging.info(f"CRM: Cancelled scheduled message {message_id} for user {user_id}. Record retained for audit.")
        return message

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

def delete_scheduled_messages_by_touchpoint_ids(client_id: UUID, user_id: UUID, touchpoint_ids: List[str]):
    """
    Deletes all PENDING scheduled messages for a client that were created by a specific
    list of playbook touchpoint IDs. This is used by the relationship planner
    to clear its own plan without affecting messages from other sources.
    """
    if not touchpoint_ids:
        logging.warning(f"CRM: Call to delete messages by touchpoint IDs received an empty list for client {client_id}. Aborting.")
        return

    with Session(engine) as session:
        client_check = session.exec(select(Client.id).where(Client.id == client_id, Client.user_id == user_id)).first()
        if not client_check:
            logging.error(f"CRM: Permission denied. User {user_id} attempted to delete messages for client {client_id}.")
            return

        statement = delete(ScheduledMessage).where(
            ScheduledMessage.client_id == client_id,
            ScheduledMessage.status == MessageStatus.PENDING,
            ScheduledMessage.playbook_touchpoint_id.in_(touchpoint_ids)
        )
        results = session.exec(statement)
        session.commit()
        logging.info(f"CRM: Deleted {results.rowcount} pending relationship plan messages for client {client_id}.")

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

# --- Community Functions ---

def enrich_clients_for_community_view(clients: List[Client]) -> List[Dict[str, Any]]:
    """
    Takes a list of clients and enriches them with calculated health metrics.
    """
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

def get_community_overview(user_id: uuid.UUID) -> List[Dict[str, Any]]:
    """
    Retrieves all clients for a user and calculates health metrics for each.
    """
    logging.info(f"CRM: Calculating community overview for user_id: {user_id}")
    
    with Session(engine) as session:
        clients = session.exec(select(Client).where(Client.user_id == user_id)).all()
        return enrich_clients_for_community_view(clients)


def clear_active_recommendations(client_id: UUID, user_id: UUID) -> bool:
    """
    Clears any active recommendation slates and removes the most recent
    AI draft from the conversation history for a specific client.
    """
    try:
        with Session(engine) as session:
            client_exists = session.exec(
                select(Client.id)
                .where(Client.id == client_id, Client.user_id == user_id)
            ).first()

            if not client_exists:
                logging.warning(f"CRM AUTH: User {user_id} attempted to clear recommendations for client {client_id} without permission.")
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
                logging.info(f"CRM: Marked {len(active_slates)} recommendation slates as completed for client {client_id}")

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
                    logging.info(f"CRM: Cleared stale AI draft from message {msg.id} for client {client_id}")
                    break

            session.commit()
            return True

    except Exception as e:
        logging.error(f"CRM: Error clearing recommendations/drafts for client {client_id}: {e}", exc_info=True)
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
    entity_id_str = str(entity_id) if entity_id else None
    if not entity_id_str:
        return None
        
    statement = select(Resource).where(Resource.entity_id == entity_id_str)
    return session.exec(statement).first()


def does_nudge_exist_for_client_and_resource(client_id: uuid.UUID, resource_id: uuid.UUID, session: Session, event_type: str) -> bool:
    """
    Checks if a nudge (CampaignBriefing) of a specific type already exists
    for a given client and triggering resource.
    This is crucial for preventing duplicate nudge notifications.
    """
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

async def process_new_contact_for_existing_events(client: Client, user_id: UUID):
    """
    Immediately score new contact against all existing events and create campaigns.
    This provides instant nudges without waiting for the next pipeline run.
    """
    from agent_core.brain.nudge_engine import _get_client_score_for_event, _create_campaign_from_event
    from agent_core.brain.verticals import VERTICAL_CONFIGS
    from data.models.user import User
    from data.models.event import MarketEvent
    from data.models.campaign import MatchedClient
    
    logging.info(f"PROCESSING NEW CONTACT: Immediately scoring {client.full_name} against existing events")
    
    user = get_user_by_id(user_id)
    if not user:
        logging.error(f"PROCESSING NEW CONTACT: User {user_id} not found")
        return 0
    
    vertical_config = VERTICAL_CONFIGS.get(user.vertical)
    if not vertical_config:
        logging.error(f"PROCESSING NEW CONTACT: No vertical config found for user {user_id}")
        return 0
    
    with Session(engine) as session:
        events = session.exec(select(MarketEvent).where(MarketEvent.user_id == user_id)).all()
        logging.info(f"PROCESSING NEW CONTACT: Found {len(events)} existing events to score against")
        
        MAX_EVENTS_TO_PROCESS = 50
        if len(events) > MAX_EVENTS_TO_PROCESS:
            events = sorted(events, key=lambda e: e.created_at, reverse=True)[:MAX_EVENTS_TO_PROCESS]
            logging.info(f"PROCESSING NEW CONTACT: Limited to {MAX_EVENTS_TO_PROCESS} most recent events for performance")
        
        campaigns_created = 0
        
        for event in events:
            resource = get_resource_by_entity_id(event.entity_id, session)
            if not resource:
                logging.warning(f"PROCESSING NEW CONTACT: No resource found for event {event.id}")
                continue
            
            if does_nudge_exist_for_client_and_resource(client.id, resource.id, session, event.event_type):
                logging.info(f"PROCESSING NEW CONTACT: Nudge already exists for client {client.id} and resource {resource.id}")
                continue
            
            try:
                resource_embedding = None
                if resource.resource_type == "property":
                    remarks = resource.attributes.get('PublicRemarks')
                    if remarks:
                        from agent_core import llm_client
                        resource_embedding = await llm_client.generate_embedding(remarks)
                
                score, reasons = _get_client_score_for_event(client, event, resource_embedding, vertical_config)
                
                if score >= 25:
                    logging.info(f"PROCESSING NEW CONTACT: Client {client.full_name} matched event {event.id} with score {score}. Reasons: {reasons}")
                    
                    matched_audience = [MatchedClient(
                        client_id=client.id, 
                        client_name=client.full_name, 
                        match_score=score, 
                        match_reasons=reasons
                    )]
                    
                    await _create_campaign_from_event(event, user, resource, matched_audience, db_session=session)
                    campaigns_created += 1
                    logging.info(f"PROCESSING NEW CONTACT: Created campaign for event {event.id}")
                else:
                    logging.info(f"PROCESSING NEW CONTACT: Client {client.full_name} did not match event {event.id}. Score: {score}")
                    
            except Exception as e:
                logging.error(f"PROCESSING NEW CONTACT: Error processing event {event.id}: {e}")
        
        logging.info(f"PROCESSING NEW CONTACT: Created {campaigns_created} campaigns for {client.full_name}")
        return campaigns_created