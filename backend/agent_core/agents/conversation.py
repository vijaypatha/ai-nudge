# File Path: backend/agent_core/agents/conversation.py
# --- FINAL CORRECTED VERSION: Enhanced with date awareness and better instructions for personal intel.

from typing import Dict, Any, List
import uuid
import json
import logging
from datetime import datetime, timezone

from data.models.user import User
from data.models.resource import Resource
from data.models.campaign import MatchedClient
from data.models.message import Message, MessageDirection
from integrations import openai as openai_service
from data import crm as crm_service

# This function remains unchanged.
async def draft_instant_nudge_message(
    realtor: User,
    topic: str,
) -> str:
    """
    Uses a live LLM to draft a message for the "Instant Nudge" feature based on a user-provided topic.
    """
    logging.info(f"CONVERSATION AGENT (INSTANT NUDGE): Drafting message for topic '{topic}'...")

    style_prompt_addition = ""
    if realtor.ai_style_guide:
        try:
            style_rules = json.dumps(realtor.ai_style_guide, indent=2)
            style_prompt_addition = f"\n\nIMPORTANT: You MUST follow these style rules to match the user's voice:\n{style_rules}"
        except Exception as e:
            logging.error(f"CONVERSATION AGENT: Could not apply style guide. Error: {e}")

    base_prompt_intro = f"You are an expert real estate agent's assistant, 'AI Nudge'. Your agent's name is {realtor.full_name}.{style_prompt_addition}"

    prompt = f"""
    {base_prompt_intro}
    Your task is to draft a friendly, professional, and engaging SMS message for a client.
    The topic or goal of the message is: "{topic}"
    Instructions:
    1. Draft a master SMS message. Use the placeholder `[Client Name]` for personalization.
    2. The tone should be warm and helpful.
    3. The message should be concise and end with an open-ended question to encourage a reply.
    
    Draft the SMS message now:
    """

    ai_draft = await openai_service.generate_text_completion(
        prompt_messages=[{"role": "user", "content": prompt}],
        model="gpt-4o-mini"
    )

    return ai_draft or f"Hi [Client Name], I was just thinking about you and wanted to reach out regarding {topic}."


