# backend/workflow/pipeline.py
# This file contains the core logic for the production data pipeline.

import logging
import asyncio
from sqlmodel import Session
from uuid import uuid4

from data import crm as crm_service
from agent_core.brain import nudge_engine
from integrations.mls.factory import get_mls_client
from data.models.user import UserType
from data.models.event import MarketEvent
from data.database import engine

# Configure logging
logger = logging.getLogger(__name__)

async def run_main_opportunity_pipeline():
    """
    The main production pipeline. It finds all active users, checks for new
    market events from their integrated data source (like an MLS), and
    processes those events to generate Nudges.
    """
    logger.info("PIPELINE: Starting main opportunity pipeline run...")
    
    # 1. Get all users who can have market events (e.g., realtors)
    all_users = crm_service.get_all_users()
    realtor_users = [user for user in all_users if user.user_type == UserType.REALTOR and user.onboarding_complete]
    
    if not realtor_users:
        logger.info("PIPELINE: No active realtors found. Ending pipeline run.")
        return

    logger.info(f"PIPELINE: Found {len(realtor_users)} active realtor(s) to process.")

    # 2. Process events for each user
    for user in realtor_users:
        logger.info(f"PIPELINE: Processing events for user {user.id} ({user.full_name})...")
        try:
            # 3. Initialize the correct data source client (e.g., FlexMLS RESO)
            mls_client = get_mls_client(user)
            if not mls_client:
                logger.warning(f"PIPELINE: Could not get MLS client for user {user.id}. Skipping.")
                continue

            # 4. Fetch recent market events from the live API
            # This looks for any changes in the last 7 days (10080 minutes).
            # MLS properties typically stay active for days/weeks, not minutes.
            # The get_events method is part of the MlsApiInterface
            market_events = mls_client.get_events(minutes_ago=10080)
            
            if not market_events:
                logger.info(f"PIPELINE: No new market events found for user {user.id}.")
                continue

            logger.info(f"PIPELINE: Found {len(market_events)} new market event(s) for user {user.id}.")
            
            # 5. Process each event through the Nudge Engine within a single session
            with Session(engine) as db_session:
                for event in market_events:
                    logger.info(f"PIPELINE: Processing event {event.event_type} (Entity: {event.entity_id}) for user {user.id}.")
                    
                    # Convert Event to MarketEvent for the nudge engine
                    market_event = MarketEvent(
                        id=uuid4(),
                        user_id=user.id,
                        event_type=event.event_type,
                        entity_id=event.entity_id,
                        entity_type="property",
                        payload=event.raw_data,  # Convert raw_data to payload
                        market_area="default"
                    )
                    
                    # The nudge engine expects an async call, so we await it
                    await nudge_engine.process_market_event(event=market_event, user=user, db_session=db_session)
                
                db_session.commit() # Commit all changes for this user at once

        except Exception as e:
            logger.error(f"PIPELINE: Failed to process events for user {user.id}. Error: {e}", exc_info=True)
            # Continue to the next user even if one fails
            continue

    logger.info("PIPELINE: Main opportunity pipeline run finished.")