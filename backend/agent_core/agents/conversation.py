# File Path: backend/agent_core/agents/conversation.py
# --- FINAL CORRECTED VERSION: Enhanced with date awareness and better instructions for personal intel.

from typing import Dict, Any, List, Optional
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
from workflow.relationship_playbooks import IntentType
from data.models.client import Client

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
    --- MODIFIED: Prompt now explicitly requires a draft to fix reliability issue. ---
    """
    logging.info(f"CO-PILOT AGENT: Generating recommendation slate for client {client_id}...")
    
    client = crm_service.get_client_by_id(client_id, realtor.id)
    if not client: return {} 

    client_name = client.full_name
    client_tags = ", ".join(client.user_tags + client.ai_tags) if (client.user_tags or client.ai_tags) else "None"
    
    json_schema = """
    {
      "recommendations": [
        {
          "type": "SUGGEST_DRAFT",
          "payload": { "text": "<The suggested SMS response text. This is a required field.>" }
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

    prompt = f"""
    You are an AI Co-Pilot for {realtor.full_name}, an expert in their field.
    Analyze the latest incoming message from a client named {client_name} and generate a structured JSON object of recommended actions.

    ## CONTEXT
    - Client Name: {client_name}
    - Existing Client Tags: {client_tags}
    - Conversation History (most recent first):
    """
    for message in reversed(conversation_history):
        direction = "Client" if message.direction == "inbound" else "Agent"
        prompt += f"- {direction}: {message.content}\n"
    prompt += f"\n## LATEST INCOMING MESSAGE FROM {client_name}:\n\"{incoming_message.content}\"\n"
    prompt += f"""
    ## INSTRUCTIONS
    1.  **Analyze the LATEST INCOMING MESSAGE** in the context of the history.
    2.  **Generate a helpful SMS response draft.** This is mandatory. Your response should be encouraging and move the conversation forward.
    3.  **Identify new, actionable intelligence.** If new intel is found (needs, timeline, personal details), generate an `UPDATE_CLIENT_INTEL` recommendation.
    4.  **Tag Formatting:** Tags MUST be short (2-3 words max). Do NOT suggest adding tags that already exist.
    5.  **Format your entire output** as a single, valid JSON object following the schema. The `SUGGEST_DRAFT` recommendation is always required.

    ## JSON OUTPUT SCHEMA
    ```json
    {json_schema}
    ```
    Now, generate the JSON output:
    """
    
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

# --- NEW FUNCTION START ---
async def detect_conversational_intent(message_content: str) -> Optional[IntentType]:
    """
    Analyzes the content of a message to detect specific user intents
    that could trigger a multi-step relationship playbook.
    """
    logging.info("CONVERSATION AGENT (INTENT): Analyzing message for strategic intent...")

    # Enhanced system prompt with explicit strategic focus
    system_prompt = """
You are a strategic relationship intelligence system for real estate professionals. 
Your ONLY job is to identify HIGH-VALUE opportunities that require multi-step nurturing campaigns.

You MUST respond with EXACTLY ONE of these classifications:

- "LONG_TERM_NURTURE": Client expresses future intent with timeline 2+ months OR shows buying/selling signals but not immediate urgency
- "SHORT_TERM_LEAD": Client shows immediate urgency (under 2 months) OR requests immediate action  
- "NONE": Casual conversation with no strategic opportunity

LONG_TERM_NURTURE Examples:
- "thinking about selling in 6 months"
- "maybe next year we'll look for something bigger" 
- "not ready now but interested in the market"
- "our lease is up in the fall"
- "when the kids graduate we might downsize"
- "not ready for about 6 months"
- "planning to move next spring"
- "considering our options for later this year"

SHORT_TERM_LEAD Examples:
- "looking to buy ASAP"
- "need to sell before we move next month"
- "can we see this property this weekend?"
- "ready to start looking now"
- "want to list within the next few weeks"

NONE Examples:
- "thanks for the birthday wishes"
- "how's the weather?"
- "got your message"
- "happy holidays"

CRITICAL: Focus on STRATEGIC OPPORTUNITY and TIMELINE, not just casual mentions.
If a client mentions ANY future timeline (2+ months), classify as LONG_TERM_NURTURE.
Do NOT add explanation, punctuation, or other text. Response must be a single keyword only.
"""

    prompt = f"Client message: '{message_content}'"

    try:
        response = await openai_service.generate_text_completion(
            prompt_messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            model="gpt-4o-mini"
        )

        detected_intent = response.strip().upper()
        logging.info(f"CONVERSATION AGENT (INTENT): Raw LLM response: '{response}'. Parsed intent: '{detected_intent}'")

        if detected_intent in ["LONG_TERM_NURTURE", "SHORT_TERM_LEAD"]:
            return detected_intent
        return None

    except Exception as e:
        logging.error(f"CONVERSATION AGENT (INTENT): Error detecting intent: {e}", exc_info=True)
        return None

async def draft_campaign_step_message(realtor: User, client: Client, prompt: str, delay_days: int) -> tuple[str, int]:
    """
    Uses an LLM to generate the full message content for a single step in a campaign playbook.
    """
    logging.info(f"CONVERSATION AGENT (CAMPAIGN STEP): Drafting message for client {client.id} with prompt: '{prompt[:50]}...'")

    style_prompt_addition = ""
    if realtor.ai_style_guide:
        try:
            style_rules = json.dumps(realtor.ai_style_guide, indent=2)
            style_prompt_addition = f"\n\nIMPORTANT: You MUST follow these style rules to match the user's voice:\n{style_rules}"
        except Exception as e:
            logging.error(f"CONVERSATION AGENT: Could not apply style guide. Error: {e}")

    full_prompt = f"""
    You are an AI assistant for a real estate agent named {realtor.full_name}.
    Your task is to draft a personalized, ready-to-send SMS message to a client named {client.full_name}.
    Use the client's first name, {client.full_name.split(' ')[0]}, for personalization.
    {style_prompt_addition}

    Instructions for this message: {prompt}

    Draft the complete SMS message now:
    """

    ai_draft = await openai_service.generate_text_completion(
        prompt_messages=[{"role": "user", "content": full_prompt}],
        model="gpt-4o-mini"
    )

    if not ai_draft:
        ai_draft = f"Hi {client.full_name.split(' ')[0]}, just checking in."
    
    # Return the generated content and the original delay_days for scheduling
    return ai_draft, delay_days