# --- MODIFIED: Prompt is enhanced with date context and more detailed instructions ---
async def generate_recommendation_slate(
    realtor: User,
    client_id: uuid.UUID,
    incoming_message: Message,
    conversation_history: List[Message]
) -> Dict[str, Any]:
    """
    Analyzes an incoming message and conversation history to generate a structured
    "slate of recommendations" for the user to act upon.
    """
    logging.info(f"CO-PILOT AGENT: Generating recommendation slate for client {client_id}...")
    
    client = crm_service.get_client_by_id(client_id, realtor.id)
    if not client: return {} 

    client_name = client.full_name
    client_tags = ", ".join(client.user_tags + client.ai_tags) if (client.user_tags or client.ai_tags) else "None"

    all_resources = crm_service.get_all_resources_for_user(user_id=realtor.id)
    resource_context_str = ""
    if all_resources:
        property_resources = [r for r in all_resources if r.resource_type == 'property']
        if property_resources:
            resource_context_str = "\n\nAvailable Properties (for context):\n"
            for i, res in enumerate(property_resources[:3]):
                attrs = res.attributes
                address = attrs.get('address', 'N/A')
                price = attrs.get('price', 0)
                status = res.status
                resource_context_str += f"- {address}, Price: ${price:,.0f}, Status: {status}\n"

    json_schema = """
    {
      "recommendations": [
        {
          "type": "SUGGEST_DRAFT",
          "payload": { "text": "<The suggested SMS response text>" }
        },
        {
          "type": "UPDATE_CLIENT_INTEL",
          "payload": {
            "tags_to_add": ["<tag1>", "<tag2>"],
            "notes_to_add": "<A concise note summarizing new client intel from the message>"
          }
        }
      ]
    }
    """

    # --- MODIFICATION START ---
    # Added Current Date context and enhanced instructions for the AI.
    current_date_str = datetime.now(timezone.utc).strftime('%B %d, %Y')

    prompt = f"""
    You are an AI Co-Pilot for {realtor.full_name}, an expert in their field.
    Your task is to analyze the latest incoming message from a client named {client_name} and generate a structured JSON object of recommended actions.

    ## CONTEXT
    - Current Date: {current_date_str}
    - Client Name: {client_name}
    - Existing Client Tags: {client_tags}
    {resource_context_str}
    - Conversation History (most recent first):
    """
    
    for message in reversed(conversation_history):
        direction = "Client" if message.direction == MessageDirection.INBOUND else "Agent"
        prompt += f"- {direction}: {message.content}\n"
    
    prompt += f"\n## LATEST INCOMING MESSAGE FROM {client_name}:\n\"{incoming_message.content}\"\n"

    prompt += f"""
    ## INSTRUCTIONS
    1.  **Analyze the LATEST INCOMING MESSAGE** in the context of the history, available resources, and the Current Date.
    2.  **Generate a helpful SMS response draft.** Use the Current Date to ensure your response is timely (e.g., if a client's birthday has passed, say "hope you had a great birthday" instead of "happy early birthday").
    3.  **Identify new, actionable intelligence.**
        - This includes real estate preferences (budget, location, features).
        - **Crucially, also identify important personal details like birthdays, anniversaries, or other life events.**
    4.  **Suggest Actions based on new intel.**
        - If the client mentions a personal date like a birthday, suggest an `UPDATE_CLIENT_INTEL` action to add a corresponding tag (e.g., "birthday-june-30") and a note (e.g., "Birthday is on June 30.").
        - Do NOT suggest adding tags that are already present in the 'Existing Client Tags' list.
    5.  **Format your entire output** as a single, valid JSON object following the schema below. If no new intel is found, the `UPDATE_CLIENT_INTEL` recommendation can be omitted.

    ## JSON OUTPUT SCHEMA
    ```json
    {json_schema}
    ```
    Now, generate the JSON output:
    """
    # --- MODIFICATION END ---
    
    logging.info(f"CO-PILOT AGENT: Sending prompt to LLM for client {client_id}.")
    
    raw_response = await openai_service.generate_text_completion(
        prompt_messages=[{"role": "user", "content": prompt}],
        model="gpt-4o-mini",
        response_format={"type": "json_object"}
    )

    if not raw_response:
        logging.error(f"CO-PILOT AGENT: LLM returned an empty response for client {client_id}.")
        return {}

    try:
        recommendation_data = json.loads(raw_response)
        logging.info(f"CO-PILOT AGENT: Successfully parsed recommendation slate from LLM for client {client_id}.")
        return recommendation_data
    except json.JSONDecodeError:
        logging.error(f"CO-PILOT AGENT: Failed to parse JSON from LLM response. Raw response: {raw_response}")
        return { "recommendations": [{"type": "SUGGEST_DRAFT", "payload": {"text": raw_response}}] }


