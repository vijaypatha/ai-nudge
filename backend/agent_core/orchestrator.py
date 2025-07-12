# backend/agent_core/orchestrator.py
# --- MODIFIED: Upgraded to manage the recommendation slate lifecycle.

from typing import Dict, Any
import uuid
import logging

from sqlmodel import Session
from data.database import engine

# The client_insights agent is no longer needed here, as its logic is now in the main co-pilot.
# from agent_core.agents import client_insights
from integrations import twilio_outgoing
from data import crm as crm_service
from data.models.campaign import CampaignBriefing, CampaignStatus
from data.models.user import User
from data.models.message import Message, MessageDirection, MessageStatus
from workflow.relationship_playbooks import get_playbook_for_intent, IntentType
from agent_core.agents import conversation as conversation_agent



async def handle_incoming_message(client_id: uuid.UUID, incoming_message: Message, realtor: User) -> Dict[str, Any]:
    """
    Processes an incoming client message, now with strategic intent detection.
    """
    logging.info(f"ORCHESTRATOR: Handling incoming message from client {client_id} for user {realtor.id}...")

    with Session(engine) as session:
        # --- This section for pausing active plans remains unchanged ---
        active_plan = crm_service.get_active_recommendation_slate_for_client(client_id, realtor.id, session)
        
        if active_plan and active_plan.is_plan:
            logging.info(f"ORCHESTRATOR: Active plan {active_plan.id} found for client {client_id}. Pausing plan.")
            active_plan.status = CampaignStatus.PAUSED
            session.add(active_plan)
            crm_service.cancel_scheduled_messages_for_plan(active_plan.id, realtor.id, session)
        elif active_plan:
            crm_service.update_slate_status(active_plan.id, CampaignStatus.COMPLETED, realtor.id, session)

        crm_service.update_last_interaction(client_id, user_id=realtor.id, session=session)
        conversation_history = crm_service.get_recent_messages(client_id=client_id, user_id=realtor.id, limit=10)
        client = crm_service.get_client_by_id(client_id, user_id=realtor.id)

        # --- ENHANCED: STRATEGIC INTENT DETECTION WITH BETTER LOGGING ---
        detected_intent = await conversation_agent.detect_conversational_intent(incoming_message.content)
        
        if detected_intent:
            logging.info(f"ORCHESTRATOR: Strategic intent '{detected_intent}' detected for message: '{incoming_message.content[:50]}...'")
        else:
            logging.info(f"ORCHESTRATOR: No strategic intent detected for message: '{incoming_message.content[:50]}...'")
        
        playbook = get_playbook_for_intent(detected_intent) if detected_intent else None

        if playbook and client:
            # --- PATH 1: A strategic intent was found. Create a Nudge Plan. ---
            logging.info(f"ORCHESTRATOR: Intent '{detected_intent}' detected. Creating Nudge Plan from playbook '{playbook.name}'.")
            
            new_plan = CampaignBriefing(
                user_id=realtor.id,
                client_id=client_id,
                parent_message_id=incoming_message.id,
                is_plan=True,
                campaign_type=playbook.intent_type,
                headline=f"AI-Suggested Plan: {playbook.name}",
                key_intel={"playbook_name": playbook.name, "steps": [step.__dict__ for step in playbook.steps]},
                original_draft="This is a multi-step plan.",  # Placeholder, as the plan has its own steps.
                status=CampaignStatus.DRAFT,
                matched_audience=[{"client_id": str(client_id), "client_name": client.full_name}],
                triggering_event_id=uuid.uuid4()
            )
            
            crm_service.save_campaign_briefing(new_plan, session=session)
            logging.info(f"ORCHESTRATOR: Saved new Nudge Plan {new_plan.id} for strategic intent '{detected_intent}'.")
            
        else:
            # --- PATH 2: No special intent. Fall back to the original behavior. ---
            if detected_intent:
                logging.info(f"ORCHESTRATOR: Intent '{detected_intent}' detected but no playbook found or client missing.")
            else:
                logging.info("ORCHESTRATOR: No specific intent detected. Generating standard recommendation slate.")
            
            recommendation_data = await conversation_agent.generate_recommendation_slate(
                realtor=realtor,
                client_id=client_id,
                incoming_message=incoming_message,
                conversation_history=conversation_history
            )

            if recommendation_data and recommendation_data.get("recommendations"):
                draft_rec = next((rec for rec in recommendation_data["recommendations"] if rec.get("type") == "SUGGEST_DRAFT"), None)
                draft_text = draft_rec['payload']['text'] if draft_rec and draft_rec.get('payload') else "Could not generate draft."

                new_slate = CampaignBriefing(
                    user_id=realtor.id,
                    client_id=client_id,
                    parent_message_id=incoming_message.id,
                    is_plan=False,
                    campaign_type="inbound_response_recommendation",
                    headline=f"AI Suggestions for {client.full_name}",
                    key_intel=recommendation_data,
                    original_draft=draft_text,
                    status=CampaignStatus.DRAFT,
                    matched_audience=[],
                    triggering_event_id=uuid.uuid4()
                )

                crm_service.save_campaign_briefing(new_slate, session=session)
                logging.info(f"ORCHESTRATOR: Saved new recommendation slate {new_slate.id}.")

        session.commit()
        logging.info(f"ORCHESTRATOR: Transaction committed successfully for client {client_id}.")

    return {"status": "processed"}


async def orchestrate_send_message_now(client_id: uuid.UUID, content: str, user_id: uuid.UUID) -> bool:
    """
    Orchestrates sending a single, immediate message.
    ---
    MODIFIED to also mark the active recommendation slate as 'completed'.
    """
    logging.info(f"ORCHESTRATOR: Orchestrating immediate send for client {client_id} for user {user_id}")
    
    # --- STATE MANAGEMENT: When a message is sent, the recommendation is fulfilled. ---
    with Session(engine) as session:
        active_slate = crm_service.get_active_recommendation_slate_for_client(client_id, user_id, session)
        if active_slate:
            logging.info(f"ORCHESTRATOR: Message sent, marking active slate {active_slate.id} as 'completed'.")
            crm_service.update_slate_status(active_slate.id, 'completed', user_id, session)
        session.commit()

    user = crm_service.get_user_by_id(user_id)
    client = crm_service.get_client_by_id(client_id, user_id=user_id)
    
    if not user or not user.twilio_phone_number:
        logging.error(f"ORCHESTRATOR ERROR: User {user_id} not found or has no Twilio number assigned.")
        return False
        
    if not client or not client.phone:
        logging.error(f"ORCHESTRATOR ERROR: Client {client_id} not found for user {user_id} or has no phone number.")
        return False
    
    first_name = client.full_name.strip().split(' ')[0]
    personalized_content = content.replace("[Client Name]", first_name)
    logging.info(f"ORCHESTRATOR: Personalized message for {first_name} (from {client.full_name}).")
    
    was_sent = twilio_outgoing.send_sms(
        from_number=user.twilio_phone_number,
        to_number=client.phone,
        body=personalized_content
    )
    
    if was_sent:
        crm_service.update_last_interaction(client_id, user_id=user_id)
    
    return was_sent