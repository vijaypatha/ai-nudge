# FILE: backend/celery_tasks.py
# PURPOSE: Defines the background tasks that our Celery worker will run.

import asyncio
import logging

# Use absolute imports to prevent any pathing issues.
# from backend.celery_worker import celery_app
# from backend.integrations.mls.factory import get_mls_client
# from backend.agent_core.brain import nudge_engine
# from backend.data import crm as crm_service

from celery_worker import celery_app
from integrations.mls.factory import get_mls_client
from agent_core.brain import nudge_engine
from data import crm as crm_service

logger = logging.getLogger(__name__)

# This decorator registers the function as a Celery task.
@celery_app.task
def check_mls_for_events_task():
    """
    The main scheduled task to poll the MLS for new events and process them.
    This is the "alarm" that triggers our "Perceive -> Reason" loop.
    """
    logger.info("CELERY TASK: Starting MLS event check...")
    mls_client = get_mls_client()
    if not mls_client:
        logger.error("CELERY TASK FAILED: Could not create MLS client.")
        return

    # Discover events from the last 15 minutes.
    market_events = mls_client.discover_events(minutes_ago=15)
    
    if not market_events:
        logger.info("CELERY TASK: No new market events found.")
        return

    logger.info(f"CELERY TASK: Found {len(market_events)} new market events. Processing...")
    
    # For now, assume a single default user for the background task.
    # In the future, this would handle tasks for multiple users.
    realtor = crm_service.get_user_by_id(crm_service.mock_users_db[0].id)
    if not realtor:
        logger.error("CELERY TASK FAILED: Could not find a default realtor user to process events for.")
        return

    for event in market_events:
        # Since nudge_engine.process_market_event is an async function,
        # we run it within an asyncio event loop.
        asyncio.run(nudge_engine.process_market_event(event, realtor))
    
    logger.info("CELERY TASK: Finished processing market events.")


@celery_app.task
def send_scheduled_message_task(message_id: str):
    """
    (Future Use) This task will be called by the Relationship Planner to send
    a message at a specific time in the future.
    """
    logger.info(f"CELERY TASK: Pretending to send scheduled message -> {message_id}")
    # TODO: Add logic to fetch the message by ID and send it via the communication tool.
    pass

@celery_app.task
def check_for_recency_nudges_task():
    """
    A background task that periodically runs the recency check in the Nudge Engine.
    """
    print("CELERY TASK: Kicking off daily check for recency nudges...")
    try:
        # We need to run our async function from the synchronous Celery task.
        asyncio.run(nudge_engine.generate_recency_nudges())
        print("CELERY TASK: Recency nudge check completed successfully.")
    except Exception as e:
        print(f"CELERY TASK ERROR: Recency nudge check failed: {e}")