# This function remains unchanged.
async def draft_outbound_campaign_message(
    realtor: User,
    event_type: str,
    matched_audience: List[MatchedClient],
    resource: Resource | None = None,
) -> str:
    """
    Uses a live LLM to draft a personalized outbound message for a campaign.
    This function is now vertical-agnostic by operating on a generic Resource.
    """
    logging.info(f"CONVERSATION AGENT (OUTBOUND): Drafting message for event '{event_type}'...")

    style_prompt_addition = ""
    if realtor.ai_style_guide:
        try:
            style_rules = json.dumps(realtor.ai_style_guide, indent=2)
            style_prompt_addition = f"\n\nIMPORTANT: You MUST follow these style rules to match the user's voice:\n{style_rules}"
            logging.info(f"CONVERSATION AGENT: Applying style guide for user {realtor.id}")
        except Exception as e:
            logging.error(f"CONVERSATION AGENT: Could not apply style guide. Error: {e}")

    base_prompt_intro = f"You are an expert real estate agent's assistant, 'AI Nudge'.{style_prompt_addition}"

    prompt = ""
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
    elif event_type == "sold_listing" and resource:
        attrs = resource.attributes
        prompt = f"""
        {base_prompt_intro}
        Your task is to draft a compelling, value-driven SMS message about a nearby property that just sold.
        This is for clients who might be thinking of selling their own homes.
        Realtor's Name: {realtor.full_name}
        Context: The property at {attrs.get('address', 'N/A')} just sold for ${attrs.get('price', 0):,.0f}.
        Instructions:
        1. Draft a master SMS message. Use `[Client Name]` for personalization.
        2. The tone should be insightful and create urgency/opportunity.
        3. Start a conversation by asking if they've considered what this news means for their own home's value.
        4. Keep it concise for SMS. Do NOT include a listing URL.
        Draft the SMS message now:
        """
    elif event_type == "back_on_market" and resource:
        attrs = resource.attributes
        prompt = f"""
        {base_prompt_intro}
        Your task is to draft a helpful, urgent SMS message about a property that's unexpectedly available again.
        This is for clients who previously showed interest in similar homes.
        Realtor's Name: {realtor.full_name}
        Context: The property at {attrs.get('address', 'N/A')} was pending sale, but just came back on the market.
        Instructions:
        1. Draft a master SMS message. Use `[Client Name]` for personalization.
        2. The tone should be helpful and create a sense of a second chance.
        3. MUST include the property's listing URL at the end.
        4. Keep it concise and clear.
        Property URL: {attrs.get('listing_url', 'N/A')}
        Draft the SMS message now:
        """
    elif event_type == "expired_listing" and resource:
        attrs = resource.attributes
        prompt = f"""
        {base_prompt_intro}
        Your task is to draft a short, direct, and professional outreach message for your agent, {realtor.full_name}, to send to a homeowner whose listing just expired.
        Context: The property at {attrs.get('address', 'N/A')} was listed with another agent and has now expired without selling. This is a prime opportunity to win a new client.
        Instructions:
        1. The message should be from the agent's perspective.
        2. Acknowledge the listing expired and express empathy.
        3. Briefly introduce yourself and suggest you have a different, effective marketing strategy.
        4. End with a clear, low-pressure call to action.
        Draft the outreach message now:
        """
    elif event_type == "coming_soon" and resource:
        attrs = resource.attributes
        prompt = f"""
        {base_prompt_intro}
        Your task is to draft an exciting, exclusive-access SMS message for clients.
        Realtor's Name: {realtor.full_name}
        Context: The property at {attrs.get('address', 'N/A')} is not on the public market yet but will be soon ("Coming Soon").
        Instructions:
        1. Draft a master SMS message. Use `[Client Name]` for personalization.
        2. The tone should be exciting and create a sense of exclusivity.
        3. Emphasize that they are getting a "first look" before anyone else.
        Draft the SMS message now:
        """
    elif event_type == "withdrawn_listing" and resource:
        attrs = resource.attributes
        prompt = f"""
        {base_prompt_intro}
        Your task is to draft a very gentle, professional message for your agent, {realtor.full_name}, to send to a homeowner who has just withdrawn their property from the market.
        Context: The property at {attrs.get('address', 'N/A')} was recently withdrawn. The homeowner may be tired of the process. The goal is to be helpful, not pushy.
        Instructions:
        1. The message should be from the agent's perspective.
        2. The tone must be low-pressure.
        3. Offer to be a future resource. Do NOT ask for a meeting now.
        Draft the outreach message now:
        """
    elif resource:
        attrs = resource.attributes
        prompt = f"""
        {base_prompt_intro}
        Your task is to draft a compelling and slightly informal master SMS message.
        Realtor's Name: {realtor.full_name}
        Context: A '{event_type}' event occurred for the resource at {attrs.get('address', 'Resource')}.
        Instructions:
        1. Draft a master SMS message. Use `[Client Name]` for personalization.
        2. The tone should be helpful and insightful.
        3. You MUST include the resource's URL at the end if it exists.
        Resource URL: {attrs.get('listing_url', 'N/A')}
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