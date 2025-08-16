# File Path: backend/agent_core/agents/profiler.py
# PURPOSE: An AI agent responsible for synthesizing a complete client profile against a canonical schema.

import logging
import json
from typing import Dict, Any

from agent_core import llm_client

# Define the canonical schemas directly in the agent for clarity and control.
# These were finalized in our previous discussion.
CANONICAL_SCHEMAS = {
    "real_estate_buyer": {
        "objective": "str", "budget_max": "int", "preapproval_status": "str",
        "min_bedrooms": "int", "max_bedrooms": "int", "min_bathrooms": "float", "max_bathrooms": "float",
        "min_sqft": "int", "min_acreage": "float", "max_hoa_fee": "int", "min_year_built": "int",
        "property_types": "List[str]", "locations": "List[str]", "must_haves": "List[str]",
        "deal_breakers": "List[str]", "timeline": "str", "urgency_level": "str"
    },
    "real_estate_seller": {
        "property_address": "str", "property_type": "str", "bedrooms": "int", "bathrooms": "float",
        "sqft": "int", "acreage": "float", "year_built": "int", "property_condition": "str",
        "features_and_upgrades": "List[str]", "desired_sale_price": "int", "bottom_line_price": "int",
        "timeline_to_sell": "str", "ideal_closing_date": "str", "motivation_for_selling": "str",
        "is_occupied": "str", "remaining_mortgage": "int"
    },

    "therapy_client": {
        "primary_concerns": "List[str]",
        "therapy_experience": "str",
        "client_goals": "List[str]",
        "preferred_approaches": "List[str]",
        "session_frequency": "str",
        "urgency_level": "str"
    },
    # Add other vertical schemas here
}

async def synthesize_client_profile(
    text_to_analyze: str,
    user_vertical: str,
    client_role: str # e.g., "buyer" or "seller"
) -> Dict[str, Any]:
    """
    Synthesizes a client's profile by analyzing text and populating a canonical schema.
    
    Returns:
        A dictionary containing the 'ai_summary', 'actionable_intel', and structured 'preferences'.
    """
    if not text_to_analyze or not text_to_analyze.strip():
        return {}

    schema_key = f"{user_vertical}_{client_role}"
    schema = CANONICAL_SCHEMAS.get(schema_key)

    if not schema:
        logging.warning(f"PROFILER AGENT: No canonical schema found for key '{schema_key}'.")
        return {}

    schema_json_string = json.dumps(schema, indent=2)

    prompt = f"""
    You are an expert AI assistant for a {user_vertical} professional. Your task is to synthesize all available information about a client into a clean, structured profile.

    Analyze the provided text, which includes notes, conversation history, and survey answers.
    Your response MUST be a single JSON object with three top-level keys:
    1.  "ai_summary": A concise, 1-2 sentence summary of the client's current situation and goals.
    2.  "actionable_intel": A list of short, critical, time-sensitive action items. Examples: ["Appointment Requested", "Client is frustrated"]. If none, return an empty list.
    3.  "preferences": A JSON object that STRICTLY follows the canonical schema provided below.

    CANONICAL SCHEMA FOR "preferences":
    {schema_json_string}

    RULES:
    - Populate the "preferences" object using only information explicitly found in the text.
    - If a value for a field is not found, omit the key entirely. Do NOT invent data.
    - Convert numerical values (like budget or sqft) to integers, removing any symbols or commas.
    - The entire output must be a single, valid JSON object.

    Text to analyze:
    ---
    {text_to_analyze}
    ---

    Return ONLY the structured JSON object.
    """

    logging.info(f"PROFILER AGENT: Synthesizing profile against schema '{schema_key}'...")

    try:
        response_text = await llm_client.get_chat_completion(
            prompt,
            temperature=0.0,
            json_response=True
        )
        
        if not response_text:
            logging.warning("PROFILER AGENT: Received an empty response from the LLM.")
            return {}

        synthesized_data = json.loads(response_text)
        
        # Basic validation
        if not all(k in synthesized_data for k in ["ai_summary", "actionable_intel", "preferences"]):
            logging.error(f"PROFILER AGENT: LLM response was missing required top-level keys. Response: {response_text}")
            return {}

        logging.info(f"PROFILER AGENT: Successfully synthesized client profile.")
        return synthesized_data

    except json.JSONDecodeError as e:
        logging.error(f"PROFILER AGENT: Failed to decode JSON from LLM response: {e}\nResponse text: {response_text}", exc_info=True)
        return {}
    except Exception as e:
        logging.error(f"PROFILER AGENT: An unexpected error occurred during profile synthesis: {e}", exc_info=True)
        return {}