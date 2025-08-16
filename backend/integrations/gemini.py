# ---
# File Path: backend/integrations/gemini.py
# Purpose: Handles all communication with Google's Gemini models.
# ---
import os
import json
import logging
import google.generativeai as genai
from typing import List, Optional

logger = logging.getLogger(__name__)

# Configure the API key from environment variables
# Ensure you have GOOGLE_API_KEY set in your environment.
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    # For testing purposes, use a dummy key instead of raising an error
    logger.warning("GOOGLE_API_KEY environment variable not set. Using dummy key for testing.")
    GOOGLE_API_KEY = "test-google-api-key"

# Only configure genai if we have a valid API key
if GOOGLE_API_KEY and GOOGLE_API_KEY != "test-google-api-key":
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

async def match_faq_with_gemini(user_query: str, faqs: List[dict]) -> Optional[str]:
    """
    Use Gemini to match user query against FAQ list and return appropriate response
    """
    if not faqs:
        return None
    
    # Create FAQ context as JSON
    faq_context = json.dumps(faqs, indent=2)
    
    prompt = f"""You are a helpful customer service assistant. A customer has asked a question, and you have access to a list of frequently asked questions and their answers.

Customer Question: "{user_query}"

Available FAQs:
{faq_context}

Instructions:
- If the customer's question matches any FAQ topic, provide the appropriate answer
- You may combine multiple relevant FAQ answers if needed
- Keep responses professional, helpful, and under 320 characters for SMS
- If no FAQ matches the question, respond with exactly "NO_MATCH"
- Do not make up information not in the FAQs

Response:"""

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.2,  # Low temperature for consistency
                max_output_tokens=150,
                candidate_count=1
            )
        )
        
        result = response.text.strip()
        logging.info(f"GEMINI FAQ: Query '{user_query}' -> Response '{result}'")
        
        return result if result != "NO_MATCH" else None
        
    except Exception as e:
        logging.error(f"GEMINI FAQ ERROR: {e}")
        return None

async def get_chat_completion(
    prompt_messages: List[dict] = None,
    prompt: str = None,
    model: str = "gemini-2.5-flash",
    temperature: float = 0.7,
    max_tokens: int = 1000,
    response_format: dict = None,
    **kwargs
) -> Optional[str]:
    """
    Gets a chat completion from Google Gemini 2.5 API.
    
    Args:
        prompt_messages: List of message dicts with 'role' and 'content' keys
        prompt: Single string prompt (alternative to prompt_messages)
        model: Gemini model to use (default: gemini-2.0-flash-exp)
        temperature: Controls randomness (0.0-1.0)
        max_tokens: Maximum tokens to generate
        response_format: Format specification (e.g., {"type": "json_object"})
        **kwargs: Additional arguments
    
    Returns:
        Generated text response or None on error
    """
    try:
        # Use Gemini 2.5 Flash for best performance
        genai_model = genai.GenerativeModel(model)
        
        # Prepare content based on input format
        if prompt_messages:
            # Convert OpenAI-style messages to Gemini format
            content_parts = []
            for msg in prompt_messages:
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                
                if role == 'system':
                    # Gemini doesn't have system messages, so we prepend to user message
                    content_parts.append(f"System: {content}")
                elif role in ['user', 'assistant']:
                    content_parts.append(f"{role.title()}: {content}")
            
            # Combine all content
            full_prompt = "\n\n".join(content_parts)
        elif prompt:
            full_prompt = prompt
        else:
            raise ValueError("Either prompt_messages or prompt must be provided")
        
        # Configure generation parameters
        generation_config = genai.types.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
            candidate_count=1
        )
        
        # Handle JSON response format
        if response_format and response_format.get("type") == "json_object":
            # Gemini's official JSON mode is activated by setting the response_mime_type.
            # This is more reliable than instructing it in the prompt.
            generation_config.response_mime_type = "application/json"
        
        # Generate response
        response = await genai_model.generate_content_async(
            full_prompt,
            generation_config=generation_config
        )
        
        result = response.text.strip()
        logger.info(f"GEMINI CHAT: Generated response with {len(result)} characters")
        
        return result
        
    except Exception as e:
        logger.error(f"GEMINI CHAT ERROR: {e}")
        return None

async def generate_text_completion(
    prompt_messages: List[dict] = None,
    prompt: str = None,
    model: str = "gemini-2.0-flash-exp",
    temperature: float = 0.7,
    max_tokens: int = 1000,
    response_format: dict = None,
    **kwargs
) -> Optional[str]:
    """
    Alias for get_chat_completion to maintain compatibility with existing code.
    """
    return await get_chat_completion(
        prompt_messages=prompt_messages,
        prompt=prompt,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        response_format=response_format,
        **kwargs
    )