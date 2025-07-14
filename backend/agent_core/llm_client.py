# backend/agent_core/llm_client.py
# --- REPLACED: This is now a functional, production-ready abstraction layer. ---
import logging
from typing import List

from common.config import get_settings
# Import our specific provider integrations
from integrations.gemini import get_text_embedding as get_gemini_embedding
# from integrations.openai import get_text_embedding as get_openai_embedding # Future use

logger = logging.getLogger(__name__)

async def generate_embedding(text: str) -> List[float]:
    """
    Generates a vector embedding for a given text using the configured LLM provider.
    This is the single point of entry for all embedding tasks in the application.

    Args:
        text: The input string to embed.

    Returns:
        A list of floats representing the vector embedding.
    """
    settings = get_settings()
    provider = settings.LLM_PROVIDER
    
    # Clean and truncate text to avoid excessive API usage
    text_to_embed = text.strip()
    if not text_to_embed:
        logger.warning("LLM CLIENT: generate_embedding called with empty text. Returning zero-vector.")
        return [0.0] * 768 # Return a zero-vector of Gemini's expected dimension

    # Truncate to a reasonable length to control costs and stay within model limits
    max_length = 2048
    if len(text_to_embed) > max_length:
        text_to_embed = text_to_embed[:max_length]
        logger.warning(f"LLM CLIENT: Text truncated to {max_length} characters for embedding.")

    logger.info(f"LLM CLIENT: Generating embedding with provider '{provider}' for text: '{text_to_embed[:60]}...'")

    try:
        if provider.lower() == "gemini":
            return await get_gemini_embedding(text_to_embed)
        elif provider.lower() == "openai":
            # This is where we would call the OpenAI embedding function
            # return await get_openai_embedding(text_to_embed)
            raise NotImplementedError("OpenAI embedding function is not yet implemented.")
        else:
            raise ValueError(f"Unknown LLM_PROVIDER '{provider}' in settings.")
            
    except Exception as e:
        logger.error(f"LLM CLIENT: Error generating embedding with {provider}: {e}", exc_info=True)
        # Return a zero-vector on any error to prevent crashes downstream
        return [0.0] * 768