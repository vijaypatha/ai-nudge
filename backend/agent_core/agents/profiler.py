# File Path: backend/agent_core/agents/profiler.py
# PURPOSE: An AI agent responsible for understanding client notes and extracting structured data.

import logging
import json
from typing import Dict, Any

from agent_core import llm_client

PROMPT_TEMPLATE = """
You are an expert real estate assistant. Your task is to analyze the provided text about a client and extract specific structured information.
Only extract information that is explicitly mentioned in the text. Do not make assumptions or infer values that are not present.
Your output MUST be a valid JSON object with ONLY the following keys. If a value is not found for a key, omit that key from the JSON object entirely.

- "budget_max": (integer) The client's maximum budget, written as a number without commas or symbols.
- "locations": (list of strings) A list of cities, neighborhoods, or areas the client is interested in.
- "min_bedrooms": (integer) The minimum number of bedrooms required.
- "min_bathrooms": (integer) The minimum number of bathrooms required.

Here is the text to analyze:
---
{client_notes_text}
---
"""

async def extract_preferences_from_text(text: str) -> Dict[str, Any]:
    """
    Uses an LLM to read unstructured text and extract structured client preferences.

    Args:
        text: The full text of the client's notes and tags.

    Returns:
        A dictionary containing the extracted preferences, or an empty dictionary if none are found or an error occurs.
    """
    if not text or not text.strip():
        return {}

    prompt = PROMPT_TEMPLATE.format(client_notes_text=text)
    logging.info("PROFILER AGENT: Extracting structured preferences from text...")

    try:
        # We use the raw chat completion here to get a JSON response
        response_text = await llm_client.get_chat_completion(
            prompt,
            temperature=0.0,
            json_response=True # Request JSON mode if available
        )
        
        if not response_text:
            logging.warning("PROFILER AGENT: Received an empty response from the LLM.")
            return {}

        extracted_data = json.loads(response_text)
        logging.info(f"PROFILER AGENT: Successfully extracted preferences: {extracted_data}")
        return extracted_data

    except json.JSONDecodeError as e:
        logging.error(f"PROFILER AGENT: Failed to decode JSON from LLM response: {e}\nResponse text: {response_text}", exc_info=True)
        return {}
    except Exception as e:
        logging.error(f"PROFILER AGENT: An unexpected error occurred during preference extraction: {e}", exc_info=True)
        return {}