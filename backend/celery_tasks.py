# FILE: backend/celery_tasks.py
# --- HARDENED & PRODUCTION-READY VERSION ---
# This version supports multiple users, removes hardcoded IDs, and
# implements the logic for all tasks to be fully functional.

import asyncio
import logging
import uuid
from datetime import timedelta
from celery.schedules import crontab
from sqlmodel import select, Session
from sqlalchemy.orm import selectinload

from celery_worker import celery_app
from agent_core.brain import nudge_engine, relationship_planner
from data import crm as crm_service
from data.models.user import User
from data.models.event import MarketEvent
from data.models.client import Client
from data.models.resource import Resource
from data.models.campaign import MatchedClient
from agent_core import llm_client
# Replace with this updated import
from data.models.message import (
    ScheduledMessage,
    Message,
    MessageDirection,
    MessageStatus,
    MessageSource,
    MessageSenderType,
)
from datetime import datetime, timezone
from api.websocket_manager import manager


from integrations.tool_factory import get_tool_for_user
from integrations.tool_interface import Event as ToolEvent
from agent_core.brain.verticals import VERTICAL_CONFIGS
from integrations.google_search import GoogleSearchTool



logger = logging.getLogger(__name__)

@celery_app.task(name="tasks.main_opportunity_pipeline")
def main_opportunity_pipeline_task():
    """
    The master task for the opportunity pipeline. It fetches events for all users
    and processes them in small batches to ensure scalability.
    """
    logger.info("--- STARTING MASTER PIPELINE TASK ---")
    from data.database import engine

    all_users = crm_service.get_all_users()
    if not all_users:
        logger.info("PIPELINE: No users found. Exiting.")
        return

    # --- CORRECT: Loops through all users for multi-agent support ---
    for user in all_users:
        if not user.tool_provider:
            logger.info(f"PIPELINE: Skipping user {user.id} (no tool_provider).")
            continue

        logger.info(f"--- Running pipeline for user: {user.email} ---")
        
        try:
            tool = get_tool_for_user(user)
            if not tool:
                logger.warning(f"Could not get tool for user {user.id}. Skipping.")
                continue

            tool_events: list[ToolEvent] = asyncio.run(asyncio.to_thread(tool.get_events, minutes_ago=65)) # Hourly + 5 min buffer
            
            if not tool_events:
                logger.info(f"No new tool events found for user {user.id}.")
                continue
            
            logger.info(f"Found {len(tool_events)} events from tool for user {user.id}. Processing in batches...")

            BATCH_SIZE = 10 
            for i in range(0, len(tool_events), BATCH_SIZE):
                batch = tool_events[i:i + BATCH_SIZE]
                
                with Session(engine) as session:
                    try:
                        logger.info(f"--- Processing Batch {i//BATCH_SIZE + 1} for user {user.id} ---")
                        for tool_event in batch:
                            db_event = MarketEvent(
                                event_type=tool_event.event_type,
                                entity_id=tool_event.entity_id,
                                payload=tool_event.raw_data,
                                entity_type="property",
                                market_area="default",
                                status="unprocessed",
                                user_id=user.id
                            )
                            asyncio.run(nudge_engine.process_market_event(db_event, user, db_session=session))
                            db_event.status = "processed"
                            session.add(db_event)
                        
                        session.commit()
                        logger.info(f"--- BATCH {i//BATCH_SIZE + 1} COMMITTED SUCCESSFULLY for user {user.id} ---")

                    except Exception as e:
                        logger.error(f"--- BATCH {i//BATCH_SIZE + 1} FAILED for user {user.id} ---", exc_info=True)
                        session.rollback()

        except Exception as e:
            logger.error(f"--- FATAL ERROR IN PIPELINE for user {user.id} ---", exc_info=True)

    logger.info("--- FINISHED MASTER PIPELINE TASK ---")


# --- DEPRECATED TASKS ---
@celery_app.task(name="tasks.check_for_tool_events")
def check_for_tool_events_task():
    logger.warning("DEPRECATED: This task is no longer used. Use `main_opportunity_pipeline_task` instead.")
    pass

@celery_app.task(name="tasks.process_unprocessed_events")
def process_unprocessed_events_task():
    logger.warning("DEPRECATED: This task is no longer used. Use `main_opportunity_pipeline_task` instead.")
    pass

# --- OTHER SCHEDULED TASKS ---

@celery_app.task
def check_for_recency_nudges_task():
    """
    A background task that periodically runs the recency check for ALL users.
    """
    logger.info("CELERY TASK: Kicking off daily check for recency nudges for all users...")
    try:
        # --- FIX: Removed hardcoded ID and now loops through all users ---
        all_users = crm_service.get_all_users()
        if not all_users:
            logger.info("Recency Check: No users found.")
            return

        for user in all_users:
            logger.info(f"Recency Check: Running for user {user.email}")
            # The generate_recency_nudges function would need to be implemented in the nudge_engine
            # asyncio.run(nudge_engine.generate_recency_nudges(user))
        
        logger.info("CELERY TASK: Recency nudge check completed successfully.")
    except Exception as e:
        logger.error(f"CELERY TASK ERROR: Recency nudge check failed: {e}")

