# backend/agent_core/orchestrator.py
# DEFINITIVE FIX: Manages database operations within a single, explicit
# transaction to ensure data integrity and prevent silent failures.

from typing import Dict, Any
import uuid
import logging

from sqlmodel import Session
from data.database import engine

from agent_core.agents import conversation as conversation_agent
from agent_core.agents import client_insights
from integrations import twilio_outgoing
from data import crm as crm_service
from data.models.campaign import CampaignBriefing
from data.models.user import User

async def handle_incoming_message(client_id: uuid.UUID, incoming_message_content: str, realtor: User) -> Dict[str, Any]:
    """
    Processes an incoming client message by generating a reply draft, analyzing
    for intel, and updating the client's last_interaction timestamp.
    All database operations are wrapped in a single transaction.
    """
    logging.info(f"ORCHESTRATOR: Handling incoming message from client {client_id} for user {realtor.id}...")
    
    # --- DEFINITIVE FIX: Use a single, managed database session for the entire operation ---
    # This ensures all changes are committed together in one transaction, preventing race conditions
    # and silent failures.
    with Session(engine) as session:
        # Note: Read operations like get_client_by_id don't need the session passed in,
        # but all write operations MUST use the managed session.
        client = crm_service.get_client_by_id(client_id, user_id=realtor.id)
        if not client:
            logging.error(f"ORCHESTRATOR ERROR: Could not find client with ID {client_id} for user {realtor.id}. Aborting.")
            return {"error": "Client not found"}

        # Perform write operations using the managed session
        crm_service.update_last_interaction(client_id, user_id=realtor.id, session=session)

        client_context = {"client_name": client.full_name, "client_tags": client.user_tags + client.ai_tags}

        ai_response_draft = await conversation_agent.generate_response(
            client_id=client_id,
            incoming_message_content=incoming_message_content,
            context=client_context
        )
        logging.info("ORCHESTRATOR: AI Conversation Agent generated reply draft.")

        if ai_response_draft and isinstance(ai_response_draft, dict):
            draft_text = ai_response_draft.get('ai_draft', 'Could not generate draft.')
            draft_briefing = CampaignBriefing(
                user_id=realtor.id,
                client_id=client_id,
                campaign_type="ai_draft_response",
                headline=f"AI Draft for {client.full_name}",
                key_intel=ai_response_draft,
                original_draft=draft_text,
                matched_audience=[],
                triggering_event_id=uuid.uuid4()
            )
            crm_service.save_campaign_briefing(draft_briefing, session=session)

        found_intel = await client_insights.extract_intel_from_message(incoming_message_content)
        
        if found_intel:
            intel_text_for_draft = ""
            if isinstance(found_intel, dict):
                intel_text_for_draft = found_intel.get('suggestion') or found_intel.get('text') or str(found_intel)
            else:
                intel_text_for_draft = str(found_intel)

            intel_briefing = CampaignBriefing(
                user_id=realtor.id,
                client_id=client.id,
                campaign_type="intel_suggestion",
                headline=f"New Intel Suggestion for {client.full_name}",
                key_intel={"suggestion": found_intel},
                original_draft=intel_text_for_draft,
                matched_audience=[],
                triggering_event_id=uuid.uuid4()
            )
            crm_service.save_campaign_briefing(intel_briefing, session=session)

        # Commit all the queued changes at the very end of the process.
        session.commit()
        logging.info(f"ORCHESTRATOR: Transaction committed successfully for client {client_id}.")

    return { "ai_draft_response": ai_response_draft }

async def orchestrate_send_message_now(client_id: uuid.UUID, content: str, user_id: uuid.UUID) -> bool:
    """
    Orchestrates sending a single, immediate message from the user's specific
    Twilio number.
    """
    logging.info(f"ORCHESTRATOR: Orchestrating immediate send for client {client_id} for user {user_id}")
    
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
        # This function can create its own session, which is fine for this simple, single operation.
        crm_service.update_last_interaction(client_id, user_id=user_id)
    
    return was_sent