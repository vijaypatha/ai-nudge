# File Path: backend/agent_core/agents/profiler.py
# PURPOSE: An AI agent responsible for understanding client notes and extracting structured data dynamically.

import logging
import json
from typing import Dict, Any

from agent_core import llm_client

async def extract_preferences_from_text(text: str, user_vertical: str = "general") -> Dict[str, Any]:
    """
    Dynamically extracts ANY preferences mentioned in client notes and conversations.
    No pre-defined fields - adapts to whatever is actually mentioned in the text.
    
    Args:
        text: The full text of the client's notes, tags, and conversation history.
        user_vertical: The professional's vertical (real_estate, therapy, etc.) for context.
    
    Returns:
        A dictionary containing dynamically discovered preferences, or an empty dictionary if none are found.
    """
    if not text or not text.strip():
        return {}

    # Dynamic prompt that adapts to any vertical and discovers what's mentioned
    prompt = f"""
    You are analyzing client notes and conversations for a {user_vertical} professional.
    
    Extract ALL preferences, requirements, or important details mentioned in the text.
    Return as JSON with FLAT keys (no nesting) based on what you actually find.
    
    Examples of what to look for (but don't limit yourself to these):
    - Budget information (any format: max_price, budget_range, etc.)
    - Location preferences (cities, neighborhoods, areas, proximity to things)
    - Feature requirements (bedrooms, bathrooms, amenities, specific features)
    - Personal preferences (style, approach, frequency, timing, etc.)
    - Deal-breakers or must-haves
    - Any other specific requirements, preferences, or important details
    
    Important:
    - Only extract information that is explicitly mentioned in the text
    - Use FLAT descriptive keys (no nested objects)
    - Don't make assumptions or infer values not present
    - Return valid JSON with whatever preferences you discover
    - Use simple key names like: min_sqft, home_office, budget_max, etc.
    
    Text to analyze:
    ---
    {text}
    ---
    
    Return ONLY valid JSON with FLAT descriptive keys based on the content found.
    """

    logging.info(f"PROFILER AGENT: Extracting dynamic preferences for {user_vertical} vertical...")

    try:
        # Get dynamic response from LLM
        response_text = await llm_client.get_chat_completion(
            prompt,
            temperature=0.0,
            json_response=True
        )
        
        if not response_text:
            logging.warning("PROFILER AGENT: Received an empty response from the LLM.")
            return {}

        extracted_data = json.loads(response_text)
        logging.info(f"PROFILER AGENT: Successfully extracted dynamic preferences: {extracted_data}")
        return extracted_data

    except json.JSONDecodeError as e:
        logging.error(f"PROFILER AGENT: Failed to decode JSON from LLM response: {e}\nResponse text: {response_text}", exc_info=True)
        return {}
    except Exception as e:
        logging.error(f"PROFILER AGENT: An unexpected error occurred during preference extraction: {e}", exc_info=True)
        return {}