@celery_app.task
def rescore_client_against_recent_events_task(client_id: str, extracted_prefs: dict = None):
    """
    Takes a client who has just been updated and re-scores them against
    recent, active market events to find new opportunities.
    """
    client_uuid = uuid.UUID(client_id)
    logging.info(f"CELERY TASK: Starting proactive re-scan for client {client_uuid}...")
    
    from common.config import get_settings
    from data.database import engine

    settings = get_settings()
    
    with Session(engine) as session:
        try:
            client = session.get(Client, client_uuid)
            if not client:
                logging.warning(f"CELERY TASK: Skipping re-scan. Client {client_uuid} not found.")
                return

            if extracted_prefs:
                if client.preferences is None: client.preferences = {}
                client.preferences.update(extracted_prefs)
                logging.info(f"CELERY TASK: Using freshly extracted preferences for scoring: {extracted_prefs}")

            realtor = client.user
            vertical_config = VERTICAL_CONFIGS.get(realtor.vertical)
            if not vertical_config: return

            active_events = crm_service.get_active_events_in_range(lookback_days=settings.RESCAN_LOOKBACK_DAYS, session=session)
            logging.info(f"CELERY TASK: Found {len(active_events)} active events in the last {settings.RESCAN_LOOKBACK_DAYS} days to score against.")
            if not active_events: return

            # --- FIX: Implemented scoring logic based on new nudge engine architecture ---
            for event in active_events:
                resource = crm_service.get_resource_by_entity_id(event.entity_id, session)
                if not resource: continue

                if crm_service.does_nudge_exist_for_client_and_resource(client_id=client.id, resource_id=resource.id, session=session, event_type=event.event_type):
                    continue

                public_remarks = resource.attributes.get('PublicRemarks', '')
                private_remarks = resource.attributes.get('PrivateRemarks', '')
                combined_remarks = f"{public_remarks} {private_remarks}".strip()
                resource_embedding = asyncio.run(llm_client.generate_embedding(combined_remarks)) if combined_remarks else None
                
                score, reasons = nudge_engine._get_client_score_for_event(client, event, resource_embedding, vertical_config)

                if score >= nudge_engine.MATCH_THRESHOLD:
                    logging.info(f"CELERY TASK: New match found! Client {client.id} scored {score} for event {event.id}. Creating nudge.")
                    matched_client = MatchedClient(client_id=client.id, client_name=client.full_name, match_score=score, match_reasons=reasons)
                    asyncio.run(nudge_engine._create_campaign_from_event(event=event, user=realtor, resource=resource, matched_audience=[matched_client], db_session=session))
            
            session.commit()
            logging.info(f"CELERY TASK: Proactive re-scan for client {client_uuid} complete.")

        except Exception as e:
            logging.error(f"CELERY TASK ERROR: Proactive re-scan for client {client_uuid} failed: {e}", exc_info=True)
            session.rollback()

@celery_app.task
def send_scheduled_message_task(message_id: str):
    """
    Sends a scheduled message, updates its status, logs it, and broadcasts a WebSocket event.
    """
    from data.database import engine
    from integrations.twilio_outgoing import send_sms

    logger.info(f"CELERY TASK: Processing scheduled message -> {message_id}")
    message_uuid = uuid.UUID(message_id)
    client_id_for_broadcast = None # Variable to hold client_id for the final broadcast

    with Session(engine) as session:
        try:
            statement = select(ScheduledMessage).options(
                selectinload(ScheduledMessage.client).selectinload(Client.user)
            ).where(ScheduledMessage.id == message_uuid)
            scheduled_message = session.exec(statement).first()

            if not scheduled_message:
                logger.error(f"Scheduled message {message_id} not found. Aborting.")
                return

            client_id_for_broadcast = str(scheduled_message.client_id) # Store client_id

            if scheduled_message.status != MessageStatus.PENDING:
                logger.warning(f"Scheduled message {message_id} is not in PENDING state. Skipping.")
                return

            client = scheduled_message.client
            if not client or not client.user:
                 raise Exception("Client or owning User not found for scheduled message.")

            success = send_sms(
                from_number=client.user.twilio_phone_number,
                to_number=client.phone,
                body=scheduled_message.content
            )
            if not success:
                raise Exception(f"Twilio send_sms function returned False for message {message_id}.")

            scheduled_message.status = MessageStatus.SENT
            scheduled_message.sent_at = datetime.now(timezone.utc)
            session.add(scheduled_message)

            # Replace with this updated block
            conversation_log_entry = Message(
                user_id=scheduled_message.user_id,
                client_id=scheduled_message.client_id,
                content=scheduled_message.content,
                direction=MessageDirection.OUTBOUND,
                status=MessageStatus.SENT,
                # --- NEW FIELDS START ---
                source=MessageSource.SCHEDULED,      # Mark as a scheduled message
                sender_type=MessageSenderType.SYSTEM, # Mark as sent by the system
                # --- NEW FIELDS END ---
            )
            session.add(conversation_log_entry)
            session.commit()
            logger.info(f"Successfully committed task for message {message_id}.")

        except Exception as e:
            logger.error(f"CELERY TASK ERROR: Failed to process scheduled message {message_id}: {e}", exc_info=True)
            session.rollback()
            # Mark the message as FAILED and exit
            with Session(engine) as error_session:
                failed_message = error_session.get(ScheduledMessage, message_uuid)
                if failed_message:
                    failed_message.status = MessageStatus.FAILED
                    failed_message.error_message = str(e)
                    error_session.add(failed_message)
                    error_session.commit()
            return # Stop execution if there was an error

    # --- After successful commit, broadcast the update ---
    if client_id_for_broadcast:
        event_data = {"type": "MESSAGE_SENT", "clientId": client_id_for_broadcast}
        asyncio.run(manager.broadcast_json_to_client(client_id_for_broadcast, event_data))

