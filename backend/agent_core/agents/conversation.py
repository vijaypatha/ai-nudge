# FILE: backend/agent_core/agents/conversation.py
# --- FINAL, COMPLETE, AND CORRECTED VERSION ---

from typing import Dict, Any, List, Optional
import uuid
import json
import logging
import asyncio
from datetime import datetime, timezone
from sqlmodel import Session

from data.models.user import User
from data.models.resource import Resource
from data.models.campaign import MatchedClient
from data.models.message import Message, MessageDirection
from integrations import gemini as gemini_service
from data import crm as crm_service
from workflow.relationship_playbooks import IntentType
from data.models.client import Client

# Helper dictionary to make prompts vertically-aware
PROFESSIONAL_TITLES = {
    "real_estate": "real estate agent",
    "therapy": "therapist",
}

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
    
    system_prompt = f"""
    You are an expert assistant for {realtor.full_name}, a {professional_title}. Your assistant name is 'Co-Pilot'.{style_prompt_addition}
    Your task is to draft a friendly, professional, and engaging SMS message for a client.
    The topic or goal of the message is: "{topic}"
    
    Instructions:
    1. Draft a master SMS message. Use the placeholder `[Client Name]` for personalization.
    2. The tone should be warm and helpful, appropriate for the agent's profession.
    3. The message should be concise and end with an open-ended question to encourage a reply.
    """
    
    prompt_messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": "Draft the SMS message now:"}]

    ai_draft = await gemini_service.generate_text_completion(
        prompt_messages=prompt_messages
    )

    return ai_draft or f"Hi [Client Name], I was just thinking about you and wanted to reach out regarding {topic}."


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
    
    system_prompt = f"""
    You are an AI Co-Pilot for {realtor.full_name}, an expert in their field.
    Your task is to analyze the latest incoming message from a client and generate a structured JSON object of recommended actions.
    
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
    6.  **Format your entire output** as a single, valid JSON object following the schema provided.

    ## JSON OUTPUT SCHEMA
    ```json
    {json_schema}
    ```
    """

    conversation_str = ""
    for message in reversed(conversation_history):
        direction = "Client" if message.direction == "inbound" else "Agent"
        conversation_str += f"- {direction}: {message.content}\n"

    user_prompt = f"""
    ## CONTEXT
    - Client Name: {client_name}
    - Existing Client Tags: {client_tags}
    - Conversation History (most recent first):
    {conversation_str}
    
    ## LATEST INCOMING MESSAGE FROM {client_name}:
    "{incoming_message.content}"

    Now, generate the JSON output:
    """
    
    prompt_messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    logging.info(f"CO-PILOT AGENT: Sending prompt to LLM for client {client_id}.")
    raw_response = await gemini_service.generate_text_completion(
        prompt_messages=prompt_messages,
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
    """
    logging.info(f"CONVERSATION AGENT (OUTBOUND): Drafting message for event '{event_type}'...")
    style_prompt_addition = ""
    if realtor.ai_style_guide:
        try:
            style_rules = json.dumps(realtor.ai_style_guide, indent=2)
            style_prompt_addition = f"\n\nIMPORTANT: You MUST follow these style rules to match the user's voice:\n{style_rules}"
        except Exception as e:
            logging.error(f"CONVERSATION AGENT: Could not apply style guide. Error: {e}")

    professional_title = PROFESSIONAL_TITLES.get(realtor.vertical, "professional")
    base_prompt_intro = f"You are an expert assistant for a {professional_title}.{style_prompt_addition}"
    prompt_messages = []
    final_draft = ""

    if event_type == "content_suggestion" and resource and resource.attributes:
        attrs = resource.attributes
        client_name = matched_audience[0].client_name if matched_audience else 'there'
        match_reason = matched_audience[0].match_reasons[0] if matched_audience and matched_audience[0].match_reasons else 'based on our conversations'
        topic = attrs.get('topic', 'a relevant topic')
        content_title = attrs.get('title')
        content_url = attrs.get('url')

        if not content_title:
             logging.warning(f"CONVERSATION AGENT: 'content_suggestion' resource for user {realtor.id} is missing a title. Aborting specific message generation.")
             return "Hi [Client Name], I came across some information I thought you might find interesting. Let me know if you'd like me to send it over."

        system_prompt = f"""
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
        prompt_messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Draft the SMS message now:"}
        ]
        
        llm_response = await gemini_service.generate_text_completion(prompt_messages=prompt_messages)
        
        if llm_response:
            final_draft = llm_response.strip()
        else:
            final_draft = f"Hi {client_name}, I came across an article about {topic} titled \"{content_title}\" that I thought might be helpful."
        
        if content_url:
            final_draft = f"{final_draft}\n\nHope you find it helpful: {content_url}"

        return final_draft

    elif event_type in ["new_listing", "listing_announcement"]:
        attrs = resource.attributes if resource else {}
        address = attrs.get("UnparsedAddress", "a new property")
        price = attrs.get("ListPrice")
        beds = attrs.get("BedroomsTotal", "N/A")
        baths = attrs.get("BathroomsTotalInteger", "N/A")
        sqft = attrs.get("LivingArea")
        remarks = attrs.get("PublicRemarks") or ""

        price_display = f"${price:,.0f}" if isinstance(price, (int, float)) else "Contact for pricing"
        sqft_display = f"{sqft:,.0f}" if isinstance(sqft, (int, float)) else "Contact for details"
        
        media = attrs.get("Media", [])
        photo_count = len([m for m in media if m.get("MediaCategory") == "Photo"])
        
        client_context = ""
        if matched_audience:
            primary_client = matched_audience[0]
            client_name = primary_client.client_name
            match_reasons = primary_client.match_reasons or []
            
            if match_reasons:
                context_parts = []
                for reason in match_reasons:
                    if "bedrooms" in reason.lower() or "beds" in reason.lower():
                        context_parts.append("bedroom preferences")
                    elif "price" in reason.lower() or "budget" in reason.lower():
                        context_parts.append("price range")
                    elif "location" in reason.lower() or "area" in reason.lower():
                        context_parts.append("location preferences")
                    elif "investment" in reason.lower():
                        context_parts.append("investment goals")
                    elif "family" in reason.lower():
                        context_parts.append("family needs")
                    else:
                        context_parts.append("your preferences")
                
                if context_parts:
                    client_context = f" based on {', '.join(set(context_parts))}"
        
        system_prompt = f"""
        {base_prompt_intro}
        A 'listing_announcement' event has occurred.
        Draft a SHORT, compelling property announcement message (under 200 characters).
        
        Property Details:
        - Address: {address}
        - Price: {price_display}
        - Beds: {beds} | Baths: {baths} | SqFt: {sqft_display}
        - Photos: {photo_count} photos available
        - Description: {remarks[:100]}...
        
        Client Context: {client_context}
        
        Requirements:
        1. Keep it CONCISE and engaging
        2. Highlight 1-2 key features that match the client's preferences
        3. Include a simple call-to-action
        4. Use friendly, professional tone
        5. Start with "Hi [Client Name],"
        6. Make it personal based on client context - don't use generic "new listing alert"
        
        Examples based on context:
        - For bedroom preferences: "Hi [Client Name], found a {beds}bd home that matches your needs! {address} - {price_display}. Perfect size for your family."
        - For price range: "Hi [Client Name], this {address} property fits your budget perfectly! {beds}bd/{baths}ba, {price_display}. Worth checking out."
        - For location: "Hi [Client Name], new property in your preferred area! {address} - {beds}bd/{baths}ba, {price_display}. Great location match."
        - Generic: "Hi [Client Name], thought of you for this {address} property! {address} - {beds}bd/{baths}ba, {price_display}. Let me know if you'd like to see it."
        """
        prompt_messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Draft the message now:"}
        ]
    
    else: # Fallback for other event types
        if event_type == "recency_nudge":
            client_name = matched_audience[0].client_name
            system_prompt = f"""
            {base_prompt_intro}
            A 'recency_nudge' event has occurred. This means the client, {client_name}, hasn't been contacted in a while.
            Your task is to draft a short, friendly, and low-pressure SMS message to check in.
            - Start with a warm greeting.
            - Mention it's been a little while and you were thinking of them.
            - Ask a simple, open-ended question like "How have you been?" or "How are things?".
            - Keep it brief and casual. Avoid sounding salesy or demanding.
            - The goal is to simply restart the conversation.
            """
        elif resource:
            system_prompt = f"""
            {base_prompt_intro}
            A '{event_type}' event occurred.
            A relevant resource was found, with these attributes: {json.dumps(resource.attributes, indent=2) if resource else "{}"}
            Draft a generic but relevant message to share this with a client.
            """
        else:
            system_prompt = f"A '{event_type}' event occurred. Draft a generic check-in message for a client."
        
        prompt_messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Draft the message now:"}
        ]

    llm_response = await gemini_service.generate_text_completion(prompt_messages=prompt_messages)
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

    - "LONG_TERM_NURTURE": Client expresses future intent with timeline 2+ months OR shows buying/selling signals but not immediate urgency
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

    prompt_messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Client message: '{message_content}'"}
    ]

    try:
        response = await gemini_service.generate_text_completion(prompt_messages=prompt_messages)
        if not response: return None

        detected_intent_str = response.strip().upper()
        logging.info(f"CONVERSATION AGENT (INTENT): Raw LLM response: '{response}'. Parsed intent: '{detected_intent_str}'")

        if detected_intent_str in [IntentType.LONG_TERM_NURTURE.value, IntentType.SHORT_TERM_LEAD.value]:
            return IntentType(detected_intent_str)
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
            
    professional_title = PROFESSIONAL_TITLES.get(realtor.vertical, "professional")
    system_prompt = f"""
    You are an AI assistant for {realtor.full_name}, a {professional_title}.
    Your task is to draft a personalized, ready-to-send SMS message to a client named {client.full_name}.
    Use the client's first name, {client.full_name.split(' ')[0]}, for personalization.
    {style_prompt_addition}

    Instructions for this message: {prompt}
    """
    
    prompt_messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "Draft the complete SMS message now:"}
    ]

    ai_draft = await gemini_service.generate_text_completion(prompt_messages=prompt_messages)

    if not ai_draft:
        ai_draft = f"Hi {client.full_name.split(' ')[0]}, just checking in."

    return ai_draft, delay_days


