# File Path: backend/agent_core/llm_client.py
# PURPOSE: A unified client for interacting with different LLM providers (OpenAI, Gemini, etc.).

import logging
from typing import List, Optional

from common.config import get_settings
from integrations.gemini import get_text_embedding as get_gemini_embedding, get_chat_completion as get_gemini_chat
from integrations.openai import get_text_embedding as get_openai_embedding, get_chat_completion as get_openai_chat

logger = logging.getLogger(__name__)

async def generate_embedding(text: str) -> List[float]:
    """
    Generates a vector embedding for a given text string using the configured LLM provider.
    This is used for semantic search and conceptual matching.
    """
    settings = get_settings()
    provider = settings.LLM_PROVIDER
    
    text_to_embed = text.strip() if text else ""
    if not text_to_embed:
        logger.warning("LLM CLIENT: generate_embedding called with empty text. Returning zero-vector.")
        return [0.0] * 1536

    max_length = 8192 
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
        return [0.0] * 1536

async def get_chat_completion(
    prompt: str,
    temperature: float = 0.7,
    max_tokens: int = 1024,
    json_response: bool = False
) -> Optional[str]:
    """
    Gets a chat completion from the configured LLM provider. This function now
    correctly formats the request for the underlying provider functions.
    """
    settings = get_settings()
    provider = settings.LLM_PROVIDER
    
    logger.info(f"LLM CLIENT: Requesting chat completion with provider '{provider}'...")
    
    # This is the critical change: construct the 'messages' list that the
    # underlying provider functions now expect.
    messages_payload = [{"role": "user", "content": prompt}]
    
    try:
        if provider.lower() == "openai":
            return await get_openai_chat(
                messages=messages_payload, 
                temperature=temperature, 
                max_tokens=max_tokens, 
                json_response=json_response
            )
        elif provider.lower() == "gemini":
            return await get_gemini_chat(
                messages=messages_payload, 
                temperature=temperature, 
                max_tokens=max_tokens, 
                json_response=json_response
            )
        else:
            raise ValueError(f"Unknown LLM_PROVIDER '{provider}' in settings.")
            
    except Exception as e:
        logger.error(f"LLM CLIENT: Error getting chat completion with {provider}: {e}", exc_info=True)
        return None