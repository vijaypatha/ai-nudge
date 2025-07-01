# ---
# File Path: backend/agent_core/agents/conversation.py 
# --- UPDATED to comprehensively integrate the user's learned style guide ---
from typing import Dict, Any, List
import uuid
import json

from data.models.user import User
from data.models.property import Property
from data.models.campaign import MatchedClient
from integrations import openai as openai_service
from data import crm as crm_service

# --- Function for INBOUND Messages (Unchanged from your version) ---
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

# --- Function for OUTBOUND Campaigns (UPDATED with Style Adaptation) ---
async def draft_outbound_campaign_message(
    realtor: User,
    event_type: str,
    matched_audience: List[MatchedClient],
    property_item: Property | None = None,
) -> str:
    """
    Uses a live LLM to draft a personalized outbound message, now incorporating
    the user's learned writing style into the existing prompt structure.
    """
    print(f"CONVERSATION AGENT (OUTBOUND): Drafting message for event '{event_type}'...")

    # --- KEY INTEGRATION: Create the style guide addition ---
    # This will be added to every prompt to ensure the AI matches the user's voice.
    style_prompt_addition = ""
    if realtor.ai_style_guide:
        try:
            style_rules = json.dumps(realtor.ai_style_guide, indent=2)
            style_prompt_addition = f"\n\nIMPORTANT: You MUST follow these style rules to match the user's voice:\n{style_rules}"
            print(f"CONVERSATION AGENT: Applying style guide for user {realtor.id}")
        except Exception as e:
            print(f"CONVERSATION AGENT: Could not apply style guide. Error: {e}")

    # This base prompt will now be used within each specific event prompt.
    base_prompt_intro = f"You are an expert real estate agent's assistant, 'AI Nudge'.{style_prompt_addition}"

    prompt = ""
    # --- Logic for Recency Nudge ---
    if event_type == "recency_nudge":
        prompt = f"""
        {base_prompt_intro}
        Your task is to draft a friendly, casual, and short "checking in" SMS message.
        The agent, {realtor.full_name}, hasn't spoken to these clients in a while and wants to reconnect.

        Instructions:
        1. Draft a master SMS message. Use the placeholder `[Client Name]` for personalization.
        2. The tone should be warm and relationship-focused, not salesy.
        3. Do NOT mention a specific property.
        4. The goal is simply to restart the conversation. Ask an open-ended question.
        
        Draft the SMS message now:
        """
    # --- Logic for "Just Sold" Nudge  ---
    elif event_type == "sold_listing" and property_item:
        prompt = f"""
        {base_prompt_intro}
        Your task is to draft a compelling, value-driven SMS message about a nearby property that just sold.
        This is for clients who might be thinking of selling their own homes.

        Realtor's Name: {realtor.full_name}
        Context: The property at {property_item.address} just sold for ${property_item.price:,.0f}.

        Instructions:
        1. Draft a master SMS message. Use `[Client Name]` for personalization.
        2. The tone should be insightful and create urgency/opportunity.
        3. Start a conversation by asking if they've considered what this news means for their own home's value.
        4. Keep it concise for SMS. Do NOT include a listing URL.
        
        Draft the SMS message now:
        """
    # --- Logic for "Back on Market" Nudge  ---
    elif event_type == "back_on_market" and property_item:
        prompt = f"""
        {base_prompt_intro}
        Your task is to draft a helpful, urgent SMS message about a property that's unexpectedly available again.
        This is for clients who previously showed interest in similar homes.

        Realtor's Name: {realtor.full_name}
        Context: The property at {property_item.address} was pending sale, but just came back on the market.

        Instructions:
        1. Draft a master SMS message. Use `[Client Name]` for personalization.
        2. The tone should be helpful and create a sense of a second chance.
        3. MUST include the property's listing URL at the end.
        4. Keep it concise and clear.

        Property URL: {property_item.listing_url or "N/A"}
        Draft the SMS message now:
        """
    # --- Logic for "Expired Listing" Nudge   ---
    elif event_type == "expired_listing" and property_item:
        prompt = f"""
        {base_prompt_intro}
        Your task is to draft a short, direct, and professional outreach message for your agent, {realtor.full_name}, to send to a homeowner whose listing just expired.

        Context: The property at {property_item.address} was listed with another agent and has now expired without selling. This is a prime opportunity to win a new client.

        Instructions:
        1. The message should be from the agent's perspective.
        2. Acknowledge the listing expired and express empathy.
        3. Briefly introduce yourself and suggest you have a different, effective marketing strategy.
        4. End with a clear, low-pressure call to action.
        
        Draft the outreach message now:
        """
    # --- Logic for "Coming Soon" Nudge   ---
    elif event_type == "coming_soon" and property_item:
        prompt = f"""
        {base_prompt_intro}
        Your task is to draft an exciting, exclusive-access SMS message for clients.

        Realtor's Name: {realtor.full_name}
        Context: The property at {property_item.address} is not on the public market yet but will be soon ("Coming Soon").

        Instructions:
        1. Draft a master SMS message. Use `[Client Name]` for personalization.
        2. The tone should be exciting and create a sense of exclusivity.
        3. Emphasize that they are getting a "first look" before anyone else.
        
        Draft the SMS message now:
        """
    # --- Logic for "Withdrawn Listing" Nudge   ---
    elif event_type == "withdrawn_listing" and property_item:
        prompt = f"""
        {base_prompt_intro}
        Your task is to draft a very gentle, professional message for your agent, {realtor.full_name}, to send to a homeowner who has just withdrawn their property from the market.

        Context: The property at {property_item.address} was recently withdrawn. The homeowner may be tired of the process. The goal is to be helpful, not pushy.

        Instructions:
        1. The message should be from the agent's perspective.
        2. The tone must be low-pressure.
        3. Offer to be a future resource. Do NOT ask for a meeting now.
        
        Draft the outreach message now:
        """
    # --- Fallback Logic for other Market Events   ---
    elif property_item:
        prompt = f"""
        {base_prompt_intro}
        Your task is to draft a compelling and slightly informal master SMS message.

        Realtor's Name: {realtor.full_name}
        Context: A '{event_type}' event occurred for the property at {property_item.address}.
        
        Instructions:
        1. Draft a master SMS message. Use `[Client Name]` for personalization.
        2. The tone should be helpful and insightful.
        3. You MUST include the property's listing URL at the end if it exists.

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
        ai_draft = f"Hi [Client Name], just wanted to share a quick update with you!"

    return ai_draft
