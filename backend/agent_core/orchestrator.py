# ---
# File Path: backend/agent_core/orchestrator.py
# Purpose: The central AI orchestrator that coordinates agents and tools.
# ---

from typing import Dict, Any
import uuid

# Import the specific AI agents this orchestrator will coordinate.
from agent_core.agents import conversation as conversation_agent
from agent_core.agents import client_insights
from agent_core.tools import communication as comm_tool
from data import crm as crm_service
from data.models.campaign import CampaignBriefing

def _get_mock_client_context(client_id: uuid.UUID) -> Dict[str, Any]:
    """Simulates fetching relevant context for a client."""
    client_data = crm_service.get_client_by_id_mock(client_id)
    if client_data:
        return {
            "client_tags": client_data.tags,
            "client_name": client_data.full_name,
            "last_interaction": client_data.last_interaction
        }
    return {}

async def handle_incoming_message(client_id: uuid.UUID, incoming_message_content: str) -> Dict[str, Any]:
    """
    Processes an incoming client message by performing two key tasks:
    1. Generates an intelligent draft response for the Realtor.
    2. Analyzes the message for new client intel to suggest profile updates.
    """
    print(f"ORCHESTRATOR: Handling incoming message from client {client_id}: '{incoming_message_content[:50]}...'")
    
    client = crm_service.get_client_by_id_mock(client_id)
    if not client:
        print(f"ORCHESTRATOR ERROR: Could not find client with ID {client_id}. Aborting.")
        return {"error": "Client not found"}

    client_context = {"client_name": client.full_name, "client_tags": client.tags}

    # --- Task 1: Generate a standard reply draft ---
    ai_response_draft = await conversation_agent.generate_response(
        client_id=client_id,
        incoming_message_content=incoming_message_content,
        context=client_context
    )
    print("ORCHESTRATOR: AI Conversation Agent generated reply draft.")

    # --- Task 2: Analyze the message for new intel ---
    found_intel = await client_insights.extract_intel_from_message(incoming_message_content)
    
    if found_intel:
        realtor = crm_service.mock_users_db[0]
        key_intel_data = {"suggestion": found_intel}
        
        intel_briefing = CampaignBriefing(
            user_id=realtor.id,
            client_id=client_id,
            campaign_type="intel_suggestion",
            headline=f"New Intel Suggestion for {client.full_name}",
            key_intel=key_intel_data,
            original_draft=found_intel,
            matched_audience=[],
            triggering_event_id=uuid.uuid4()
        )
        crm_service.save_campaign_briefing(intel_briefing)

    return { "ai_draft_response": ai_response_draft }

async def orchestrate_send_message_now(client_id: uuid.UUID, content: str) -> bool:
    """Orchestrates the business logic for sending a message immediately."""
    print(f"ORCHESTRATOR: Orchestrating immediate send for client {client_id}")
    client = crm_service.get_client_by_id_mock(client_id)
    if not client:
        print(f"ORCHESTRATOR ERROR: Client {client_id} not found.")
        return False
    
    success = comm_tool.send_message_now(client_id, content)
    return success