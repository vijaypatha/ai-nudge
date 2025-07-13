# File Path: backend/workflow/campaigns.py

import logging
import asyncio
from uuid import UUID
from datetime import datetime, timedelta, timezone
from sqlmodel import Session

from data.database import engine
from data.models.campaign import CampaignBriefing, CampaignStatus
from data.models.message import ScheduledMessage, MessageStatus
from data import crm as crm_service
from agent_core.agents import conversation as conversation_agent
from workflow.relationship_playbooks import get_playbook_for_intent

async def _regenerate_plan_from_message(user_id: UUID, client_id: UUID, parent_message_id: UUID, session: Session):
    """
    A helper function to regenerate a campaign plan based on a message.
    This refactors logic from the orchestrator for reuse.
    """
    logging.info(f"CAMPAIGN WORKFLOW: Regenerating plan for client {client_id} from message {parent_message_id}")
    user = crm_service.get_user_by_id(user_id)
    client = crm_service.get_client_by_id(client_id, user_id)
    parent_message = session.get(crm_service.Message, parent_message_id)

    if not all([user, client, parent_message]):
        logging.error("CAMPAIGN WORKFLOW: Could not regenerate plan due to missing user, client, or message.")
        return

    detected_intent = await conversation_agent.detect_conversational_intent(parent_message.content)
    playbook = get_playbook_for_intent(detected_intent) if detected_intent else None

    if playbook:
        logging.info(f"CAMPAIGN WORKFLOW: Intent '{detected_intent}' detected. Creating new plan.")
        tasks = [conversation_agent.draft_campaign_step_message(user, client, step.prompt, step.delay_days) for step in playbook.steps]
        results = await asyncio.gather(*tasks)
        enriched_steps = [
            {**playbook.steps[i].__dict__, 'generated_draft': generated_draft}
            for i, (generated_draft, _) in enumerate(results)
        ]
        new_plan = CampaignBriefing(
            user_id=user_id, client_id=client_id, is_plan=True,
            campaign_type=playbook.intent_type, headline=f"AI-Suggested Plan: {playbook.name}",
            key_intel={"playbook_name": playbook.name, "steps": enriched_steps},
            original_draft="Multi-step plan regenerated from new client info.", status=CampaignStatus.DRAFT,
            parent_message_id=parent_message_id
        )
        crm_service.save_campaign_briefing(new_plan, session=session)
        logging.info(f"CAMPAIGN WORKFLOW: Saved regenerated plan for client {client.id}.")


async def handle_copilot_action(briefing_id: UUID, action_type: str, user_id: UUID) -> dict:
    """
    Handles actions from a Co-Pilot Briefing card, like updating or ending a plan.
    """
    logging.info(f"CAMPAIGN WORKFLOW: Handling Co-Pilot action '{action_type}' for briefing {briefing_id}")
    with Session(engine) as session:
        copilot_briefing = crm_service.get_campaign_briefing_by_id(briefing_id, user_id)
        if not copilot_briefing or copilot_briefing.campaign_type != "co_pilot_briefing":
            raise ValueError("Co-Pilot briefing not found.")

        paused_plan_id_str = copilot_briefing.key_intel.get("paused_plan_id")
        if not paused_plan_id_str:
            raise ValueError("Briefing is missing the ID of the paused plan.")
        
        paused_plan_id = UUID(paused_plan_id_str)
        paused_plan = crm_service.get_campaign_briefing_by_id(paused_plan_id, user_id)
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
            paused_plan.status = CampaignStatus.CANCELLED
            copilot_briefing.status = CampaignStatus.COMPLETED
            session.add(paused_plan)
            session.add(copilot_briefing)
            
            if not copilot_briefing.parent_message_id or not copilot_briefing.client_id:
                raise ValueError("Cannot update plan without parent message or client context.")
            
            await _regenerate_plan_from_message(
                user_id=user_id,
                client_id=copilot_briefing.client_id,
                parent_message_id=copilot_briefing.parent_message_id,
                session=session
            )
            session.commit()
            logging.info(f"CAMPAIGN WORKFLOW: Cancelled old plan {paused_plan_id} and regenerated a new one.")
            return {"status": "success", "action": "updated"}
        
        else:
            raise ValueError(f"Unknown action type: {action_type}")


async def approve_and_schedule_precomputed_plan(plan_id: UUID, user_id: UUID) -> CampaignBriefing:
    """
    Approves a campaign plan by creating scheduled messages from its pre-computed drafts.
    """
    logging.info(f"CAMPAIGN WORKFLOW: Approving pre-computed plan {plan_id} for user {user_id}.")
    with Session(engine) as session:
        plan = crm_service.get_campaign_briefing_by_id(plan_id, user_id)
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

            scheduled_at = datetime.now(timezone.utc) + timedelta(days=step.get('delay_days', 0))
            scheduled_message = ScheduledMessage(
                user_id=user_id,
                client_id=plan.client_id,
                parent_plan_id=plan.id,
                content=generated_draft,
                scheduled_at=scheduled_at.isoformat(),
                status=MessageStatus.PENDING,
                is_recurring=False
            )
            session.add(scheduled_message)
        
        plan.status = CampaignStatus.ACTIVE
        session.add(plan)
        session.commit()
        session.refresh(plan)
        logging.info(f"CAMPAIGN WORKFLOW: Approved and scheduled {len(steps)} messages for plan {plan.id}.")
        return plan