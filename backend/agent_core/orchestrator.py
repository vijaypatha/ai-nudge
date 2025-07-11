# backend/agent_core/orchestrator.py
# --- MODIFIED: Fetches recent conversation history and passes it to the conversation agent for context.

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
from data.models.message import Message, MessageDirection, MessageStatus

async def handle_incoming_message(client_id: uuid.UUID, incoming_message: Message, realtor: User) -> Dict[str, Any]:
    """
    Processes an incoming client message by generating a reply draft, analyzing
    for intel, and updating the client's last_interaction timestamp.
    The incoming message is assumed to be already saved to the database.
    """
    logging.info(f"ORCHESTRATOR: Handling incoming message from client {client_id} for user {realtor.id}...")
    
    with Session(engine) as session:
        client = crm_service.get_client_by_id(client_id, user_id=realtor.id)
        if not client:
            logging.error(f"ORCHESTRATOR ERROR: Could not find client with ID {client_id} for user {realtor.id}. Aborting.")
            return {"error": "Client not found"}
        
        # Perform other write operations using the managed session
        crm_service.update_last_interaction(client_id, user_id=realtor.id, session=session)

        # --- MODIFICATION START: Fetch recent conversation history for context ---
        # Call the new CRM function to get the last 10 messages. This provides
        # the AI with memory of the recent back-and-forth.
        conversation_history = crm_service.get_recent_messages(
            client_id=client_id, 
            user_id=realtor.id,
            limit=10 
        )
        logging.info(f"ORCHESTRATOR: Fetched {len(conversation_history)} recent messages for AI context.")
        # --- MODIFICATION END ---

        client_context = {"client_name": client.full_name, "client_tags": client.user_tags + client.ai_tags}

        # --- MODIFIED: Pass the conversation_history to the agent ---
        ai_response_draft = await conversation_agent.generate_response(
            client_id=client_id,
            incoming_message_content=incoming_message.content,
            context=client_context,
            conversation_history=conversation_history # Pass the history here
        )
        logging.info("ORCHESTRATOR: AI Conversation Agent generated reply draft.")

        if ai_response_draft and isinstance(ai_response_draft, dict):
            draft_text = ai_response_draft.get('ai_draft', 'Could not generate draft.')
            draft_briefing = CampaignBriefing(
                user_id=realtor.id,
                client_id=client_id,
                parent_message_id=incoming_message.id,
                campaign_type="ai_draft_response",
                headline=f"AI Draft for {client.full_name}",
                key_intel=ai_response_draft,
                original_draft=draft_text,
                matched_audience=[],
                triggering_event_id=uuid.uuid4()
            )
            crm_service.save_campaign_briefing(draft_briefing, session=session)

        found_intel = await client_insights.extract_intel_from_message(incoming_message.content)
        
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
        crm_service.update_last_interaction(client_id, user_id=user_id)
    
    return was_sent