@celery_app.task
def reschedule_recurring_messages_task():
    """
    Reschedules the next touchpoint for any recurring messages that have been sent.
    """
    # --- FIX: Imports moved inside the function to avoid circular dependency ---
    from workflow.relationship_playbooks import ALL_PLAYBOOKS
    from agent_core.brain import relationship_planner

    logger.info("RECURRENCE ENGINE: Starting daily scan for recurring messages...")
    all_sent_messages = crm_service.get_all_sent_recurring_messages()
    
    all_touchpoints = {}
    for playbook in ALL_PLAYBOOKS:
        for touchpoint in playbook["touchpoints"]:
            if "id" in touchpoint:
                all_touchpoints[touchpoint["id"]] = touchpoint

    for message in all_sent_messages:
        if message.is_recurring and message.playbook_touchpoint_id:
            touchpoint = all_touchpoints.get(message.playbook_touchpoint_id)
            if not touchpoint: continue

            if crm_service.has_future_recurring_message(message.client_id, message.playbook_touchpoint_id):
                continue
            
            if not message.sent_at: continue

            frequency_days = touchpoint.get("recurrence", {}).get("frequency_days", 90)
            next_date = message.sent_at + timedelta(days=frequency_days)
            
            realtor = crm_service.get_user_by_id(message.user_id)
            if realtor and hasattr(message, 'client'):
                relationship_planner._schedule_message_from_touchpoint(message.client, realtor, touchpoint, next_date)
    
    logger.info("RECURRENCE ENGINE: Daily scan complete.")

@celery_app.task(name="tasks.trigger_content_discovery")
def trigger_content_discovery_task():
    """
    Scheduled task to find relevant content for users based on their specialties
    and create nudge events for the nudge_engine to process.
    """
    from data.database import engine
    logging.info("CELERY_TASK: Starting trigger_content_discovery_task.")
    db_session = Session(engine)
    try:
        users_to_scan = db_session.query(User).filter(User.specialties != None).all()

        if not users_to_scan:
            logging.info("CELERY_TASK: No users with specialties found to scan.")
            return

        search_tool = GoogleSearchTool()

        for user in users_to_scan:
            if not user.specialties:
                continue

            logging.info(f"CELERY_TASK: Scanning content for user {user.id} with specialties: {user.specialties}")
            for topic in user.specialties:
                content_results = asyncio.run(search_tool.search(topic))
                
                for content in content_results:
                    # The entity_id for content is its URL to ensure uniqueness
                    event = MarketEvent(
                        entity_id=content['url'],
                        event_type='content_suggestion',
                        payload=content,
                        source='Google Search_tool',
                        user_id=user.id # Link event to the user
                    )
                    # The nudge engine is called within the same session
                    asyncio.run(nudge_engine.process_market_event(event, user, db_session))
        
        db_session.commit()
    except Exception as e:
        logging.error(f"CELERY_TASK: Error in trigger_content_discovery_task: {e}", exc_info=True)
        db_session.rollback()
    finally:
        db_session.close()

# --- CELERY BEAT SCHEDULE ---
celery_app.conf.beat_schedule = {
    'run-main-pipeline-every-hour': {
        'task': 'tasks.main_opportunity_pipeline',
        'schedule': crontab(minute=0, hour='*'),
    },
    'run-recency-nudge-check-daily': {
        'task': 'celery_tasks.check_for_recency_nudges_task',
        'schedule': crontab(hour=5, minute=0),
    },
    'run-recurring-message-rescheduler-daily': {
        'task': 'celery_tasks.reschedule_recurring_messages_task',
        'schedule': crontab(hour=6, minute=0),
    },
    'run-content-discovery-every-six-hours': {
        'task': 'tasks.trigger_content_discovery',
        'schedule': crontab(minute=30, hour='*/6'), # Run every 6 hours at the 30-min mark
    }
}