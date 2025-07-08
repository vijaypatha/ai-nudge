# ---
# File Path: backend/agent_core/orchestrator.py
# Purpose: The central AI orchestrator that coordinates agents and tools.
# DEFINITIVE FIX: The `orchestrate_send_message_now` function is updated to
# intelligently extract the client's first name for a more personal touch.
# ---

from typing import Dict, Any
import uuid
import logging

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
    """
    logging.info(f"ORCHESTRATOR: Handling incoming message from client {client_id} for user {realtor.id}...")
    
    client = crm_service.get_client_by_id(client_id, user_id=realtor.id)
    if not client:
        logging.error(f"ORCHESTRATOR ERROR: Could not find client with ID {client_id} for user {realtor.id}. Aborting.")
        return {"error": "Client not found"}

    crm_service.update_last_interaction(client_id, user_id=realtor.id)

    client_context = {"client_name": client.full_name, "client_tags": client.user_tags + client.ai_tags}

    # Task 1: Generate a standard reply draft
    ai_response_draft = await conversation_agent.generate_response(
        client_id=client_id,
        incoming_message_content=incoming_message_content,
        context=client_context
    )
    logging.info("ORCHESTRATOR: AI Conversation Agent generated reply draft.")

    # Task 2: Analyze the message for new intel
    found_intel = await client_insights.extract_intel_from_message(incoming_message_content)
    
    if found_intel:
        key_intel_data = {"suggestion": found_intel}
        intel_briefing = CampaignBriefing(
            user_id=realtor.id,
            campaign_type="intel_suggestion",
            headline=f"New Intel Suggestion for {client.full_name}",
            key_intel=key_intel_data,
            original_draft=found_intel,
            matched_audience=[],
            triggering_event_id=uuid.uuid4()
        )
        crm_service.save_campaign_briefing(intel_briefing)

    return { "ai_draft_response": ai_response_draft }

async def orchestrate_send_message_now(client_id: uuid.UUID, content: str, user_id: uuid.UUID) -> bool:
    """
    Orchestrates sending a single, immediate message. It personalizes the content
    by replacing placeholders and updates the client's last_interaction timestamp.
    """
    logging.info(f"ORCHESTRATOR: Orchestrating immediate send for client {client_id} for user {user_id}")
    
    client = crm_service.get_client_by_id(client_id, user_id=user_id)
    if not client or not client.phone:
        logging.error(f"ORCHESTRATOR ERROR: Client {client_id} not found for user {user_id} or has no phone number.")
        return False
    
    # --- ADDED: First Name Extraction Logic ---
    # Split the full name by spaces and take the first part for a personal touch.
    first_name = client.full_name.strip().split(' ')[0]
    
    # --- MODIFIED: Personalization now uses the extracted first name ---
    personalized_content = content.replace("[Client Name]", first_name)
    logging.info(f"ORCHESTRATOR: Personalized message for {first_name} (from {client.full_name}).")
    
    # Send the personalized message via Twilio
    was_sent = twilio_outgoing.send_sms(to_number=client.phone, body=personalized_content)
    
    if was_sent:
        crm_service.update_last_interaction(client_id, user_id=user_id)
    
    return was_sent
