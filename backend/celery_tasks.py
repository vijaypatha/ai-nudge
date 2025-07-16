# FILE: backend/celery_tasks.py
# --- FINAL, COMPLETE, AND UNABBREVIATED VERSION ---
# This version contains the master pipeline with batch processing to prevent
# memory overloads. All other helper functions are included in their entirety.

import asyncio
import logging
import uuid
from datetime import timedelta
from celery.schedules import crontab
from sqlmodel import select, Session

from celery_worker import celery_app
from agent_core.brain import nudge_engine, relationship_planner
from data import crm as crm_service
from data.models.user import User
from data.models.event import MarketEvent
from data.models.client import Client
from data.models.resource import Resource
from agent_core import llm_client
from workflow.relationship_playbooks import ALL_PLAYBOOKS

logger = logging.getLogger(__name__)

@celery_app.task(name="tasks.main_opportunity_pipeline")
def main_opportunity_pipeline_task():
    """
    The master task for the opportunity pipeline. It fetches events and
    processes them in small batches to prevent memory overloads and ensure
    data is committed incrementally.
    """
    logger.info("--- STARTING MASTER PIPELINE TASK ---")
    from data.database import engine

    all_users = crm_service.get_all_users()
    if not all_users:
        logger.info("PIPELINE: No users found. Exiting.")
        return

    for user in all_users:
        if not user.tool_provider:
            logger.info(f"PIPELINE: Skipping user {user.id} (no tool_provider).")
            continue

        logger.info(f"--- Running pipeline for user: {user.email} ---")
        
        try:
            tool = nudge_engine.get_tool_for_user(user)
            if not tool:
                logger.warning(f"Could not get tool for user {user.id}. Skipping.")
                continue

            tool_events: list[nudge_engine.ToolEvent] = asyncio.run(asyncio.to_thread(tool.get_events, minutes_ago=1440))
            
            if not tool_events:
                logger.info(f"No new tool events found for user {user.id}.")
                continue
            
            logger.info(f"Found {len(tool_events)} events from tool. Processing in batches...")

            BATCH_SIZE = 10 
            for i in range(0, len(tool_events), BATCH_SIZE):
                batch = tool_events[i:i + BATCH_SIZE]
                
                with Session(engine) as session:
                    try:
                        logger.info(f"--- Processing Batch {i//BATCH_SIZE + 1} ({len(batch)} events) ---")
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
                        logger.info(f"--- BATCH {i//BATCH_SIZE + 1} COMMITTED SUCCESSFULLY ---")

                    except Exception as e:
                        logger.error(f"--- BATCH {i//BATCH_SIZE + 1} FAILED ---", exc_info=True)
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

# --- OTHER SCHEDULED TASKS (100% Complete) ---

@celery_app.task
def check_for_recency_nudges_task():
    """
    A background task that periodically runs the recency check in the Nudge Engine.
    """
    logger.info("CELERY TASK: Kicking off daily check for recency nudges...")
    try:
        realtor_id = uuid.UUID("a8c6f1d7-8f7a-4b6e-8b0f-9e5a7d6c5b4a")
        realtor = crm_service.get_user_by_id(realtor_id)
        if not realtor:
            logger.error("CELERY TASK FAILED: Could not find a default realtor user for recency check.")
            return
            
        asyncio.run(nudge_engine.generate_recency_nudges(realtor))
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
    from sqlmodel import Session
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

            if not client.notes_embedding:
                logging.warning(f"CELERY TASK: Skipping re-scan for client {client_uuid}, no embedding found.")
                return

            realtor = client.user
            if extracted_prefs:
                if client.preferences is None:
                    client.preferences = {}
                client.preferences.update(extracted_prefs)
                logging.info(f"CELERY TASK: Using freshly extracted preferences for scoring: {extracted_prefs}")    
            active_events = crm_service.get_active_events_in_range(lookback_days=settings.RESCAN_LOOKBACK_DAYS, session=session)
            logging.info(f"CELERY TASK: Found {len(active_events)} active events in the last {settings.RESCAN_LOOKBACK_DAYS} days to score against.")

            if not active_events:
                return

            resource_ids = [event.entity_id for event in active_events if event.entity_id]
            resources = session.exec(select(Resource).where(Resource.id.in_(resource_ids))).all()
            resource_map = {res.id: res for res in resources}
            
            property_embeddings = {}
            for event in active_events:
                resource = resource_map.get(event.entity_id)
                if resource and resource.attributes.get('PublicRemarks'):
                     property_embeddings[event.id] = asyncio.run(llm_client.generate_embedding(resource.attributes.get('PublicRemarks')))

            for event in active_events:
                resource = resource_map.get(event.entity_id)
                if not resource: continue

                if crm_service.does_nudge_exist_for_client_and_resource(client_id=client_uuid, resource_id=resource.id, session=session):
                    logging.info(f"CELERY TASK: Skipping resource {resource.id} for client {client_uuid}, nudge already exists.")
                    continue
                
                property_embedding = property_embeddings.get(event.id)
                score, reasons = nudge_engine._get_client_score_for_property(client, event.payload, property_embedding)

                if score >= nudge_engine.MATCH_THRESHOLD:
                    logging.info(f"CELERY TASK: New match found! Client {client_uuid} scored {score} for event {event.id}. Creating nudge.")
                    asyncio.run(nudge_engine.create_single_client_nudge_from_event(
                        event=event, realtor=realtor, client=client, score=score, reasons=reasons, db_session=session
                    ))
            
            session.commit()
            logging.info(f"CELERY TASK: Proactive re-scan for client {client_uuid} complete.")

        except Exception as e:
            logging.error(f"CELERY TASK ERROR: Proactive re-scan for client {client_uuid} failed: {e}", exc_info=True)
            session.rollback()

@celery_app.task
def send_scheduled_message_task(message_id: str):
    """
    (Future Use) This task will be called by the Relationship Planner to send
    a message at a specific time in the future.
    """
    logger.info(f"CELERY TASK: Pretending to send scheduled message -> {message_id}")
    pass

@celery_app.task
def reschedule_recurring_messages_task():
    """
    Runs daily. Finds SENT recurring messages and schedules the next one.
    """
    print("RECURRENCE ENGINE: Starting daily scan for recurring messages...")
    all_sent_messages = crm_service.get_all_sent_recurring_messages()
    
    all_touchpoints = {}
    for playbook in relationship_planner.ALL_PLAYBOOKS:
        for touchpoint in playbook["touchpoints"]:
            if "id" in touchpoint:
                all_touchpoints[touchpoint["id"]] = touchpoint

    for message in all_sent_messages:
        if message.is_recurring and message.playbook_touchpoint_id:
            touchpoint = all_touchpoints.get(message.playbook_touchpoint_id)
            if not touchpoint: continue

            if crm_service.has_future_recurring_message(message.client_id, message.playbook_touchpoint_id):
                continue
            
            if not message.sent_at:
                continue

            frequency_days = touchpoint.get("recurrence", {}).get("frequency_days", 90)
            next_date = message.sent_at + timedelta(days=frequency_days)
            
            realtor = crm_service.get_user_by_id(message.user_id)
            if realtor:
                relationship_planner._schedule_message_from_touchpoint(message.client, realtor, touchpoint, next_date)
    
    print("RECURRENCE ENGINE: Daily scan complete.")

# --- CELERY BEAT SCHEDULE ---
celery_app.conf.beat_schedule = {
    'run-main-pipeline-every-15-minutes': {
        'task': 'tasks.main_opportunity_pipeline',
        'schedule': crontab(minute='*/15'),
    },
}