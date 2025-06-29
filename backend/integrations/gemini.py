# ---
# File Path: backend/integrations/gemini.py
# Purpose: Handles all communication with Google's Gemini models.
# ---
import os
import google.generativeai as genai
from typing import List

# Configure the API key from environment variables
# Ensure you have GOOGLE_API_KEY set in your environment.
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY environment variable not set.")

genai.configure(api_key=GOOGLE_API_KEY)

async def get_text_embedding(text: str) -> List[float]:
    """
    Generates a vector embedding for a given text using Google's embedding model.

    Args:
        text: The input string to embed.

    Returns:
        A list of floats representing the vector embedding.
    """
    try:
        # Use the recommended model for semantic search and retrieval
        result = await genai.embed_content_async(
            model="models/text-embedding-004",
            content=text,
            task_type="RETRIEVAL_QUERY"
        )
        return result['embedding']
    except Exception as e:
        print(f"GEMINI API ERROR: Could not generate embedding. {e}")
        # Return a zero-vector on error. The dimension (768) matches the model's output.
        return [0.0] * 768