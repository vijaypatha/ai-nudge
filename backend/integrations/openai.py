# backend/integrations/openai.py

# Import the OpenAI client library.
from openai import OpenAI, APIStatusError, AuthenticationError
# Import your configuration settings, which contain your OpenAI API Key.
from backend.common.config import OPENAI_API_KEY

# Initialize the OpenAI client.
# This client object is used to make all API calls to OpenAI's models.
# It uses the API key loaded from your environment variables.
_openai_client = None

def get_openai_client() -> OpenAI:
    """
    Returns an initialized OpenAI client.
    Initializes it if it hasn't been already.
    Ensures the client is only created once (singleton pattern) and handles API key validation.
    """
    global _openai_client
    if _openai_client is None:
        if not OPENAI_API_KEY:
            # Raise an error if the API key is missing, preventing unauthenticated API calls.
            raise ValueError("OpenAI API Key is missing from environment variables.")
        _openai_client = OpenAI(api_key=OPENAI_API_KEY)
        print("OPENAI INTEGRATION: OpenAI client initialized.")
    return _openai_client

async def generate_text_completion(prompt_messages: list, model: str = "gpt-4o-mini") -> str | None:
    """
    Generates a text completion (response) using an OpenAI large language model (LLM).

    How it works for the robot: This is like the robot asking its supercomputer brain
    a question and getting a very smart, human-like answer back.

    - **prompt_messages**: A list of message dictionaries in the OpenAI chat format.
      Example: [{"role": "user", "content": "Hello, how are you?"}]
    - **model**: The name of the OpenAI model to use (defaulting to gpt-4o-mini for efficiency).
    Returns the generated text content as a string, or None if an error occurs.
    """
    try:
        client = get_openai_client() # Get the initialized OpenAI client
        print(f"OPENAI INTEGRATION: Calling OpenAI model '{model}' with prompt: {prompt_messages[0]['content'][:50]}...")

        # Make the API call to OpenAI for chat completion.
        # 'messages' is the conversation history.
        # 'temperature' controls randomness (lower = more focused).
        response = client.chat.completions.create(
            model=model,
            messages=prompt_messages,
            temperature=0.7,
            max_tokens=150 # Limit response length for conciseness
        )
        
        # Extract the content from the first choice in the response.
        if response.choices and response.choices[0].message.content:
            generated_text = response.choices[0].message.content.strip()
            print(f"OPENAI INTEGRATION: Received response: {generated_text[:50]}...")
            return generated_text
        return None

    except AuthenticationError as auth_e:
        # Handles errors related to invalid or missing API keys.
        print(f"OPENAI INTEGRATION ERROR: Authentication failed: {auth_e}")
        return None
    except APIStatusError as status_e:
        # Handles errors related to API calls (e.g., rate limits, server errors).
        print(f"OPENAI INTEGRATION ERROR: API error: {status_e.status_code} - {status_e.response}")
        return None
    except Exception as e:
        # Catches any other unexpected errors.
        print(f"OPENAI INTEGRATION ERROR: An unexpected error occurred: {e}")
        return None