# backend/agent_core/orchestrator.py
# --- MODIFIED: Implements "Do Both" and "Pause & Propose" logic.

from typing import Dict, Any, List
import uuid
import logging

from sqlmodel import Session, select
from data.database import engine

from integrations import twilio_outgoing
from data import crm as crm_service
# --- MODIFIED: Import new models and enum ---
from data.models.campaign import CampaignBriefing, CampaignStatus, CoPilotAction
from data.models.user import User
from data.models.message import Message
from workflow.relationship_playbooks import get_playbook_for_intent
from agent_core.agents import conversation as conversation_agent

async def handle_incoming_message(client_id: uuid.UUID, incoming_message: Message, realtor: User) -> Dict[str, Any]:
    """
    Processes an incoming client message with the new "Pause & Propose" and "Do Both" logic.
    """
    logging.info(f"ORCHESTRATOR: Handling incoming message from client {client_id}...")

    with Session(engine) as session:
        # --- "PAUSE & PROPOSE" LOGIC ---
        # First, check for any ACTIVE plans for this specific client that need to be paused.
        active_plan_statement = select(CampaignBriefing).where(
            CampaignBriefing.client_id == client_id,
            CampaignBriefing.user_id == realtor.id,
            CampaignBriefing.status == CampaignStatus.ACTIVE,
            CampaignBriefing.is_plan == True
        )
        active_plan_to_pause = session.exec(active_plan_statement).first()
        
        if active_plan_to_pause:
            logging.info(f"ORCHESTRATOR: Active plan {active_plan_to_pause.id} found for client. Pausing plan.")
            active_plan_to_pause.status = CampaignStatus.PAUSED
            session.add(active_plan_to_pause)
            crm_service.cancel_scheduled_messages_for_plan(active_plan_to_pause.id, realtor.id, session)

            # --- GENERATE CO-PILOT BRIEFING ---
            co_pilot_briefing = CampaignBriefing(
                user_id=realtor.id,
                client_id=client_id,
                parent_message_id=incoming_message.id,
                is_plan=False,
                campaign_type="co_pilot_briefing",
                headline="Co-Pilot Suggestion",
                key_intel={
                    "paused_plan_headline": active_plan_to_pause.headline,
                    "actions": [
                        CoPilotAction(type="UPDATE_PLAN", label="Update plan from new info").model_dump(),
                        CoPilotAction(type="END_PLAN", label="End plan (goal met)").model_dump(),
                    ]
                },
                original_draft=f"Your client replied, so I've paused the '{active_plan_to_pause.headline}' campaign. I can generate a new plan based on their message.",
                status=CampaignStatus.DRAFT,
                matched_audience=[],
                triggering_event_id=uuid.uuid4()
            )
            crm_service.save_campaign_briefing(co_pilot_briefing, session=session)
            logging.info(f"ORCHESTRATOR: Created Co-Pilot Briefing {co_pilot_briefing.id} for paused plan.")
            session.commit()
            return {"status": "paused_and_proposed"}

        # --- "DO BOTH" LOGIC (if no active plan was paused) ---
        crm_service.update_last_interaction(client_id, user_id=realtor.id, session=session)
        conversation_history = crm_service.get_recent_messages(client_id=client_id, user_id=realtor.id, limit=10)
        client = crm_service.get_client_by_id(client_id, user_id=realtor.id)
        detected_intent = await conversation_agent.detect_conversational_intent(incoming_message.content)
        playbook = get_playbook_for_intent(detected_intent) if detected_intent else None

        # PATH 1: A strategic intent was found. Create BOTH immediate suggestions AND a plan.
        if playbook and client:
            logging.info(f"ORCHESTRATOR: Intent '{detected_intent}' detected. Executing 'Do Both' strategy.")
            
            # 1. Create Immediate Suggestions
            recommendation_data = await conversation_agent.generate_recommendation_slate(
                realtor=realtor, client_id=client_id, incoming_message=incoming_message, conversation_history=conversation_history
            )
            if recommendation_data and recommendation_data.get("recommendations"):
                draft_rec = next((rec for rec in recommendation_data["recommendations"] if rec.get("type") == "SUGGEST_DRAFT"), None)
                draft_text = draft_rec['payload']['text'] if draft_rec and draft_rec.get('payload') else "Could not generate draft."
                immediate_slate = CampaignBriefing(
                    user_id=realtor.id, client_id=client_id, parent_message_id=incoming_message.id, is_plan=False,
                    campaign_type="inbound_response_recommendation", headline=f"AI Suggestions for {client.full_name}",
                    key_intel=recommendation_data, original_draft=draft_text, status=CampaignStatus.DRAFT, matched_audience=[], triggering_event_id=uuid.uuid4()
                )
                crm_service.save_campaign_briefing(immediate_slate, session=session)
                logging.info(f"ORCHESTRATOR: Saved immediate recommendation slate {immediate_slate.id}.")

            # 2. Create the Nudge Plan
            new_plan = CampaignBriefing(
                user_id=realtor.id, client_id=client_id, parent_message_id=incoming_message.id, is_plan=True,
                campaign_type=playbook.intent_type, headline=f"AI-Suggested Plan: {playbook.name}",
                key_intel={"playbook_name": playbook.name, "steps": [step.__dict__ for step in playbook.steps]},
                original_draft="This is a multi-step plan.", status=CampaignStatus.DRAFT,
                matched_audience=[{"client_id": str(client_id), "client_name": client.full_name}], triggering_event_id=uuid.uuid4()
            )
            crm_service.save_campaign_briefing(new_plan, session=session)
            logging.info(f"ORCHESTRATOR: Saved new Nudge Plan {new_plan.id} for strategic intent '{detected_intent}'.")

        # PATH 2: No special intent. Generate standard recommendations only.
        else:
            if client:
                logging.info("ORCHESTRATOR: No specific intent detected. Generating standard recommendation slate.")
                recommendation_data = await conversation_agent.generate_recommendation_slate(
                    realtor=realtor, client_id=client_id, incoming_message=incoming_message, conversation_history=conversation_history
                )
                if recommendation_data and recommendation_data.get("recommendations"):
                    draft_rec = next((rec for rec in recommendation_data["recommendations"] if rec.get("type") == "SUGGEST_DRAFT"), None)
                    draft_text = draft_rec['payload']['text'] if draft_rec and draft_rec.get('payload') else "Could not generate draft."
                    new_slate = CampaignBriefing(
                        user_id=realtor.id, client_id=client_id, parent_message_id=incoming_message.id, is_plan=False,
                        campaign_type="inbound_response_recommendation", headline=f"AI Suggestions for {client.full_name}",
                        key_intel=recommendation_data, original_draft=draft_text, status=CampaignStatus.DRAFT, matched_audience=[], triggering_event_id=uuid.uuid4()
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