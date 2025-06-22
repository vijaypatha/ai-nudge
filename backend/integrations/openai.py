# backend/integrations/openai.py

import httpx # Import the httpx library
from openai import OpenAI, APIStatusError, AuthenticationError
from common.config import OPENAI_API_KEY

# Initialize the OpenAI client variable.
_openai_client = None

def get_openai_client() -> OpenAI:
    """
    Returns an initialized OpenAI client.
    Initializes it if it hasn't been already (singleton pattern).
    """
    global _openai_client
    if _openai_client is None:
        if not OPENAI_API_KEY:
            raise ValueError("OpenAI API Key is missing from environment variables.")
        
        # CORRECTED: Explicitly create an httpx.Client to pass to the OpenAI client.
        # This gives us full control and avoids issues where environment variables (like proxy settings)
        # can cause unexpected arguments to be passed during default client creation.
        http_client = httpx.Client()
        
        _openai_client = OpenAI(
            api_key=OPENAI_API_KEY,
            http_client=http_client # Pass the explicitly created client
        )
        print("OPENAI INTEGRATION: OpenAI client initialized successfully.")
    return _openai_client

async def generate_text_completion(prompt_messages: list, model: str = "gpt-4o-mini") -> str | None:
    """
    Generates a text completion using an OpenAI model.
    """
    try:
        client = get_openai_client()
        print(f"OPENAI INTEGRATION: Calling OpenAI model '{model}'...")

        response = client.chat.completions.create(
            model=model,
            messages=prompt_messages,
            temperature=0.7,
            max_tokens=150
        )
        
        if response.choices and response.choices[0].message.content:
            generated_text = response.choices[0].message.content.strip()
            print(f"OPENAI INTEGRATION: Received response: {generated_text[:50]}...")
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