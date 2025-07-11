# backend/agent_core/orchestrator.py
# DEFINITIVE FIX: Manages database operations within a single, explicit
# transaction to ensure data integrity and prevent silent failures.

from typing import Dict, Any
import uuid
import logging

from sqlmodel import Session, select
from data.database import engine

from agent_core.agents import conversation as conversation_agent
from agent_core.agents import client_insights
from integrations import twilio_outgoing
from data import crm as crm_service
from data.models.campaign import CampaignBriefing
from data.models.user import User
# --- ADDED: Import Message models for creating the incoming message log ---
from data.models.message import Message, MessageDirection, MessageStatus

async def handle_incoming_message(client_id: uuid.UUID, incoming_message_content: str, realtor: User) -> Dict[str, Any]:
    """
    Processes an incoming client message by generating a reply draft, analyzing
    for intel, and updating the client's last_interaction timestamp.
    All database operations are wrapped in a single transaction.
    """
    logging.info(f"ORCHESTRATOR: Handling incoming message from client {client_id} for user {realtor.id}...")
    
    with Session(engine) as session:
        client = crm_service.get_client_by_id(client_id, user_id=realtor.id)
        if not client:
            logging.error(f"ORCHESTRATOR ERROR: Could not find client with ID {client_id} for user {realtor.id}. Aborting.")
            return {"error": "Client not found"}
        
        # --- ADDED: First, create and save the inbound message to the universal log ---
        # This gives us a parent_message_id to link the AI draft to.
        incoming_message_obj = Message(
            user_id=realtor.id,
            client_id=client_id,
            content=incoming_message_content,
            direction=MessageDirection.INBOUND,
            status=MessageStatus.RECEIVED
        )
        # Add to the session to get an ID assigned before commit
        session.add(incoming_message_obj)
        session.flush() # Flush to assign the ID to incoming_message_obj.id
        logging.info(f"ORCHESTRATOR: Saved incoming message log with temp ID {incoming_message_obj.id}.")

        # Perform other write operations using the managed session
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
                # --- MODIFIED: Link the draft to the incoming message we just saved ---
                parent_message_id=incoming_message_obj.id,
                campaign_type="ai_draft_response",
                headline=f"AI Draft for {client.full_name}",
                key_intel=ai_response_draft,
                original_draft=draft_text,
                matched_audience=[],
                triggering_event_id=uuid.uuid4() # This can be a more specific ID if available
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

    # The return value might need to be updated to pass the full draft object to a websocket later
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
        crm_service.update_last_interaction(client_id, user_id=user_id)
    
    return was_sent