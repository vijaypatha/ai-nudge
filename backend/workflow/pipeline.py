# backend/workflow/pipeline.py
import logging
import asyncio
from uuid import uuid4
from sqlmodel import Session, select

from data import crm as crm_service
from integrations.mls.factory import get_mls_client
from data.models.user import User
from data.models.event import MarketEvent, GlobalMlsEvent
from data.models.resource import Resource, ResourceType, ResourceStatus
from data.database import engine

logger = logging.getLogger(__name__)


async def process_global_events_for_user(user: User, global_events: list[GlobalMlsEvent]):
    """
    MODIFIED: Now creates Resource records and then triggers a single,
    consolidated matching process for all new resources.
    """
    from data.models.resource import Resource, ResourceType, ResourceStatus
    from agent_core.brain import nudge_engine

    logger.info(f"PIPELINE: Processing {len(global_events)} global events for user {user.id}...")
    newly_created_resources = []
    
    with Session(engine) as db_session:
        for detached_event in global_events:
            try:
                global_event = db_session.merge(detached_event)
                payload = global_event.raw_payload

                resource = crm_service.get_resource_by_entity_id(global_event.listing_key, db_session)
                if not resource:
                    resource = Resource(
                        user_id=user.id,
                        resource_type=ResourceType.PROPERTY,
                        entity_id=global_event.listing_key,
                        status=ResourceStatus.ACTIVE,
                        attributes=payload
                    )
                    db_session.add(resource)
                    db_session.flush()
                    newly_created_resources.append(resource)
            except Exception as e:
                logger.error(f"PIPELINE: Failed to create resource from event {detached_event.listing_key}. Error: {e}", exc_info=True)
                db_session.rollback()

        if newly_created_resources:
            logger.info(f"PIPELINE: Created {len(newly_created_resources)} new resources. Triggering consolidated matching.")
            # --- THIS IS THE KEY ---
            # It now calls our new, correct function to handle consolidation.
            await nudge_engine.find_and_update_matches_for_all_clients(user, newly_created_resources, db_session)
        else:
            logger.info("PIPELINE: No new resources were created from this batch of events.")

        db_session.commit()


async def run_main_opportunity_pipeline(minutes_ago: int | None = None):
    """
    The main production pipeline, implementing the Global Event Pool strategy.
    """
    logger.info("PIPELINE: Starting main pipeline run (Global Pool Strategy)...")
    try:
        first_user = crm_service.get_first_onboarded_user()
        if not first_user:
            logger.info("PIPELINE: No active users found. Ending run.")
            return
        
        data_source_client = get_mls_client(first_user)
        if not data_source_client:
            logger.warning("PIPELINE: Could not initialize MLS client.")
            return

        lookback = minutes_ago or 125
        logger.info(f"PIPELINE: Fetching market events from MLS API (lookback: {lookback} minutes)...")
        raw_events = data_source_client.get_events(minutes_ago=lookback)
        logger.info(f"PIPELINE: Fetched {len(raw_events)} raw events from API.")

    except Exception as e:
        logger.error(f"PIPELINE: Failed to fetch market events from MLS API. Error: {e}", exc_info=True)
        return

    if not raw_events:
        logger.info("PIPELINE: No new market events found from API. Ending run.")
        return

    unique_raw_events = {event.entity_id: event for event in raw_events}.values()
    
    newly_added_events = []
    source_id = "flexmls_reso_default"
    
    with Session(engine) as session:
        existing_keys = set(session.exec(
            select(GlobalMlsEvent.listing_key).where(GlobalMlsEvent.listing_key.in_([e.entity_id for e in unique_raw_events]))
        ).all())
        
        events_to_add = [
            GlobalMlsEvent(
                source_id=source_id,
                listing_key=event.entity_id,
                raw_payload=event.raw_data,
                event_timestamp=event.raw_data.get("ModificationTimestamp")
            ) for event in unique_raw_events if event.entity_id not in existing_keys
        ]
        
        if events_to_add:
            session.add_all(events_to_add)
            session.commit()
            newly_added_events = events_to_add
            logger.info(f"PIPELINE: Saved {len(newly_added_events)} new unique events to the global pool.")
        else:
            logger.info("PIPELINE: No new unique events to process. Ending run.")
            return

    all_users = crm_service.get_all_users()
    realtor_users = [u for u in all_users if u.onboarding_complete and u.vertical == "real_estate"]

    if not realtor_users:
        logger.info("PIPELINE: No active users to process new events for. Ending run.")
        return

    await asyncio.gather(*(process_global_events_for_user(user, newly_added_events) for user in realtor_users))
    logger.info("PIPELINE: Main opportunity pipeline run finished.")