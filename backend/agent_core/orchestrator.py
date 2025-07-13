# File Path: backend/agent_core/orchestrator.py

import logging
import asyncio
import uuid
from typing import Dict, Any, List
from sqlmodel import Session, select

from data.database import engine
from data.models.user import User
from data.models.client import Client
from data.models.message import Message
from data.models.campaign import CampaignBriefing, CampaignStatus, CoPilotAction
from data import crm as crm_service
from agent_core.agents import conversation as conversation_agent
from workflow.relationship_playbooks import get_playbook_for_intent
from integrations import twilio_outgoing

async def handle_incoming_message(client_id: uuid.UUID, incoming_message: Message, realtor: User) -> Dict[str, Any]:
    """
    Processes an incoming message, pre-computes campaign drafts, and handles the "Pause & Propose" logic.
    """
    logging.info(f"ORCHESTRATOR: Handling incoming message from client {client_id}...")
    try:
        with Session(engine) as session:
            # --- "PAUSE & PROPOSE" LOGIC ---
            active_plan_statement = select(CampaignBriefing).where(
                CampaignBriefing.client_id == client_id,
                CampaignBriefing.user_id == realtor.id,
                CampaignBriefing.status == CampaignStatus.ACTIVE,
                CampaignBriefing.is_plan == True
            )
            active_plan_to_pause = session.exec(active_plan_statement).first()
            
            if active_plan_to_pause:
                logging.info(f"ORCHESTRATOR: Active plan {active_plan_to_pause.id} found. Pausing.")
                active_plan_to_pause.status = CampaignStatus.PAUSED
                session.add(active_plan_to_pause)
                crm_service.cancel_scheduled_messages_for_plan(active_plan_to_pause.id, realtor.id, session)

                co_pilot_briefing = CampaignBriefing(
                    user_id=realtor.id, client_id=client_id, parent_message_id=incoming_message.id,
                    is_plan=False, campaign_type="co_pilot_briefing", headline="Co-Pilot Suggestion",
                    key_intel={
                        "paused_plan_id": str(active_plan_to_pause.id),
                        "paused_plan_headline": active_plan_to_pause.headline,
                        "actions": [
                            CoPilotAction(type="UPDATE_PLAN", label="Update plan from new info").model_dump(),
                            CoPilotAction(type="END_PLAN", label="End plan (goal met)").model_dump(),
                        ]
                    },
                    original_draft=f"Your client replied, so I've paused the '{active_plan_to_pause.headline}' campaign. I can generate a new plan based on their message.",
                    status=CampaignStatus.DRAFT
                )
                crm_service.save_campaign_briefing(co_pilot_briefing, session=session)
                session.commit()
                return {"status": "paused_and_proposed"}

            # --- FAQ CHECK (New Requirement) ---
            # A simple placeholder check. If a message is short and ends with a question mark,
            # we can bypass the expensive AI generation for now.
            content_lower = incoming_message.content.lower()
            if content_lower.endswith('?') and len(content_lower.split()) < 7:
                logging.info(f"ORCHESTRATOR: Message from client {client_id} identified as potential FAQ. Skipping standard co-pilot generation.")
                session.commit() # Save the incoming message
                return {"status": "processed_as_faq"}

            # --- STANDARD INCOMING MESSAGE LOGIC ---
            crm_service.update_last_interaction(client_id, user_id=realtor.id, session=session)
            conversation_history = crm_service.get_recent_messages(client_id=client_id, user_id=realtor.id, limit=10)
            client = crm_service.get_client_by_id(client_id, user_id=realtor.id)
            if not client: raise ValueError(f"Client {client_id} not found.")

            # 1. Always generate and save the immediate recommendation slate.
            recommendation_data = await conversation_agent.generate_recommendation_slate(
                realtor, client_id, incoming_message, conversation_history
            )
            if recommendation_data:
                draft_rec = next((r for r in recommendation_data.get("recommendations", []) if r.get("type") == "SUGGEST_DRAFT"), None)
                draft_text = draft_rec["payload"]["text"] if draft_rec and draft_rec.get("payload") else "Could not generate draft."
                immediate_slate = CampaignBriefing(
                    user_id=realtor.id, client_id=client_id, parent_message_id=incoming_message.id, is_plan=False,
                    campaign_type="inbound_response_recommendation", headline="AI Suggestions",
                    key_intel=recommendation_data, original_draft=draft_text, status=CampaignStatus.DRAFT
                )
                crm_service.save_campaign_briefing(immediate_slate, session=session)
                logging.info(f"ORCHESTRATOR: Saved immediate recommendation slate.")

            # 2. Separately, detect intent and create a pre-computed plan if needed.
            detected_intent = await conversation_agent.detect_conversational_intent(incoming_message.content)
            playbook = get_playbook_for_intent(detected_intent) if detected_intent else None

            if playbook:
                logging.info(f"ORCHESTRATOR: Intent '{detected_intent}' detected. Pre-computing draft campaign plan.")
                tasks = []
                for step in playbook.steps:
                    tasks.append(conversation_agent.draft_campaign_step_message(realtor, client, step.prompt, step.delay_days))
                
                results = await asyncio.gather(*tasks)
                enriched_steps = []
                for i, (generated_draft, _) in enumerate(results):
                    step_data = playbook.steps[i].__dict__
                    step_data['generated_draft'] = generated_draft
                    enriched_steps.append(step_data)
                
                new_plan = CampaignBriefing(
                    user_id=realtor.id, client_id=client_id, is_plan=True,
                    campaign_type=playbook.intent_type, headline=f"AI-Suggested Plan: {playbook.name}",
                    key_intel={"playbook_name": playbook.name, "steps": enriched_steps},
                    original_draft="Multi-step plan with pre-computed drafts.", status=CampaignStatus.DRAFT,
                    parent_message_id=incoming_message.id
                )
                crm_service.save_campaign_briefing(new_plan, session=session)
                logging.info(f"ORCHESTRATOR: Saved new pre-computed Nudge Plan.")

            session.commit()
    except Exception as e:
        logging.error(f"ORCHESTRATOR: Unhandled error in handle_incoming_message: {e}", exc_info=True)
        return {"status": "error"}

    return {"status": "processed"}


