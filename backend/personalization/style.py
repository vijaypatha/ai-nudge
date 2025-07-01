# ---
# File Path: backend/personalization/style.py
# Purpose: Implements the AI's ability to learn the user's writing style.
# ---

from typing import Dict, Any, Optional
import json

from data.models.user import User
from data import crm as crm_service
from integrations import openai as openai_service

async def learn_from_edit(user: User, original_draft: str, edited_draft: str) -> bool:
    """
    Analyzes the difference between an original and edited draft to learn the user's style.

    This function sends both versions to an LLM, asks it to generate a "style guide",
    and then saves that guide back to the user's profile in the database.

    Args:
        user (User): The user who made the edit.
        original_draft (str): The AI's original message draft.
        edited_draft (str): The user's final, edited version.

    Returns:
        bool: True if a new style guide was successfully generated and saved, False otherwise.
    """
    print(f"STYLE ADAPTATION: Learning from edit for user {user.id}...")

    # If there's no meaningful change, don't waste an API call.
    if original_draft.strip() == edited_draft.strip():
        print("STYLE ADAPTATION: No changes detected. Skipping learning.")
        return False

    # This prompt asks the LLM to act as a style analyst.
    prompt = f"""
    Analyze the difference between the ORIGINAL and EDITED text below.
    Based on the changes, generate a concise JSON object describing the user's writing style.

    The JSON object should contain rules and preferences covering:
    - "tone": (e.g., "casual", "formal", "enthusiastic")
    - "greeting": (e.g., "prefers 'Hey' over 'Hi'")
    - "emojis": (e.g., "uses emojis like '🌟' and '🚀'")
    - "phrasing": (e.g., "prefers shorter sentences", "avoids jargon")
    - "call_to_action": (e.g., "prefers open-ended questions like 'what are your thoughts?'")

    ---
    ORIGINAL:
    {original_draft}
    ---
    EDITED:
    {edited_draft}
    ---

    Generate the JSON style guide now:
    """

    try:
        response_text = await openai_service.generate_text_completion(
            prompt_messages=[{"role": "user", "content": prompt}],
            model="gpt-4o-mini", # Using a powerful model for better analysis
            is_json=True # Instruct the LLM to return valid JSON
        )
        
        if not response_text:
            raise ValueError("LLM returned an empty response.")

        new_style_guide = json.loads(response_text)
        print(f"STYLE ADAPTATION: New style guide generated: {new_style_guide}")

        # Save the new style guide to the user's profile
        user.ai_style_guide = new_style_guide
        crm_service.update_user(user.id, user) # We'll need to create this CRM function
        
        print(f"STYLE ADAPTATION: Style guide for user {user.id} updated successfully.")
        return True

    except Exception as e:
        print(f"STYLE ADAPTATION: ERROR - Failed to generate or save style guide: {e}")
        return False

