# backend/agent_core/orchestrator.py

from typing import Dict, Any # For type hinting dictionaries
import uuid # For unique IDs

# Import the specific AI agents this orchestrator will coordinate.
# For now, we're importing the conversation agent.
from agent_core.agents import conversation as conversation_agent

from agent_core.agents import client_insights # <-- NEW IMPORT


# Import tools (like the communication tool) that agents might need to interact with.
from agent_core.tools import communication as comm_tool

# Import data services to fetch client context
from data import crm as crm_service # Assuming crm.py will manage client data access

from data.models.campaign import CampaignBriefing, MatchedClient #

# In a real system, you might have a more sophisticated way to get client context.
# For now, we'll use a mock to simulate getting client tags.
def _get_mock_client_context(client_id: uuid.UUID) -> Dict[str, Any]:
    """
    Simulates fetching relevant context for a client.
    In a real app, this would query the personalization engine or CRM data service.
    """
    # Use the mock client data from the crm service (which will eventually be a real DB)
    client_data = crm_service.get_client_by_id_mock(client_id)
    if client_data:
        return {
            "client_tags": client_data.tags,
            "client_name": client_data.full_name,
            "last_interaction": client_data.last_interaction # Example context
        }
    return {} # Return empty dict if client not found or no context


async def handle_incoming_message(
    client_id: uuid.UUID,
    incoming_message_content: str
) -> Dict[str, Any]:
    """
    The central orchestration function for processing an incoming client message.
    This function decides which AI agent should handle the message and
    what actions should be taken.

    How it works for the robot: This is the robot's "Internal Coordinator" or "Inner Boss."
    When a new message comes in, this "boss" quickly decides:
    1. "Who should handle this message?" (e.g., the Chatting Talent).
    2. "What information do they need?" (get client context).
    3. "What should they try to do?" (generate a response).

    - **client_id**: The unique ID of the client who sent the message.
    - **incoming_message_content**: The text content of the message received.
    Returns a dictionary containing the orchestrated response, typically an AI draft.
    """
    print(f"ORCHESTRATOR: Handling incoming message from client {client_id}: '{incoming_message_content[:50]}...'")

    # Step 1: Gather context about the client.
    # The orchestrator uses its internal "network" to get information needed by the agents.
    client_context = _get_mock_client_context(client_id)
    print(f"ORCHESTRATOR: Gathered context for client {client_id}: {client_context.get('client_tags')}")

    # Step 2: Delegate to the appropriate AI agent.
    # For an incoming message, the 'conversation_agent' is typically the primary handler.
    # The orchestrator tells the conversation agent to generate a draft response.
    ai_response_draft = await conversation_agent.generate_response(
        client_id=client_id,
        incoming_message_content=incoming_message_content,
        context=client_context
    )
    print(f"ORCHESTRATOR: AI Conversation Agent generated draft.")

    # Step 3: Orchestrate potential tools or follow-up actions (basic for now).
    # Based on the AI's suggested action, the orchestrator could call tools.
    # For now, we'll just return the draft for the user to review.
    # A more advanced orchestrator might:
    # - Call comm_tool.send_message_now if 'suggested_action' is 'auto_send'
    # - Call scheduling_tool.schedule_showing if AI detects showing intent.

    return {
        "client_id": client_id,
        "incoming_message": incoming_message_content,
        "ai_draft_response": ai_response_draft,
        "orchestration_status": "draft_generated"
    }

# --- ADD THIS NEW FUNCTION ---
async def orchestrate_send_message_now(client_id: uuid.UUID, content: str) -> bool:
    """
    Orchestrates the business logic for sending a message immediately.
    This keeps the API layer clean and centralizes logic.
    """
    print(f"ORCHESTRATOR: Orchestrating immediate send for client {client_id}")
    # Step 1: Validate client existence (optional, but good practice)
    client = crm_service.get_client_by_id_mock(client_id)
    if not client:
        # In a real app, you'd raise a specific exception here
        print(f"ORCHESTRATOR ERROR: Client {client_id} not found.")
        return False
    
    # Step 2: Delegate to the communication tool
    success = comm_tool.send_message_now(client_id, content)
    return success

async def handle_incoming_message(client_id: uuid.UUID, incoming_message_content: str) -> Dict[str, Any]:
    """
    Processes an incoming client message, generates a draft response,
    AND analyzes the message for new intel.
    """
    print(f"ORCHESTRATOR: Handling incoming message from client {client_id}...")
    client_context = _get_mock_client_context(client_id)

    # --- Task 1: Generate a standard reply draft (existing logic) ---
    ai_response_draft = await conversation_agent.generate_response(
        client_id=client_id,
        incoming_message_content=incoming_message_content,
        context=client_context
    )

    # --- NEW Task 2: Analyze the message for new intel ---
    found_intel = await client_insights.extract_intel_from_message(incoming_message_content)

    if found_intel:
        # If intel is found, create a new "intel_suggestion" campaign briefing
        realtor = crm_service.mock_users_db[0]
        client = crm_service.get_client_by_id_mock(client_id)

        intel_briefing = CampaignBriefing(
            user_id=realtor.id,
            client_id=client_id, # Storing client_id for context
            campaign_type="intel_suggestion",
            headline=f"New Intel Suggestion for {client.full_name}",
            original_draft=found_intel, # Use this field to store the suggested note
            matched_audience=[], # Not applicable for this type
            triggering_event_id=uuid.uuid4() # A new unique ID for this event
        )
        crm_service.save_campaign_briefing(intel_briefing)

    return { "ai_draft_response": ai_response_draft } # Return the original response draft