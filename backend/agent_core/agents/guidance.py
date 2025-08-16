# File Path: backend/agent_core/agents/guidance.py
# Purpose: An AI agent that generates personalized commentary for property matches.

import logging
import json
from typing import Dict, Any

from agent_core import llm_client
from data.models.client import Client
from data.models.resource import Resource

async def generate_match_commentary(client: Client, resource: Resource) -> str | None:
    """
    Analyzes a client's profile and a property's details to generate a concise,
    insightful note explaining why it's a good match.
    """
    if not client or not resource or not resource.attributes:
        return None

    client_prefs_str = json.dumps(client.preferences, indent=2)
    resource_attrs_str = json.dumps(resource.attributes, indent=2)

    prompt = f"""
    You are an expert real estate agent's AI assistant. Your task is to write a short, personalized "Agent's Note" for a property that has been matched with a client.
    The note should be 1-2 sentences and highlight the specific reasons this property is a great fit, based on the client's known preferences.

    RULES:
    - Be warm, insightful, and concise.
    - Directly reference 1-3 specific features from the client's preferences that the property has.
    - Do not invent features the property doesn't have.
    - Frame it as if the agent hand-picked this property.
    - The output should be ONLY the text of the note itself.

    Client Profile & Preferences:
    ---
    {client_prefs_str}
    ---

    Matched Property Details:
    ---
    {resource_attrs_str}
    ---

    Example Note: "I hand-picked this one for you. It has the large backyard you wanted and is zoned for Desert Hills High School, which I know is important."

    Write the "Agent's Note" now.
    """

    logging.info(f"GUIDANCE AGENT: Generating commentary for client {client.id} and resource {resource.id}")

    try:
        commentary = await llm_client.get_chat_completion(
            prompt,
            temperature=0.5,
            max_tokens=100
        )
        
        if commentary:
            # Clean up potential quotation marks from the LLM response
            return commentary.strip().strip('"')

        return None

    except Exception as e:
        logging.error(f"GUIDANCE AGENT: Error generating commentary: {e}", exc_info=True)
        return None