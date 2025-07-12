# ---
# File Path: backend/integrations/gemini.py
# Purpose: Handles all communication with Google's Gemini models.
# ---
import os
import json
import logging
import google.generativeai as genai
from typing import List, Optional

# Configure the API key from environment variables
# Ensure you have GOOGLE_API_KEY set in your environment.
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY environment variable not set.")

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