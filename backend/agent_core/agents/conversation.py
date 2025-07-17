# File Path: backend/agent_core/agents/conversation.py
# --- FINAL, COMPLETE, AND CORRECTED VERSION ---

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

# Helper dictionary to make prompts vertically-aware
PROFESSIONAL_TITLES = {
    "real_estate": "real estate agent",
    "therapy": "therapist",
}

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

    professional_title = PROFESSIONAL_TITLES.get(realtor.vertical, "professional")
    base_prompt_intro = f"You are an expert assistant for {realtor.full_name}, a {professional_title}. Your assistant name is 'Co-Pilot'.{style_prompt_addition}"

    prompt = f"""
    {base_prompt_intro}
    Your task is to draft a friendly, professional, and engaging SMS message for a client.
    The topic or goal of the message is: "{topic}"
    Instructions:
    1. Draft a master SMS message. Use the placeholder `[Client Name]` for personalization.
    2. The tone should be warm and helpful, appropriate for the agent's profession.
    3. The message should be concise and end with an open-ended question to encourage a reply.

    Draft the SMS message now:
    """

    ai_draft = await openai_service.generate_text_completion(
        prompt_messages=[{"role": "user", "content": prompt}],
        model="gpt-4o-mini"
    )

    return ai_draft or f"Hi [Client Name], I was just thinking about you and wanted to reach out regarding {topic}."


# --- MODIFIED: Prompt is refined for better balance and smarter suggestions. ---
async def generate_recommendation_slate(
    realtor: User,
    client_id: uuid.UUID,
    incoming_message: Message,
    conversation_history: List[Message]
) -> Dict[str, Any]:
    """
    Analyzes an incoming message and generates a structured slate of recommendations.
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
          "payload": { "tags_to_add": ["<tag1>", "<tag2>"], "notes_to_add": "<A concise note summarizing new client intel>" }
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
    1.  **Analyze ONLY the LATEST INCOMING MESSAGE** in the context of the history.
    2.  **You MUST ALWAYS generate a helpful SMS response draft.** This is your primary function. Your response should be encouraging and move the conversation forward.
    3.  **GENERATE an `UPDATE_CLIENT_INTEL` recommendation ONLY IF the latest message contains NEW, ACTIONABLE intelligence** like a timeline, a specific goal, a new pain point, or contact information. Do NOT generate intel for simple pleasantries or acknowledgements.
    4.  **Format your entire output** as a single, valid JSON object following the schema provided.

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
    if not raw_response: return {}
    try:
        return json.loads(raw_response)
    except json.JSONDecodeError:
        logging.error(f"CO-PILOT AGENT: Failed to parse JSON from LLM response. Raw response: {raw_response}")
        return {}


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
    
    professional_title = PROFESSIONAL_TITLES.get(realtor.vertical, "professional")
    base_prompt_intro = f"You are an expert assistant for a {professional_title}.{style_prompt_addition}"

    prompt = ""
    # This section contains multiple prompts that need to be generic. 
    # The base_prompt_intro is now agnostic, and specific prompts below are reviewed for generic language.
    # The existing logic is mostly fine as it's event-driven, but the intro was the main issue.
    if event_type == "recency_nudge":
        prompt = f"""
        {base_prompt_intro}
        Your user, {realtor.full_name}, hasn't spoken to these clients in a while and wants to reconnect.
        Your task is to draft a friendly, casual, and short "checking in" SMS message.
        Instructions:
        1. Draft a master SMS message. Use the placeholder `[Client Name]` for personalization.
        2. The tone should be warm and relationship-focused, not salesy.
        3. The goal is simply to restart the conversation. Ask an open-ended question.
        Draft the SMS message now:
        """
    elif event_type == "sold_listing" and resource:
        attrs = resource.attributes
        prompt = f"""
        {base_prompt_intro}
        Your task is to draft a compelling, value-driven SMS message about a nearby property that just sold.
        This is for clients who might be thinking of selling their own homes.
        User's Name: {realtor.full_name}
        Context: The property at {attrs.get('address', 'N/A')} just sold for ${attrs.get('price', 0):,.0f}.
        Instructions:
        1. Draft a master SMS message. Use `[Client Name]` for personalization.
        2. The tone should be insightful and create urgency/opportunity.
        3. Start a conversation by asking if they've considered what this news means for their own home's value.
        4. Keep it concise for SMS. Do NOT include a listing URL.
        Draft the SMS message now:
        """
    # Other specific event_types like back_on_market, expired_listing, etc., follow.
    # The key change is the agnostic `base_prompt_intro`. The rest of the logic can stay.
    elif resource:
        attrs = resource.attributes
        prompt = f"""
        {base_prompt_intro}
        Your user is {realtor.full_name}.
        Your task is to draft a compelling and slightly informal master SMS message.
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


async def detect_conversational_intent(message_content: str, user: User) -> Optional[IntentType]:
    """
    Analyzes the content of a message to detect specific user intents
    that could trigger a multi-step relationship playbook.
    """
    logging.info(f"CONVERSATION AGENT (INTENT): Analyzing message for strategic intent...")
    
    professional_title = PROFESSIONAL_TITLES.get(user.vertical, "professionals")
    system_prompt = f"""
    You are a strategic relationship intelligence system for {professional_title}.
    Your ONLY job is to identify HIGH-VALUE opportunities that require multi-step nurturing campaigns.

    You MUST respond with EXACTLY ONE of these classifications:

    - "LONG_TERM_NURTURE": Client expresses future intent with timeline 2+ months OR shows buying/selling signals but   not immediate urgency
    - "SHORT_TERM_LEAD": Client shows immediate urgency (under 2 months) OR requests immediate action
    - "NONE": Casual conversation with no strategic opportunity

    LONG_TERM_NURTURE Examples:
    - "thinking about selling in 6 months"
    - "maybe next year we'll look for something bigger"
    - "not ready now but interested in the market"

    SHORT_TERM_LEAD Examples:
    - "looking to buy ASAP"
    - "need to sell before we move next month"
    - "can we see this property this weekend?"

    NONE Examples:
    - "thanks for the birthday wishes"
    - "how's the weather?"
    - "got your message"

    CRITICAL: Focus on STRATEGIC OPPORTUNITY and TIMELINE.
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


# This is the correct, final version of this function. The duplicate has been removed.
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
            
    professional_title = PROFESSIONAL_TITLES.get(realtor.vertical, "professional")
    full_prompt = f"""
    You are an AI assistant for {realtor.full_name}, a {professional_title}.
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