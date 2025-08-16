# File Path: backend/agent_core/llm_client.py
# PURPOSE: Centralized LLM client for all AI operations.

import logging
import asyncio
from typing import List, Optional
from common.config import get_settings

logger = logging.getLogger(__name__)

async def generate_embedding(text: str) -> List[float]:
    """
    Generates embeddings for text using the configured LLM provider.
    Returns a zero vector if the API is not available or text is empty.
    """
    if not text or not text.strip():
        logger.warning("LLM CLIENT: generate_embedding called with empty text. Returning zero-vector.")
        return [0.0] * 768  # Gemini embedding dimension
    
    settings = get_settings()
    
    try:
        if settings.LLM_PROVIDER == "openai":
            return await _generate_openai_embedding(text)
        elif settings.LLM_PROVIDER == "gemini":
            return await _generate_gemini_embedding(text)
        else:
            logger.error(f"LLM CLIENT: Unsupported provider '{settings.LLM_PROVIDER}'")
            return [0.0] * 768
    except Exception as e:
        logger.error(f"LLM CLIENT: Failed to generate embedding: {e}")
        return [0.0] * 768

async def _generate_openai_embedding(text: str) -> List[float]:
    """Generates embedding using OpenAI API with proper error handling."""
    try:
        from integrations.openai import get_text_embedding
        return await get_text_embedding(text)
    except Exception as e:
        logger.error(f"LLM CLIENT: OpenAI embedding failed: {e}")
        return [0.0] * 768

async def _generate_gemini_embedding(text: str) -> List[float]:
    """Generates embedding using Gemini API with proper error handling."""
    try:
        from integrations.gemini import get_text_embedding
        return await get_text_embedding(text)
    except Exception as e:
        logger.error(f"LLM CLIENT: Gemini embedding failed: {e}")
        return [0.0] * 768

async def get_chat_completion(
    prompt: str,
    temperature: float = 0.7,
    max_tokens: int = 1024,
    json_response: bool = False
) -> Optional[str]:
    """
    Gets a chat completion from the configured LLM provider.
    """
    settings = get_settings()
    provider = settings.LLM_PROVIDER
    
    logger.info(f"LLM CLIENT: Requesting chat completion with provider '{provider}'...")
    
    try:
        if provider.lower() == "openai":
            from integrations.openai import get_chat_completion
            return await get_chat_completion(
                prompt=prompt, 
                temperature=temperature, 
                max_tokens=max_tokens, 
                json_response=json_response
            )
        elif provider.lower() == "gemini":
            from integrations.gemini import get_chat_completion as get_gemini_chat
            return await get_gemini_chat(
                prompt=prompt, 
                temperature=temperature, 
                max_tokens=max_tokens, 
                response_format={"type": "json_object"} if json_response else None
            )
        else:
            raise ValueError(f"Unknown LLM_PROVIDER '{provider}' in settings.")
            
    except Exception as e:
        logger.error(f"LLM CLIENT: Error getting chat completion with {provider}: {e}", exc_info=True)
        return None