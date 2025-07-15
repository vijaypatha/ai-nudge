# File Path: backend/integrations/openai.py
# --- UPDATED: Switched to the proper AsyncOpenAI client.

import httpx
from openai import AsyncOpenAI, APIStatusError, AuthenticationError # <-- MODIFIED: Import AsyncOpenAI
from common.config import get_settings
from typing import List

settings = get_settings()
_openai_client = None

# --- MODIFIED: This function now returns an AsyncOpenAI client ---
def get_openai_client() -> AsyncOpenAI:
    """
    Returns an initialized AsyncOpenAI client (singleton pattern).
    """
    global _openai_client
    if _openai_client is None:
        if not settings.OPENAI_API_KEY:
            raise ValueError("OpenAI API Key is missing from environment variables.")
        
        # httpx.AsyncClient is needed for AsyncOpenAI
        http_client = httpx.AsyncClient()
        
        _openai_client = AsyncOpenAI( # <-- MODIFIED: Instantiate AsyncOpenAI
            api_key=settings.OPENAI_API_KEY,
            http_client=http_client
        )
        print("OPENAI INTEGRATION: AsyncOpenAI client initialized successfully.")
    return _openai_client

async def generate_text_completion(prompt_messages: list, model: str = "gpt-4o-mini", **kwargs) -> str | None:
    """
    Generates a text completion using an OpenAI model.
    """
    try:
        client = get_openai_client()
        print(f"OPENAI INTEGRATION: Calling OpenAI model '{model}' with extra args: {kwargs}")

        # --- MODIFIED: Added 'await' as we are now using the async client ---
        response = await client.chat.completions.create(
            model=model,
            messages=prompt_messages,
            temperature=0.7,
            max_tokens=250,
            **kwargs 
        )
        
        if response.choices and response.choices[0].message.content:
            generated_text = response.choices[0].message.content.strip()
            print(f"OPENAI INTEGRATION: Received response: {generated_text[:70]}...")
            return generated_text
        return None

    except Exception as e:
        print(f"OPENAI INTEGRATION ERROR: An unexpected error occurred in text generation: {e}")
        return None

async def get_text_embedding(text: str, model="text-embedding-3-small") -> List[float]:
    """
    Generates a vector embedding for a given text using OpenAI's embedding models.
    """
    try:
        client = get_openai_client()
        text = text.replace("\n", " ")
        # The 'await' here is now correct because we are using the AsyncOpenAI client
        response = await client.embeddings.create(input=[text], model=model)
        return response.data[0].embedding
    except Exception as e:
        print(f"OPENAI INTEGRATION ERROR: Could not generate embedding. {e}")
        return [0.0] * 1536