async def orchestrate_send_message_now(client_id: uuid.UUID, content: str, user_id: uuid.UUID) -> bool:
    logging.info(f"ORCHESTRATOR: Orchestrating immediate send for client {client_id} for user {user_id}")
    with Session(engine) as session:
        all_active_slates = crm_service.get_all_active_slates_for_client(client_id, user_id, session)
        immediate_slate = next((s for s in all_active_slates if not s.is_plan), None)
        if immediate_slate:
            logging.info(f"ORCHESTRATOR: Message sent, marking active slate {immediate_slate.id} as 'completed'.")
            crm_service.update_slate_status(immediate_slate.id, CampaignStatus.COMPLETED, user_id, session)
        session.commit()
    user = crm_service.get_user_by_id(user_id)
    client = crm_service.get_client_by_id(client_id, user_id=user_id)
    if not user or not user.twilio_phone_number:
        logging.error(f"ORCHESTRATOR ERROR: User {user_id} not found or has no Twilio number.")
        return False
    if not client or not client.phone:
        logging.error(f"ORCHESTRATOR ERROR: Client {client_id} not found for user {user_id} or has no phone number.")
        return False
    first_name = client.full_name.strip().split(' ')[0]
    personalized_content = content.replace("[Client Name]", first_name)
    was_sent = twilio_outgoing.send_sms(from_number=user.twilio_phone_number, to_number=client.phone, body=personalized_content)
    if was_sent:
        crm_service.update_last_interaction(client_id, user_id=user_id)
    return was_sent