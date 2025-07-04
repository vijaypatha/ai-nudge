# FILE: backend/celery_tasks.py
# PURPOSE: Defines the background tasks that our Celery worker will run.
# --- CORRECTED to call the correct nudge engine functions ---

import asyncio
import logging
import uuid

from celery_worker import celery_app
from agent_core.brain import nudge_engine
from data import crm as crm_service
from agent_core.brain import nudge_engine, relationship_planner
from data.models.message import MessageStatus
from datetime import timedelta
from celery.schedules import crontab
from workflow.relationship_playbooks import ALL_PLAYBOOKS

logger = logging.getLogger(__name__)

@celery_app.task
def check_mls_for_events_task():
    """
    The main scheduled task to poll the MLS for new events and process them.
    This is the "alarm" that triggers our "Perceive -> Reason" loop.
    """
    logger.info("CELERY TASK: Starting MLS event check...")
    
    # --- FIX: Use the main orchestrator function from nudge_engine ---
    # This function already handles getting the MLS client and fetching all event types.
    try:
        # Get the default user to run the scan for.
        realtor_id = uuid.UUID("a8c6f1d7-8f7a-4b6e-8b0f-9e5a7d6c5b4a")
        realtor = crm_service.get_user_by_id(realtor_id)
        if not realtor:
            logger.error("CELERY TASK FAILED: Could not find a default realtor user.")
            return

        # Run the async function from our synchronous Celery task.
        # This single function call replaces the old, incorrect logic.
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
        # --- FIX: Fetch the realtor and pass it to the function ---
        # The generate_recency_nudges function requires the realtor object.
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
def send_scheduled_message_task(message_id: str):
    """
    (Future Use) This task will be called by the Relationship Planner to send
    a message at a specific time in the future.
    """
    logger.info(f"CELERY TASK: Pretending to send scheduled message -> {message_id}")
    # TODO: Add logic to fetch the message by ID and send it via the communication tool.
    pass

celery_app.task
def reschedule_recurring_messages_task():
    """
    Runs daily. Finds SENT recurring messages and schedules the next one.
    """
    print("RECURRENCE ENGINE: Starting daily scan for recurring messages...")
    all_sent_messages = crm_service.get_all_sent_scheduled_messages() # You'll need to create this function in crm.py
    
    # Flatten all playbooks into a dictionary for easy lookup
    all_touchpoints = {}
    for playbook in relationship_planner.ALL_PLAYBOOKS:
        for touchpoint in playbook["touchpoints"]:
            if "id" in touchpoint:
                all_touchpoints[touchpoint["id"]] = touchpoint

    for message in all_sent_messages:
        if message.is_recurring and message.playbook_touchpoint_id:
            touchpoint = all_touchpoints.get(message.playbook_touchpoint_id)
            if not touchpoint: continue

            # Check if a follow-up is already scheduled to prevent duplicates
            if crm_service.has_future_recurring_message(message.client_id, message.playbook_touchpoint_id):
                continue
            
            # Calculate next date and schedule
            frequency_days = touchpoint.get("recurrence", {}).get("frequency_days", 90)
            next_date = message.sent_at + timedelta(days=frequency_days)
            
            realtor = crm_service.get_user_by_id(touchpoint.get("user_id")) # Assuming user_id is on touchpoint
            # This is a simplified call; in reality, you'd re-invoke the planner or a drafter
            relationship_planner._schedule_message_from_touchpoint(message.client, realtor, touchpoint, next_date)
    
    print("RECURRENCE ENGINE: Daily scan complete.")


# Add the new task to the Celery Beat schedule to run daily at 2 AM
celery_app.conf.beat_schedule['reschedule-recurring-daily'] = {
    'task': 'celery_tasks.reschedule_recurring_messages_task',
    'schedule': crontab(hour=2, minute=0),
}