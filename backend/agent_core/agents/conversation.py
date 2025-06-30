# ---
# File Path: backend/agent_core/agents/conversation.py
# This version is UPDATED to handle the new 'recency_nudge' event type.
# ---
from typing import Dict, Any, List
import uuid

from data.models.user import User
from data.models.property import Property
from data.models.campaign import MatchedClient
from integrations import openai as openai_service
from data import crm as crm_service

# --- Function for INBOUND Messages (Existing) ---
async def generate_response(
    client_id: uuid.UUID,
    incoming_message_content: str,
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generates a draft response for an incoming client message using an LLM.
    """
    print(f"CONVERSATION AGENT (INBOUND): Generating response for client {client_id}...")
    
    client_name = context.get('client_name', 'client')
    client_tags = ", ".join(context.get('client_tags', []))
    
    all_properties = crm_service.get_all_properties()
    property_context_str = ""
    if all_properties:
        property_context_str = "\n\nAvailable Properties (for context, include only relevant ones in response):\n"
        for i, prop in enumerate(all_properties[:3]):
            property_context_str += (f"- Property {i+1}: {prop.address}, Price: ${prop.price:,.0f}, Status: {prop.status}, Type: {prop.property_type}\n")

    messages = [{"role": "system", "content": (f"You are an AI Nudge assistant... The client's name is {client_name}. Their tags include: {client_tags}.{property_context_str}")}, {"role": "user", "content": incoming_message_content}]
    
    ai_draft_content = await openai_service.generate_text_completion(prompt_messages=messages, model="gpt-4o-mini")
    
    if ai_draft_content:
        return {"ai_draft": ai_draft_content, "confidence": 0.95, "suggested_action": "send_draft"}
    else:
        return {"ai_draft": "I'm sorry, I couldn't generate a smart response right now.", "confidence": 0.1, "suggested_action": "review_manually"}

# --- Function for OUTBOUND Campaigns (UPDATED) ---
async def draft_outbound_campaign_message(
    realtor: User,
    event_type: str,
    matched_audience: List[MatchedClient],
    property_item: Property | None = None, # Property is now optional
) -> str:
    """
    Uses a live LLM to draft a personalized outbound message for different campaign types.
    """
    print(f"CONVERSATION AGENT (OUTBOUND): Drafting message for event '{event_type}' via live LLM call...")

    prompt = ""
    # --- NEW LOGIC for Recency Nudge ---
    if event_type == "recency_nudge":
        prompt = f"""
        You are an expert real estate agent's assistant, 'AI Nudge'. Your task is to draft a friendly, casual, and short "checking in" SMS message.
        The agent, {realtor.full_name}, hasn't spoken to these clients in a while and wants to reconnect.

        Instructions:
        1.  Draft a master SMS message. Use the placeholder `[Client Name]` for personalization.
        2.  The tone should be warm and relationship-focused, not salesy.
        3.  Do NOT mention a specific property.
        4.  The goal is simply to restart the conversation. Ask an open-ended question.
        
        Draft the SMS message now:
        """
    # --- Existing Logic for Market Events ---
    elif property_item:
        prompt = f"""
        You are an expert real estate agent's assistant, 'AI Nudge'. Your task is to draft a compelling and slightly informal master SMS message.

        Realtor's Name: {realtor.full_name}
        Context: A '{event_type}' event occurred for the property at {property_item.address}.
        
        Instructions:
        1.  Draft a master SMS message for a list of clients. Use the placeholder `[Client Name]` for personalization.
        2.  The tone should be helpful and insightful, not pushy.
        3.  You MUST include the property's listing URL at the end if it exists.
        4.  The message must be concise and ready for SMS.

        Property URL: {property_item.listing_url or "N/A"}
        Draft the SMS message now:
        """

    if not prompt:
        return "Could not generate a message draft for this event type."

    ai_draft = await openai_service.generate_text_completion(
        prompt_messages=[{"role": "user", "content": prompt}],
        model="gpt-4o-mini"
    )

    if not ai_draft:
        print(f"CONVERSATION AGENT (OUTBOUND): LLM failed, using fallback message for event {event_type}.")
        ai_draft = f"Hi [Client Name], just wanted to check in and see how you're doing!"

    print("CONVERSATION AGENT (OUTBOUND): Message draft completed.")
    return ai_draft