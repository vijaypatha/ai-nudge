# ---
# File Path: backend/agent_core/orchestrator.py
# Purpose: The central AI orchestrator that coordinates agents and tools.
# This version is UPDATED to be database-aware, use the real Twilio integration,
# and implement last_interaction tracking.
# ---

from typing import Dict, Any
import uuid

from agent_core.agents import conversation as conversation_agent
from agent_core.agents import client_insights
# CORRECTED: We will call the real Twilio integration directly, not a mock tool.
from integrations import twilio_outgoing
from data import crm as crm_service
from data.models.campaign import CampaignBriefing

# Note: The _get_mock_client_context function is no longer needed as we fetch real data.

async def handle_incoming_message(client_id: uuid.UUID, incoming_message_content: str) -> Dict[str, Any]:
    """
    Processes an incoming client message by generating a reply draft, analyzing
    for intel, and updating the client's last_interaction timestamp.
    """
    print(f"ORCHESTRATOR: Handling incoming message from client {client_id}...")
    
    # Use the database-aware CRM function
    client = crm_service.get_client_by_id(client_id)
    if not client:
        print(f"ORCHESTRATOR ERROR: Could not find client with ID {client_id}. Aborting.")
        return {"error": "Client not found"}

    # --- FEATURE IMPLEMENTATION: Interaction Tracking for INBOUND messages ---
    crm_service.update_last_interaction(client_id)

    client_context = {"client_name": client.full_name, "client_tags": client.tags}

    # --- Task 1: Generate a standard reply draft ---
    ai_response_draft = await conversation_agent.generate_response(
        client_id=client_id,
        incoming_message_content=incoming_message_content,
        context=client_context
    )
    print("ORCHESTRATOR: AI Conversation Agent generated reply draft.")

    # --- Task 2: Analyze the message for new intel (Existing logic preserved) ---
    found_intel = await client_insights.extract_intel_from_message(incoming_message_content)
    
    if found_intel:
        # Get the default user from the database
        realtor = crm_service.get_user_by_id(uuid.UUID("a8c6f1d7-8f7a-4b6e-8b0f-9e5a7d6c5b4a"))
        if realtor:
            key_intel_data = {"suggestion": found_intel}
            
            # CORRECTED: The CampaignBriefing model does not have a client_id.
            # This type of briefing is associated with a user, not a specific client.
            intel_briefing = CampaignBriefing(
                user_id=realtor.id,
                campaign_type="intel_suggestion",
                headline=f"New Intel Suggestion for {client.full_name}",
                key_intel=key_intel_data,
                original_draft=found_intel,
                matched_audience=[], # This type of nudge is informational
                triggering_event_id=uuid.uuid4() # This event is self-generated
            )
            crm_service.save_campaign_briefing(intel_briefing)

    return { "ai_draft_response": ai_response_draft }

async def orchestrate_send_message_now(client_id: uuid.UUID, content: str) -> bool:
    """
    Orchestrates sending a single, immediate message and updates the
    client's last_interaction timestamp.
    """
    print(f"ORCHESTRATOR: Orchestrating immediate send for client {client_id}")
    client = crm_service.get_client_by_id(client_id)
    if not client or not client.phone:
        print(f"ORCHESTRATOR ERROR: Client {client_id} not found or has no phone number.")
        return False
    
    # CORRECTED: Call the real Twilio integration, not a mock tool.
    was_sent = twilio_outgoing.send_sms(to_number=client.phone, body=content)
    
    if was_sent:
        # --- FEATURE IMPLEMENTATION: Interaction Tracking for OUTBOUND one-off messages ---
        crm_service.update_last_interaction(client_id)
    
    return was_sent