def _trim_resource_for_prompt(resource: Resource) -> Dict[str, Any]:
    """A helper function to extract only the essential data from a verbose resource object."""
    attrs = resource.attributes
    return {
        "id": str(resource.id),
        "address": attrs.get("UnparsedAddress", "N/A"),
        "price": attrs.get("ListPrice"),
        "beds": attrs.get("BedroomsTotal"),
        "baths": attrs.get("BathroomsTotalInteger"),
        "sqft": attrs.get("LivingArea"),
        "remarks_snippet": (attrs.get("PublicRemarks") or "")[:250] + "..."
    }

async def draft_consolidated_nudge_with_commentary(
    realtor: User,
    client: Client,
    matches_to_process: List[Resource],
    total_matches_found: int,
    session: Session
) -> Dict[str, Any]:
    """
    Generates personalized commentaries for all curated matches using a structured prompt.
    """
    from backend.agent_core.brain.market_context import get_context_for_resource
    import json

    logging.info(f"CONVERSATION AGENT: Processing {len(matches_to_process)} curated matches for client {client.id}...")

    properties_for_ai = []
    for resource in matches_to_process:
        context = get_context_for_resource(resource, realtor, session)
        properties_for_ai.append({
            "details": _trim_resource_for_prompt(resource),
            "context": context
        })
    
    client_tags = (client.user_tags or []) + (client.ai_tags or [])
    client_persona = "Investor" if "investor" in [tag.lower() for tag in client_tags] else "Homebuyer"
    client_motivation = client.preferences.get('ai_summary', 'find a suitable property.')
    
    json_schema = """
    {
      "curation_rationale": "<A 1-2 sentence summary FOR THE AGENT explaining why these properties were chosen.>",
      "summary_draft": "<A concise, professional SMS summary draft FOR THE CLIENT.>",
      "commentaries": [
        { "id": "<property_id_1>", "commentary": "<Your one-sentence insight for property 1>" }
      ]
    }
    """

    system_prompt = f"""
    You are an expert real estate co-pilot for {realtor.full_name}.
    Your client is {client.full_name} ({client_persona}).
    Their core motivation is: "{client_motivation}"

    Your task is to generate a single JSON object with three parts:
    1. 'curation_rationale': A summary FOR THE AGENT explaining why these properties are a good fit.
    2. 'summary_draft': A concise, professional SMS message FOR THE CLIENT about the {len(matches_to_process)} curated properties.
    3. 'commentaries': A list of insightful, one-sentence commentaries FOR THE CLIENT, one for each property.

    **RULES:**
    - You MUST connect property features to the client's core motivation.
    - Be direct and data-driven. DO NOT use cliches like "gem" or "stunning."
    - The summary_draft must be under 160 characters and contain NO emojis.
    
    **REQUIRED JSON OUTPUT (no markdown):**
    {json_schema}
    """
    
    user_prompt = f"""
    **DATA TO ANALYZE:**
    {json.dumps(properties_for_ai, indent=2)}
    """
    
    prompt_messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    try:
        logging.info("CONVERSATION AGENT: Making single, unified AI call...")
        raw_response = await gemini_service.get_chat_completion(
            prompt_messages=prompt_messages, 
            response_format={"type": "json_object"}
        )
        
        if not raw_response:
            # If the AI call gracefully returns None, trigger the exception to use the fallback.
            raise ValueError("AI response was empty or blocked.")

        response_data = json.loads(raw_response)
        
        commentary_map = {item['id']: item['commentary'] for item in response_data.get("commentaries", [])}
        
        ordered_commentaries = [
            commentary_map.get(str(res.id), "This is a strong match based on your preferences.") 
            for res in matches_to_process
        ]
        
        return {
            "commentaries": ordered_commentaries,
            "summary_draft": response_data.get("summary_draft", f"Hi {client.full_name.split(' ')[0]}, I've curated {len(matches_to_process)} properties for you."),
            "curation_rationale": response_data.get("curation_rationale", "Top matches selected based on relevance.")
        }
    except Exception as e:
        logging.error(f"CONVERSATION AGENT: Unified AI call failed. Error: {e}", exc_info=True)
        return {
            "commentaries": ["This is an excellent match based on your preferences." for _ in matches_to_process],
            "summary_draft": f"Hi {client.full_name.split(' ')[0]}, I found {len(matches_to_process)} new properties worth reviewing.",
            "curation_rationale": "Top matches were selected based on relevance."
        }