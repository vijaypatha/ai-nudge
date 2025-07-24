# File Path: backend/workflow/campaigns.py
# --- MODIFIED: Implements "safe time" scheduling for AI plans.

import logging
from uuid import UUID, uuid4
from datetime import datetime, timedelta, timezone, time
from sqlmodel import Session
import pytz

from data.database import engine
from data.models.campaign import CampaignBriefing, CampaignStatus
from data.models.message import ScheduledMessage, MessageStatus
from data import crm as crm_service

# --- NEW: Helper function for safe time calculation ---
def _calculate_safe_future_utc(client_timezone_str: str, delay_days: int) -> datetime:
    """
    Calculates a future datetime, defaulting to 10:00 AM in the client's local
    timezone, and returns it as a UTC datetime object.
    """
    try:
        client_tz = pytz.timezone(client_timezone_str)
    except pytz.UnknownTimeZoneError:
        logging.warning(f"CAMPAIGN WORKFLOW: Unknown timezone '{client_timezone_str}', falling back to UTC.")
        client_tz = pytz.utc

    # Get the current time in the client's timezone and add the delay
    now_in_client_tz = datetime.now(client_tz)
    future_date_in_client_tz = now_in_client_tz + timedelta(days=delay_days)
    
    # Set the time to a "safe" 10:00 AM local time
    safe_time = time(10, 0)
    final_local_datetime = future_date_in_client_tz.replace(
        hour=safe_time.hour, 
        minute=safe_time.minute, 
        second=0, 
        microsecond=0
    )
    
    # Convert the final local datetime back to UTC for storage
    return final_local_datetime.astimezone(pytz.utc)


async def approve_and_schedule_precomputed_plan(plan_id: UUID, user_id: UUID) -> CampaignBriefing:
    """
    Approves a campaign plan by creating scheduled messages from its pre-computed drafts.
    Now uses "safe time" recipient-centric scheduling.
    """
    logging.info(f"CAMPAIGN WORKFLOW: Approving pre-computed plan {plan_id} for user {user_id}.")
    with Session(engine) as session:
        plan = crm_service.get_campaign_briefing_by_id(plan_id, user_id, session=session)
        if not plan or not plan.is_plan or plan.status != CampaignStatus.DRAFT:
            raise ValueError("Plan not found or not in a state to be approved.")
        if not plan.client_id:
            raise ValueError("Plan must be associated with a client.")
            
        # --- NEW: Fetch the client to get their timezone ---
        client = crm_service.get_client_by_id(plan.client_id, user_id)
        if not client:
            raise ValueError(f"Client {plan.client_id} not found for plan approval.")
        
        # Use client's timezone, fall back to user's, then UTC
        target_tz = client.timezone or plan.user.timezone or 'UTC'

        steps = plan.key_intel.get("steps", [])
        if not steps:
            raise ValueError("Plan has no steps to schedule.")

        for step in steps:
            generated_draft = step.get("generated_draft")
            if not generated_draft:
                logging.warning(f"CAMPAIGN WORKFLOW: Step '{step.get('name')}' is missing draft. Skipping.")
                continue

            # --- MODIFIED: Use the new safe time calculation helper ---
            scheduled_time_in_utc = _calculate_safe_future_utc(
                client_timezone_str=target_tz,
                delay_days=step.get('delay_days', 0)
            )

            scheduled_message = ScheduledMessage(
                user_id=user_id,
                client_id=plan.client_id,
                parent_plan_id=plan.id,
                content=generated_draft,
                scheduled_at_utc=scheduled_time_in_utc,
                timezone=target_tz, # Store the actual timezone used
                status=MessageStatus.PENDING,
                playbook_touchpoint_id=step.get('name'),
                is_recurring=False
            )
            session.add(scheduled_message)

        plan.status = CampaignStatus.ACTIVE
        session.add(plan)
        session.commit()
        session.refresh(plan)
        logging.info(f"CAMPAIGN WORKFLOW: Approved and scheduled {len(steps)} messages for plan {plan.id}.")
        return plan

# The handle_copilot_action function remains unchanged
async def handle_copilot_action(briefing_id: UUID, action_type: str, user_id: UUID) -> dict:
    # ... (rest of the function is unchanged)
    pass