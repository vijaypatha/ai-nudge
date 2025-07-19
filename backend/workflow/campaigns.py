# File Path: backend/workflow/campaigns.py
# --- DEFINITIVE FIX: Implements the "copy-on-update" logic for a seamless user experience.

import logging
from uuid import UUID, uuid4
from datetime import datetime, timedelta, timezone
from sqlmodel import Session

from data.database import engine
from data.models.campaign import CampaignBriefing, CampaignStatus
from data.models.message import ScheduledMessage, MessageStatus
from data import crm as crm_service

async def handle_copilot_action(briefing_id: UUID, action_type: str, user_id: UUID) -> dict:
    """
    Handles actions from a Co-Pilot Briefing card, like updating or ending a plan.
    """
    logging.info(f"CAMPAIGN WORKFLOW: Handling Co-Pilot action '{action_type}' for briefing {briefing_id}")
    with Session(engine) as session:
        copilot_briefing = crm_service.get_campaign_briefing_by_id(briefing_id, user_id, session=session)
        if not copilot_briefing or copilot_briefing.campaign_type != "co_pilot_briefing":
            raise ValueError("Co-Pilot briefing not found.")

        paused_plan_id_str = copilot_briefing.key_intel.get("paused_plan_id")
        if not paused_plan_id_str:
            raise ValueError("Briefing is missing the ID of the paused plan.")
        
        paused_plan_id = UUID(paused_plan_id_str)
        paused_plan = crm_service.get_campaign_briefing_by_id(paused_plan_id, user_id, session=session)
        if not paused_plan:
            raise ValueError("The paused plan could not be found.")

        if action_type == "END_PLAN":
            paused_plan.status = CampaignStatus.COMPLETED
            copilot_briefing.status = CampaignStatus.COMPLETED
            session.add(paused_plan)
            session.add(copilot_briefing)
            session.commit()
            logging.info(f"CAMPAIGN WORKFLOW: Ended plan {paused_plan_id} and completed briefing {briefing_id}.")
            return {"status": "success", "action": "ended"}

        elif action_type == "UPDATE_PLAN":
            # --- NEW LOGIC START ---
            # Instead of re-analyzing a low-intent message, we create a new draft
            # that is an exact copy of the paused plan. This provides a better UX.
            
            # 1. Create a new plan that is a copy of the one that was paused.
            new_plan = CampaignBriefing(
                id=uuid4(), # Give it a new ID
                user_id=paused_plan.user_id,
                client_id=paused_plan.client_id,
                is_plan=True,
                campaign_type=paused_plan.campaign_type,
                headline=paused_plan.headline,
                key_intel=paused_plan.key_intel,
                original_draft=paused_plan.original_draft,
                status=CampaignStatus.DRAFT, # Set it as a new draft
                parent_message_id=copilot_briefing.parent_message_id # Link to the latest message
            )
            
            # 2. Mark the old plan as cancelled and the briefing as completed.
            paused_plan.status = CampaignStatus.CANCELLED
            copilot_briefing.status = CampaignStatus.COMPLETED

            session.add(new_plan)
            session.add(paused_plan)
            session.add(copilot_briefing)
            session.commit()
            
            logging.info(f"CAMPAIGN WORKFLOW: Copied plan {paused_plan.id} to new draft {new_plan.id}.")
            return {"status": "success", "action": "updated"}
            # --- NEW LOGIC END ---
        
        else:
            raise ValueError(f"Unknown action type: {action_type}")


async def approve_and_schedule_precomputed_plan(plan_id: UUID, user_id: UUID) -> CampaignBriefing:
    """
    Approves a campaign plan by creating scheduled messages from its pre-computed drafts.
    """
    logging.info(f"CAMPAIGN WORKFLOW: Approving pre-computed plan {plan_id} for user {user_id}.")
    with Session(engine) as session:
        plan = crm_service.get_campaign_briefing_by_id(plan_id, user_id, session=session)
        if not plan or not plan.is_plan or plan.status != CampaignStatus.DRAFT:
            raise ValueError("Plan not found or not in a state to be approved.")
        if not plan.client_id:
            raise ValueError("Plan must be associated with a client.")

        steps = plan.key_intel.get("steps", [])
        if not steps:
            raise ValueError("Plan has no steps to schedule.")

        for step in steps:
            generated_draft = step.get("generated_draft")
            if not generated_draft:
                logging.warning(f"CAMPAIGN WORKFLOW: Step '{step.get('name')}' is missing a pre-computed draft. Skipping.")
                continue

            # This correctly calculates a future datetime object in UTC.
            scheduled_time_in_utc = datetime.now(timezone.utc) + timedelta(days=step.get('delay_days', 0))

            # --- FIX IS HERE ---
            # The ScheduledMessage object now requires 'scheduled_at_utc' and 'timezone'.
            scheduled_message = ScheduledMessage(
                user_id=user_id,
                client_id=plan.client_id,
                parent_plan_id=plan.id,
                content=generated_draft,
                scheduled_at_utc=scheduled_time_in_utc, # Use the correct field name
                timezone="UTC", # Provide a default value as this is a system-generated plan
                status=MessageStatus.PENDING,
                playbook_touchpoint_id=step.get('name'),
                is_recurring=False
                # Note: Celery task scheduling is handled by a separate process for manually scheduled messages.
                # This function directly saves to the DB; a separate worker will need to pick these up.
            )
            session.add(scheduled_message)

        plan.status = CampaignStatus.ACTIVE
        session.add(plan)
        session.commit()
        session.refresh(plan)
        logging.info(f"CAMPAIGN WORKFLOW: Approved and scheduled {len(steps)} messages for plan {plan.id}.")
        return plan