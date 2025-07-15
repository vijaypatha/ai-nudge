# backend/agent_core/llm_client.py
# --- UPDATED: Now defaults to and calls the OpenAI embedding function.

import logging
from typing import List

from common.config import get_settings
# Import our specific provider integrations
from integrations.gemini import get_text_embedding as get_gemini_embedding
from integrations.openai import get_text_embedding as get_openai_embedding

logger = logging.getLogger(__name__)

async def generate_embedding(text: str) -> List[float]:
    """
    Generates a vector embedding using the configured LLM provider.
    """
    settings = get_settings()
    provider = settings.LLM_PROVIDER
    
    text_to_embed = text.strip()
    if not text_to_embed:
        logger.warning("LLM CLIENT: generate_embedding called with empty text. Returning zero-vector.")
        # Defaulting to OpenAI's embedding dimension
        return [0.0] * 1536

    max_length = 4096 # Truncate to a reasonable length
    if len(text_to_embed) > max_length:
        text_to_embed = text_to_embed[:max_length]
        logger.warning(f"LLM CLIENT: Text truncated to {max_length} characters for embedding.")

    logger.info(f"LLM CLIENT: Generating embedding with provider '{provider}'...")

    try:
        if provider.lower() == "openai":
            return await get_openai_embedding(text_to_embed)
        elif provider.lower() == "gemini":
            return await get_gemini_embedding(text_to_embed)
        else:
            raise ValueError(f"Unknown LLM_PROVIDER '{provider}' in settings.")
            
    except Exception as e:
        logger.error(f"LLM CLIENT: Error generating embedding with {provider}: {e}", exc_info=True)
        return [0.0] * 1536 # Default to OpenAI's dimension on error