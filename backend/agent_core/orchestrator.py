# File Path: backend/agent_core/orchestrator.py
# --- MODIFIED: Fixes broadcast method call and adds AI tag processing ---

import logging
import asyncio
import uuid
import json
from api.websocket_manager import manager as websocket_manager
from typing import Dict, Any, List, Optional
from sqlmodel import Session, select

from data.database import engine
from data.models.user import User
from data.models.client import Client

from data.models.message import (
    Message,
    MessageDirection,
    MessageStatus,
    MessageSource,
    MessageSenderType,
)
from data.models.campaign import CampaignBriefing, CampaignStatus, CoPilotAction
from data import crm as crm_service
from agent_core.agents import conversation as conversation_agent
from workflow.relationship_playbooks import get_playbook_for_intent
from integrations import twilio_outgoing

async def handle_incoming_message(client_id: uuid.UUID, incoming_message: Message, user: User) -> Dict[str, Any]:
    """
    Processes an incoming message, pre-computes campaign drafts, and handles the "Pause & Propose" logic.
    This function is now vertically agnostic.
    """
    logging.info(f"ORCHESTRATOR: Handling incoming message from client {client_id}...")
    try:
        with Session(engine) as session:
            # --- "PAUSE & PROPOSE" LOGIC ---
            active_plan_statement = select(CampaignBriefing).where(
                CampaignBriefing.client_id == client_id,
                CampaignBriefing.user_id == user.id,
                CampaignBriefing.status == CampaignStatus.ACTIVE,
                CampaignBriefing.is_plan == True
            )
            active_plan_to_pause = session.exec(active_plan_statement).first()
            
            if active_plan_to_pause:
                logging.info(f"ORCHESTRATOR: Active plan {active_plan_to_pause.id} found. Pausing.")
                active_plan_to_pause.status = CampaignStatus.PAUSED
                session.add(active_plan_to_pause)
                crm_service.cancel_scheduled_messages_for_plan(active_plan_to_pause.id, user.id, session)

                co_pilot_briefing = CampaignBriefing(
                    user_id=user.id, client_id=client_id, parent_message_id=incoming_message.id,
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
                # --- NOTIFY FRONTEND OF NEW INTEL ---
                try:
                    intel_update_notification = { "type": "INTEL_UPDATED", "clientId": str(client_id) }
                    # [FIX] Corrected method name and argument
                    await websocket_manager.broadcast_json_to_client(
                        client_id=str(client_id),
                        data=intel_update_notification
                    )
                    logging.info(f"ORCHESTRATOR: Broadcasted INTEL_UPDATED event for client {client_id}")
                except Exception as e:
                    logging.error(f"ORCHESTRATOR: Failed to broadcast INTEL_UPDATED event. Error: {e}")
                return {"status": "paused_and_proposed"}

            # --- FAQ CHECK ---
            content_lower = incoming_message.content.lower()
            if content_lower.endswith('?') and len(content_lower.split()) < 7:
                logging.info(f"ORCHESTRATOR: Message from client {client_id} identified as potential FAQ. Skipping standard co-pilot generation.")
                session.commit()
                return {"status": "processed_as_faq"}

            # --- STANDARD INCOMING MESSAGE LOGIC ---
            crm_service.update_last_interaction(client_id, user_id=user.id, session=session)
            conversation_history = crm_service.get_recent_messages(client_id=client_id, user_id=user.id, limit=10)
            client = crm_service.get_client_by_id(client_id, user_id=user.id)
            if not client: raise ValueError(f"Client {client_id} not found.")

            # 1. Generate immediate recommendations (includes drafts AND tags)
            recommendation_data = await conversation_agent.generate_recommendation_slate(
                user, client_id, incoming_message, conversation_history
            )

            # [NEW] Check for extracted tags and add them to the client record
            if recommendation_data and recommendation_data.get("tags"):
                tags_to_add = recommendation_data.get("tags")
                if isinstance(tags_to_add, list) and len(tags_to_add) > 0:
                    logging.info(f"ORCHESTRATOR: Extracted tags from message: {tags_to_add}. Updating client intel.")
                    await crm_service.update_client_intel(client_id=client_id, user_id=user.id, tags_to_add=tags_to_add)

            # Process recommendations for the UI
            if recommendation_data:
                draft_rec = next((r for r in recommendation_data.get("recommendations", []) if r.get("type") == "SUGGEST_DRAFT"), None)
                draft_text = draft_rec["payload"]["text"] if draft_rec and draft_rec.get("payload") else "Could not generate draft."
                immediate_slate = CampaignBriefing(
                    user_id=user.id, client_id=client_id, parent_message_id=incoming_message.id, is_plan=False,
                    campaign_type="inbound_response_recommendation", headline="AI Suggestions",
                    key_intel=recommendation_data, original_draft=draft_text, status=CampaignStatus.DRAFT
                )
                crm_service.save_campaign_briefing(immediate_slate, session=session)
                logging.info(f"ORCHESTRATOR: Saved immediate recommendation slate.")

            # 2. Detect intent and create a long-term plan if applicable
            detected_intent = await conversation_agent.detect_conversational_intent(incoming_message.content, user)
            playbook = get_playbook_for_intent(detected_intent, user.vertical) if detected_intent else None

            if playbook:
                logging.info(f"ORCHESTRATOR: Intent '{detected_intent}' detected for '{user.vertical}' vertical. Pre-computing draft campaign plan.")
                tasks = []
                for step in playbook.steps:
                    tasks.append(conversation_agent.draft_campaign_step_message(user, client, step.prompt, step.delay_days))
                
                results = await asyncio.gather(*tasks)
                enriched_steps = []
                for i, (generated_draft, _) in enumerate(results):
                    step_data = playbook.steps[i].__dict__
                    step_data['generated_draft'] = generated_draft
                    enriched_steps.append(step_data)
                
                new_plan = CampaignBriefing(
                    user_id=user.id, client_id=client_id, is_plan=True,
                    campaign_type=playbook.intent_type, headline=f"AI-Suggested Plan: {playbook.name}",
                    key_intel={"playbook_name": playbook.name, "steps": enriched_steps},
                    original_draft="Multi-step plan with pre-computed drafts.", status=CampaignStatus.DRAFT,
                    parent_message_id=incoming_message.id
                )
                crm_service.save_campaign_briefing(new_plan, session=session)
                logging.info(f"ORCHESTRATOR: Saved new pre-computed Nudge Plan.")

            session.commit()

            # --- NOTIFY FRONTEND OF NEW INTEL (STANDARD PATH) ---
            if recommendation_data or playbook:
                try:
                    intel_update_notification = { "type": "INTEL_UPDATED", "clientId": str(client_id) }
                    # [FIX] Corrected method name and argument
                    await websocket_manager.broadcast_json_to_client(
                        client_id=str(client_id),
                        data=intel_update_notification
                    )
                    logging.info(f"ORCHESTRATOR: Broadcasted INTEL_UPDATED event for client {client_id}")
                except Exception as e:
                    logging.error(f"ORCHESTRATOR: Failed to broadcast INTEL_UPDATED event. Error: {e}")

    except Exception as e:
        logging.error(f"ORCHESTRATOR: Unhandled error in handle_incoming_message: {e}", exc_info=True)
        return {"status": "error"}

    return {"status": "processed"}


async def orchestrate_send_message_now(
    client_id: uuid.UUID, 
    content: str, 
    user_id: uuid.UUID,
    source: MessageSource = MessageSource.MANUAL
) -> Optional[Message]:
    """
    Sends a message immediately, logs it with correct source, and returns the created message object.
    """
    logging.info(f"ORCHESTRATOR: Orchestrating immediate send for client {client_id} (Source: {source.value})")

    with Session(engine) as session:
        # Slate management logic remains, no changes needed here.
        all_active_slates = crm_service.get_all_active_slates_for_client(client_id, user_id, session)
        immediate_slate = next((s for s in all_active_slates if not s.is_plan), None)
        if immediate_slate:
            logging.info(f"ORCHESTRATOR: Message sent, marking active slate {immediate_slate.id} as 'completed'.")
            crm_service.update_slate_status(immediate_slate.id, CampaignStatus.COMPLETED, user_id, session)

        # User and Client retrieval logic remains, no changes needed here.
        user = crm_service.get_user_by_id(user_id)
        client = crm_service.get_client_by_id(client_id, user_id=user_id)
        if not user or not user.twilio_phone_number:
            logging.error(f"ORCHESTRATOR ERROR: User {user_id} not found or has no Twilio number.")
            return None
        if not client or not client.phone:
            logging.error(f"ORCHESTRATOR ERROR: Client {client_id} not found for user {user_id} or has no phone number.")
            return None

        # Sending logic remains, no changes needed here.
        first_name = client.full_name.strip().split(' ')[0]
        personalized_content = content.replace("[Client Name]", first_name)
        was_sent = twilio_outgoing.send_sms(from_number=user.twilio_phone_number, to_number=client.phone, body=personalized_content)

        if not was_sent:
            logging.error(f"ORCHESTRATOR: Failed to send SMS for client {client_id}. Message will not be logged.")
            # We do not commit session changes if SMS fails
            return None

        # --- REVISED MESSAGE LOGGING ---
        message_log = Message(
            user_id=user_id,
            client_id=client_id,
            content=personalized_content,
            direction=MessageDirection.OUTBOUND,
            status=MessageStatus.SENT,
            source=source, # Use the dynamic source parameter
            sender_type=MessageSenderType.USER,
        )
        session.add(message_log)
        crm_service.update_last_interaction(client_id, user_id=user_id, session=session)

        session.commit()
        session.refresh(message_log) # Refresh to get DB-generated values like created_at

        logging.info(f"ORCHESTRATOR: Database updated for message to client {client_id}.")
        return message_log