# File Path: backend/integrations/openai.py
# PURPOSE: Integration functions for interacting with the OpenAI API.

import logging
from typing import List, Optional, Dict, Any
from functools import lru_cache
from openai import AsyncOpenAI, OpenAIError
import httpx

from common.config import get_settings

logger = logging.getLogger(__name__)

@lru_cache()
def get_async_client() -> AsyncOpenAI:
    """
    Initializes and returns a cached AsyncOpenAI client.
    This version manually creates the httpx.AsyncClient to prevent
    a version incompatibility issue with proxy settings.
    """
    logger.info("OPENAI INTEGRATION: Initializing new AsyncOpenAI client...")
    settings = get_settings()
    if not settings.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is not set in the environment.")

    # Manually create the httpx client with NO arguments to avoid the 'proxies' TypeError.
    http_client = httpx.AsyncClient()
    
    return AsyncOpenAI(api_key=settings.OPENAI_API_KEY, http_client=http_client)

async def get_text_embedding(text: str) -> List[float]:
    """
    Gets a text embedding from the OpenAI API.
    """
    try:
        client = get_async_client()
        response = await client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding
    except (OpenAIError, ValueError) as e:
        logger.error(f"OPENAI INTEGRATION: Error getting text embedding: {e}", exc_info=True)
        return [0.0] * 1536

async def get_chat_completion(
    messages: list,
    model: str = "gpt-4o-mini",
    temperature: float = 0.7,
    max_tokens: int = 1024,
    json_response: bool = False,
    **kwargs
) -> Optional[str]:
    """
    Gets a chat completion from the OpenAI API. This is the new, unified function
    that is backward-compatible with other parts of the system.
    """
    try:
        client = get_async_client()
        
        # This block handles arguments from both old and new code.
        # It prioritizes the 'response_format' from kwargs if present.
        if "response_format" in kwargs:
            pass # The argument is already in kwargs
        elif json_response:
            kwargs["response_format"] = {"type": "json_object"}
        
        logger.info(f"OPENAI INTEGRATION: Calling OpenAI model '{model}' with extra args: {kwargs}")

        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs # Pass all extra arguments
        )
        content = response.choices[0].message.content
        logger.info(f"OPENAI INTEGRATION: Received response: {content[:100]}...")
        return content
    except (OpenAIError, ValueError) as e:
        logger.error(f"OPENAI INTEGRATION: Error getting chat completion: {e}", exc_info=True)
        return None

async def generate_text_completion(prompt_messages: list, model: str = "gpt-4o-mini", **kwargs) -> str | None:
    """
    Generates a text completion using an OpenAI model.
    This function is preserved for backward compatibility and now calls the new unified function.
    """
    logger.info("Calling legacy 'generate_text_completion', redirecting to 'get_chat_completion'.")
    return await get_chat_completion(
        messages=prompt_messages,
        model=model,
        **kwargs
    )