# File Path: backend/integrations/openai.py
# --- CORRECTED: The text generation function now accepts additional keyword arguments.

import httpx
from openai import OpenAI, APIStatusError, AuthenticationError
from common.config import get_settings

settings = get_settings()
_openai_client = None

def get_openai_client() -> OpenAI:
    """
    Returns an initialized OpenAI client (singleton pattern).
    """
    global _openai_client
    if _openai_client is None:
        if not settings.OPENAI_API_KEY:
            raise ValueError("OpenAI API Key is missing from environment variables.")
        
        http_client = httpx.Client()
        
        _openai_client = OpenAI(
            api_key=settings.OPENAI_API_KEY,
            http_client=http_client
        )
        print("OPENAI INTEGRATION: OpenAI client initialized successfully.")
    return _openai_client

# --- MODIFIED: Added **kwargs to accept and pass through additional parameters ---
async def generate_text_completion(prompt_messages: list, model: str = "gpt-4o-mini", **kwargs) -> str | None:
    """
    Generates a text completion using an OpenAI model.
    Now accepts additional keyword arguments to pass to the OpenAI API.
    """
    try:
        client = get_openai_client()
        print(f"OPENAI INTEGRATION: Calling OpenAI model '{model}' with extra args: {kwargs}")

        # --- MODIFIED: Spread the kwargs into the create call ---
        # This allows us to pass new parameters like 'response_format' from the agent.
        response = client.chat.completions.create(
            model=model,
            messages=prompt_messages,
            temperature=0.7,
            max_tokens=250, # Increased max tokens for JSON mode
            **kwargs 
        )
        
        if response.choices and response.choices[0].message.content:
            generated_text = response.choices[0].message.content.strip()
            print(f"OPENAI INTEGRATION: Received response: {generated_text[:70]}...")
            return generated_text
        return None

    except AuthenticationError as auth_e:
        print(f"OPENAI INTEGRATION ERROR: Authentication failed: {auth_e}")
        return None
    except APIStatusError as status_e:
        print(f"OPENAI INTEGRATION ERROR: API error: {status_e.status_code} - {status_e.response}")
        return None
    except Exception as e:
        print(f"OPENAI INTEGRATION ERROR: An unexpected error occurred: {e}")
        return None