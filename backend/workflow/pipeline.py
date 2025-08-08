# backend/workflow/pipeline.py
# --- FINAL VERSION: Adds de-duplication for the incoming API batch ---

import logging
import asyncio
from datetime import datetime
from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError
from uuid import uuid4

from data import crm as crm_service
from agent_core.brain import nudge_engine
from integrations.mls.factory import get_mls_client
from data.models.user import User
from data.models.event import MarketEvent, GlobalMlsEvent
from data.database import engine

# Configure logging
logger = logging.getLogger(__name__)


async def process_global_events_for_user(user: User, global_events: list[GlobalMlsEvent]):
    """
    Processes a batch of global events for a single user, creating user-specific
    MarketEvents and generating nudges with resilient transaction handling.
    """
    logger.info(f"PIPELINE: Processing {len(global_events)} global events for user {user.id} ({user.full_name})...")
    
    # --- THIS IS THE FIX ---
    # We now handle transactions on a per-event basis. This ensures that a single
    # failing event does not cause successfully created campaigns to be lost.
    for detached_event in global_events:
        try:
            with Session(engine) as db_session:
                # Re-attach the event object to the current session
                global_event = db_session.merge(detached_event)
                
                market_event_record = MarketEvent(
                    id=uuid4(),
                    user_id=user.id,
                    event_type="new_listing", # This could be made more dynamic later
                    entity_id=global_event.listing_key,
                    entity_type="property",
                    payload=global_event.raw_payload,
                    market_area="default",
                    status="pending"
                )
                db_session.add(market_event_record)
                
                # The nudge_engine will add the new campaign to the session
                await nudge_engine.process_market_event(
                    event=market_event_record, user=user, db_session=db_session
                )
                
                # Commit after each event is fully processed
                db_session.commit()
                logger.info(f"PIPELINE: Successfully processed and committed event {global_event.listing_key} for user {user.id}.")

        except Exception as e:
            # Log the specific event that failed and continue to the next one.
            logger.error(f"PIPELINE: Failed to process event {detached_event.listing_key} for user {user.id}. Error: {e}", exc_info=True)
            # A rollback is handled implicitly by the 'with Session...' block exiting on error.
    # --- END OF FIX ---


async def run_main_opportunity_pipeline(minutes_ago: int | None = None):
    """
    The main production pipeline, implementing the Global Event Pool strategy.
    """
    logger.info("PIPELINE: Starting main pipeline run (Global Pool Strategy)...")

    try:
        first_user = crm_service.get_first_onboarded_user()
        if not first_user:
            logger.info("PIPELINE: No active users found to initialize MLS client. Ending run.")
            return
        
        data_source_client = get_mls_client(first_user)
        if not data_source_client:
            logger.warning("PIPELINE: Could not initialize MLS client. No events will be fetched.")
            return

        lookback = minutes_ago or 65
        logger.info(f"PIPELINE: Fetching market events from MLS API (lookback: {lookback} minutes)...")
        raw_events = data_source_client.get_events(minutes_ago=lookback)
        logger.info(f"PIPELINE: Fetched {len(raw_events)} raw events from API.")

    except Exception as e:
        logger.error(f"PIPELINE: Failed to fetch market events from MLS API. Error: {e}", exc_info=True)
        return

    if not raw_events:
        logger.info("PIPELINE: No new market events found from API. Ending run.")
        return

    # --- THIS IS THE FINAL FIX ---
    # De-duplicate the incoming batch from the API before any processing.
    unique_raw_events = []
    seen_keys = set()
    for event in raw_events:
        if event.entity_id not in seen_keys:
            unique_raw_events.append(event)
            seen_keys.add(event.entity_id)
    
    if len(raw_events) != len(unique_raw_events):
        logger.warning(f"PIPELINE: De-duplicated incoming batch from {len(raw_events)} to {len(unique_raw_events)} events.")
    # --- END OF FIX ---

    newly_added_events = []
    source_id = "flexmls_reso_default"
    
    with Session(engine) as session:
        raw_event_keys = {event.entity_id for event in unique_raw_events}
        
        statement = select(GlobalMlsEvent.listing_key).where(
            GlobalMlsEvent.source_id == source_id,
            GlobalMlsEvent.listing_key.in_(raw_event_keys)
        )
        existing_keys = set(session.exec(statement).all())
        logger.info(f"PIPELINE: Found {len(existing_keys)} events that already exist in the database.")

        events_to_add = []
        for event in unique_raw_events:
            if event.entity_id not in existing_keys:
                new_global_event = GlobalMlsEvent(
                    source_id=source_id,
                    listing_key=event.entity_id,
                    raw_payload=event.raw_data,
                    event_timestamp=event.raw_data.get("ModificationTimestamp", datetime.utcnow())
                )
                events_to_add.append(new_global_event)
        
        if events_to_add:
            session.add_all(events_to_add)
            session.commit()
            for event in events_to_add:
                session.refresh(event)
            newly_added_events = events_to_add

    if not newly_added_events:
        logger.info("PIPELINE: No new unique events to process. Ending run.")
        return

    logger.info(f"PIPELINE: Saved {len(newly_added_events)} new unique events to the global pool.")

    all_users = crm_service.get_all_users()
    realtor_users = [u for u in all_users if u.onboarding_complete and u.vertical == "real_estate"]

    if not realtor_users:
        logger.info("PIPELINE: No active users to process new events for. Ending run.")
        return

    logger.info(f"PIPELINE: Found {len(realtor_users)} active users to process {len(newly_added_events)} events for.")
    
    for user in realtor_users:
        await process_global_events_for_user(user, newly_added_events)

    logger.info("PIPELINE: Main opportunity pipeline run finished.")