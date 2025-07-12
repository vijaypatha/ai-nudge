# backend/workflow/campaigns.py
# --- NEW FILE ---

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

async def approve_and_generate_campaign_messages(plan_id: UUID, user_id: UUID) -> CampaignBriefing:
    """
    Approves a campaign plan, generates the actual message drafts for each step using AI,
    and saves them as scheduled messages.
    """
    logging.info(f"CAMPAIGN WORKFLOW: Starting approval process for plan {plan_id} for user {user_id}.")
    
    with Session(engine) as session:
        plan = crm_service.get_campaign_briefing_by_id(plan_id, user_id)
        if not plan or not plan.is_plan:
            raise ValueError("Campaign plan not found or briefing is not a plan.")
        
        if plan.status != CampaignStatus.DRAFT:
            raise ValueError(f"Campaign plan is not in a draft state. Current status: {plan.status}")

        if not plan.client_id:
            raise ValueError("Campaign plan must be associated with a client.")

        client = crm_service.get_client_by_id(plan.client_id, user_id)
        if not client:
            raise ValueError("Client not found for campaign plan.")

        user = crm_service.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found.")

        steps = plan.key_intel.get("steps", [])
        logging.info(f"CAMPAIGN WORKFLOW: Plan '{plan.headline}' has {len(steps)} steps to process.")

        tasks = []
        for step in steps:
            prompt = step.get("prompt")
            delay_days = step.get("delay_days", 0)
            
            if not prompt:
                logging.warning(f"CAMPAIGN WORKFLOW: Step '{step.get('name')}' has no prompt. Skipping.")
                continue

            # Schedule the AI draft generation for each step to run concurrently
            tasks.append(
                conversation_agent.draft_campaign_step_message(
                    realtor=user,
                    client=client,
                    prompt=prompt,
                    delay_days=delay_days
                )
            )
        
        # Run all AI draft generation tasks in parallel
        generated_messages = await asyncio.gather(*tasks)

        for content, delay_days in generated_messages:
            scheduled_at = datetime.now(timezone.utc) + timedelta(days=delay_days)
            scheduled_message = ScheduledMessage(
                user_id=user_id,
                client_id=client.id,
                parent_plan_id=plan.id,
                content=content,
                scheduled_at=scheduled_at.isoformat(),
                status=MessageStatus.PENDING,
                is_recurring=False
            )
            session.add(scheduled_message)
            logging.info(f"CAMPAIGN WORKFLOW: Scheduled message for client {client.id} at {scheduled_at}.")
        
        plan.status = CampaignStatus.ACTIVE
        session.add(plan)
        
        session.commit()
        session.refresh(plan)

        logging.info(f"CAMPAIGN WORKFLOW: Successfully approved and scheduled all messages for plan {plan.id}.")
        return plan