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
    3.  **ALWAYS generate an `UPDATE_CLIENT_INTEL` recommendation** for ANY incoming message that contains useful information. This includes:
        - Personal details (family, work, interests, preferences, emotions)
        - Life events (moving, job changes, health updates, milestones)
        - Communication preferences (response style, timing, tone)
        - Goals, needs, or concerns they mention
        - Any context that would be valuable for future interactions
        - Even small details that could be useful for personalization
        - Emotional state or stress levels
        - Any information that helps understand the client better
    4.  **For tags**: ALWAYS suggest 1-3 relevant tags that would help categorize or understand the client. Examples: "first-time buyer", "relocating", "anxiety", "parenting", "work stress", "high school", "job change", "moving", "family", "stress", "excited", "concerned"
    5.  **For notes**: ALWAYS write a concise, actionable note that summarizes key information from the message. Focus on what's new or important.
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


async def draft_outbound_campaign_message(
    realtor: User,
    event_type: str,
    matched_audience: List[MatchedClient],
    resource: Resource | None = None,
    key_intel: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Uses a live LLM to draft a personalized outbound message for a campaign.
    This function is now vertical-agnostic by operating on a generic Resource.

    **FIX DOCUMENTATION:**
    - This function was failing to generate personalized messages for 'content_suggestion' events.
    - The logic checked for a `key_intel` dictionary, which was no longer being passed by the calling service.
    - The fix involves updating the condition to check for the `resource` object instead and extracting the necessary
      content details (title, topic, url) from `resource.attributes`.
    - This ensures the high-quality, specific prompt is used, solving the issue of generic messages.
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
    # Initialize final_draft to prevent potential UnboundLocalError
    final_draft = ""

    # FIX: The primary condition is changed from checking `key_intel` to checking `resource`.
    # This aligns with the data actually being passed to the function, ensuring this block is executed.
    if event_type == "content_suggestion" and resource and resource.attributes:
        attrs = resource.attributes
        client_name = matched_audience[0].client_name if matched_audience else 'there'
        match_reason = matched_audience[0].match_reasons[0] if matched_audience and matched_audience[0].match_reasons else 'based on our conversations'

        # FIX: Extract content details directly from `resource.attributes` instead of the non-existent `key_intel`.
        topic = attrs.get('topic', 'a relevant topic') # Fallback for safety
        content_title = attrs.get('title') # The presence of a title is a good indicator of valid content
        content_url = attrs.get('url')

        # If there's no title, we can't generate a good message. Fallback to a safe, generic message.
        if not content_title:
             logging.warning(f"CONVERSATION AGENT: 'content_suggestion' resource for user {realtor.id} is missing a title. Aborting specific message generation.")
             return "Hi [Client Name], I came across some information I thought you might find interesting. Let me know if you'd like me to send it over."

        # This is the high-quality prompt that was being skipped before the fix.
        base_message_prompt = f"""
        {base_prompt_intro}
        You are an empathetic, supportive, and professional therapist drafting a personalized SMS message to your client, {client_name}.
        The purpose is to share a helpful article or video related to a topic relevant to them, making the message personal and directly about the content.
        Here is the relevant information:
        - Client Name: {client_name}
        - Content Topic: {topic}
        - Content Title: "{content_title}"
        - Match Reason (why this content is relevant to the client): {match_reason}

        Draft a concise (under 160 characters if possible), personal, and supportive SMS message.
        Start with a friendly greeting like "Hey [Client Name]!".
        **Directly reference the content by its topic or title in the message body.**
        Explain briefly *why* you thought of them for this content (e.g., "thought of you because of our chat on X," or "came across this on Y and remembered Z").
        Conclude with a supportive closing.
        Crucially, **DO NOT include the link in your drafted message.** I will append the link separately.
        Example 1: "Hey [Client Name]! I came across this article on managing anxiety that reminded me of our last chat. Hope it offers some helpful perspective!"
        Example 2: "Hi [Client Name]! Just saw this great video about positive parenting techniques and immediately thought of you. Hope it's insightful!"
        """
        llm_response = await openai_service.generate_text_completion(
            prompt_messages=[
                {"role": "system", "content": base_message_prompt},
                {"role": "user", "content": "Draft the SMS message now:"}
            ],
            model="gpt-4o-mini"
        )
        if llm_response:
            final_draft = llm_response.strip()
        else:
            # Provide a structured fallback if the LLM fails, still using specific content details.
            final_draft = f"Hi {client_name}, I came across an article about {topic} titled \"{content_title}\" that I thought might be helpful."
        
        # Append the URL after the message is drafted, if it exists.
        if content_url:
            final_draft = f"{final_draft}\n\nHope you find it helpful: {content_url}"

        # Return the final message and exit the function, as the 'content_suggestion' case is fully handled.
        return final_draft

    elif event_type == "recency_nudge":
        client_name = matched_audience[0].client_name
        prompt = f"""
        {base_prompt_intro}
        A 'recency_nudge' event has occurred. This means the client, {client_name}, hasn't been contacted in a while.
        Your task is to draft a short, friendly, and low-pressure SMS message to check in.
        - Start with a warm greeting.
        - Mention it's been a little while and you were thinking of them.
        - Ask a simple, open-ended question like "How have you been?" or "How are things?".
        - Keep it brief and casual. Avoid sounding salesy or demanding.
        - The goal is to simply restart the conversation.
        """
    elif event_type == "listing_announcement":
        prompt = f"""
        {base_prompt_intro}
        A 'listing_announcement' event has occurred.
        A new property, described below, is now available. Your task is to draft a compelling announcement message.
        Here is the listing information:
        {json.dumps(resource.attributes, indent=2) if resource else "{}"}
        - Highlight 1-2 key features.
        - Include a call-to-action (e.g., "Let me know if you'd like to see it!").
        """
    # This `elif` block previously caused the bug. By handling `content_suggestion` explicitly above,
    # it now correctly serves as a fallback for other event types that have a resource but no special logic.
    elif resource:
        prompt = f"""
        {base_prompt_intro}
        A '{event_type}' event occurred.
        A relevant resource was found, with these attributes: {json.dumps(resource.attributes, indent=2) if resource else "{}"}
        Draft a generic but relevant message to share this with a client.
        """
    else:
        # Fallback for events without a resource
        prompt = f"A '{event_type}' event occurred. Draft a generic check-in message for a client."

    llm_response = await openai_service.generate_text_completion(
        prompt_messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": "Draft the message now:"}
        ],
        model="gpt-4o-mini"
    )

    return llm_response.strip() if llm_response else ""



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