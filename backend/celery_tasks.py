# FILE: backend/celery_tasks.py
# PURPOSE: Defines the background tasks that our Celery worker will run.
import asyncio
import logging
import uuid
from datetime import timedelta
from celery.schedules import crontab
from sqlmodel import select

from celery_worker import celery_app
from agent_core.brain import nudge_engine, relationship_planner
from data import crm as crm_service
from data.models.message import MessageStatus
from data.models.client import Client
from data.models.resource import Resource
from agent_core import llm_client
from workflow.relationship_playbooks import ALL_PLAYBOOKS

logger = logging.getLogger(__name__)

@celery_app.task
def check_mls_for_events_task():
    """
    The main scheduled task to poll the MLS for new events and process them.
    This is the "alarm" that triggers our "Perceive -> Reason" loop.
    """
    logger.info("CELERY TASK: Starting MLS event check...")
    try:
        realtor_id = uuid.UUID("a8c6f1d7-8f7a-4b6e-8b0f-9e5a7d6c5b4a")
        realtor = crm_service.get_user_by_id(realtor_id)
        if not realtor:
            logger.error("CELERY TASK FAILED: Could not find a default realtor user.")
            return
        asyncio.run(nudge_engine.scan_for_all_market_events(realtor, minutes_ago=15))
        logger.info("CELERY TASK: MLS event check completed successfully.")
    except Exception as e:
        logger.error(f"CELERY TASK ERROR: MLS event check failed: {e}")

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

            # If new prefs were passed directly, merge them into the client object
            # This ensures we are scoring with the absolute latest data.
            if extracted_prefs:
                if client.preferences is None: client.preferences = {}
                client.preferences.update(extracted_prefs)
                logging.info(f"CELERY TASK: Using freshly extracted preferences for scoring: {extracted_prefs}")

            if not client.notes_embedding:
                logging.warning(f"CELERY TASK: Skipping re-scan for client {client_uuid}, no embedding found.")
                return

            realtor = client.user
            # If new prefs were passed directly, merge them into the client object
# This ensures we are scoring with the absolute latest data.
            if extracted_prefs:
                if client.preferences is None:
                    client.preferences = {}
                client.preferences.update(extracted_prefs)
                logging.info(f"CELERY TASK: Using freshly extracted preferences for scoring: {extracted_prefs}")    
            active_events = crm_service.get_active_events_in_range(lookback_days=settings.RESCAN_LOOKBACK_DAYS, session=session)
            logging.info(f"CELERY TASK: Found {len(active_events)} active events in the last {settings.RESCAN_LOOKBACK_DAYS} days to score against.")

            if not active_events:
                return

            resource_ids = [event.entity_id for event in active_events]
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
            
            frequency_days = touchpoint.get("recurrence", {}).get("frequency_days", 90)
            next_date = message.sent_at + timedelta(days=frequency_days)
            
            realtor = crm_service.get_user_by_id(touchpoint.get("user_id"))
            relationship_planner._schedule_message_from_touchpoint(message.client, realtor, touchpoint, next_date)
    
    print("RECURRENCE ENGINE: Daily scan complete.")

celery_app.conf.beat_schedule['reschedule-recurring-daily'] = {
    'task': 'celery_tasks.reschedule_recurring_messages_task',
    'schedule': crontab(hour=2, minute=0),
}