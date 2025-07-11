# backend/agent_core/orchestrator.py
# --- MODIFIED: Upgraded to manage the recommendation slate lifecycle.

from typing import Dict, Any
import uuid
import logging

from sqlmodel import Session
from data.database import engine

from agent_core.agents import conversation as conversation_agent
# The client_insights agent is no longer needed here, as its logic is now in the main co-pilot.
# from agent_core.agents import client_insights
from integrations import twilio_outgoing
from data import crm as crm_service
from data.models.campaign import CampaignBriefing
from data.models.user import User
from data.models.message import Message, MessageDirection, MessageStatus

async def handle_incoming_message(client_id: uuid.UUID, incoming_message: Message, realtor: User) -> Dict[str, Any]:
    """
    Processes an incoming client message by generating a slate of recommendations,
    managing the state of old recommendations, and updating client interaction timestamps.
    """
    logging.info(f"ORCHESTRATOR: Handling incoming message from client {client_id} for user {realtor.id}...")
    
    with Session(engine) as session:
        client = crm_service.get_client_by_id(client_id, user_id=realtor.id)
        if not client:
            logging.error(f"ORCHESTRATOR ERROR: Could not find client with ID {client_id} for user {realtor.id}. Aborting.")
            return {"error": "Client not found"}
        
        # --- STATE MANAGEMENT: Mark any existing active slate as 'stale' ---
        # This is the core logic that makes old recommendations "fall off" the UI.
        active_slate = crm_service.get_active_recommendation_slate_for_client(client_id, realtor.id, session)
        if active_slate:
            logging.info(f"ORCHESTRATOR: Found active slate {active_slate.id}, marking as 'stale'.")
            crm_service.update_slate_status(active_slate.id, 'stale', realtor.id, session)

        # Update the client's last interaction timestamp.
        crm_service.update_last_interaction(client_id, user_id=realtor.id, session=session)

        # Fetch recent conversation history for the AI's context.
        conversation_history = crm_service.get_recent_messages(
            client_id=client_id, 
            user_id=realtor.id,
            limit=10 
        )
        logging.info(f"ORCHESTRATOR: Fetched {len(conversation_history)} recent messages for AI context.")

        # --- AGENT CALL: Generate the new recommendation slate ---
        # Note the function name change to reflect its new purpose.
        recommendation_slate_data = await conversation_agent.generate_recommendation_slate(
            realtor=realtor,
            client_id=client_id,
            incoming_message=incoming_message,
            conversation_history=conversation_history
        )
        logging.info("ORCHESTRATOR: Co-Pilot Agent generated a new recommendation slate.")

        # --- SAVE SLATE: Persist the new slate to the database ---
        if recommendation_slate_data and recommendation_slate_data.get("recommendations"):
            # Extract the primary text draft from the recommendations list to store in the top-level field.
            draft_rec = next((rec for rec in recommendation_slate_data["recommendations"] if rec.get("type") == "SUGGEST_DRAFT"), None)
            draft_text = draft_rec['payload']['text'] if draft_rec and draft_rec.get('payload') else "Could not generate draft."

            # Create the new CampaignBriefing object which serves as our slate.
            new_slate = CampaignBriefing(
                user_id=realtor.id,
                client_id=client_id,
                parent_message_id=incoming_message.id,
                campaign_type="inbound_response_recommendation", # New type
                headline=f"AI Suggestions for {client.full_name}",
                key_intel=recommendation_slate_data, # Store the full structured response
                original_draft=draft_text, # Store the main draft for easy access
                status='active', # The new slate is always active
                matched_audience=[],
                triggering_event_id=uuid.uuid4()
            )
            crm_service.save_campaign_briefing(new_slate, session=session)
            logging.info(f"ORCHESTRATOR: Saved new active recommendation slate {new_slate.id}.")

        # The separate client_insights agent call is no longer needed.
        # Its functionality is now integrated into the main co-pilot agent.
        
        # Commit all database changes at the end of the transaction.
        session.commit()
        logging.info(f"ORCHESTRATOR: Transaction committed successfully for client {client_id}.")

    # The return value to the webhook is less critical now, as the UI will fetch the slate via the API.
    return { "status": "processed", "new_recommendations": bool(recommendation_slate_data) }


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