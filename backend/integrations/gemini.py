# FILE: backend/integrations/gemini.py

# ---
# Purpose: Handles all communication with Google's Gemini models.
# ---

import os
import json
import asyncio
import logging
import google.generativeai as genai
from typing import List, Optional

logger = logging.getLogger(__name__)

# Gemini API has a limit on the number of documents per batch request.
GEMINI_BATCH_SIZE = 100

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    logger.warning("GOOGLE_API_KEY environment variable not set. Using dummy key for testing.")
    GOOGLE_API_KEY = "test-google-api-key"

if GOOGLE_API_KEY and GOOGLE_API_KEY != "test-google-api-key":
    genai.configure(api_key=GOOGLE_API_KEY)

async def get_text_embedding(text: str) -> List[float]:
    """Generates a vector embedding for a given text."""
    try:
        result = await genai.embed_content_async(
            model="models/text-embedding-004",
            content=text,
            task_type="RETRIEVAL_QUERY"
        )
        return result['embedding']
    except Exception as e:
        logger.error(f"LLM CLIENT: Gemini embedding failed: {e}")
        return [0.0] * 768

async def _embed_chunk(chunk: List[str]) -> List[List[float]]:
    """Helper to embed a single chunk and handle errors gracefully."""
    try:
        result = await genai.embed_content_async(
            model="models/text-embedding-004",
            content=chunk,
            task_type="RETRIEVAL_DOCUMENT"
        )
        return result['embedding']
    except Exception as e:
        logger.error(f"LLM CLIENT: Gemini embedding for a chunk failed: {e}")
        return [[0.0] * 768] * len(chunk)

async def get_text_embeddings_batched(texts: List[str]) -> List[List[float]]:
    """Generates vector embeddings for texts, handling API batch size limits with concurrent chunk processing."""
    if not texts:
        return []

    # Create and run concurrent tasks for each chunk
    tasks = [
        _embed_chunk(texts[i:i + GEMINI_BATCH_SIZE])
        for i in range(0, len(texts), GEMINI_BATCH_SIZE)
    ]
    chunk_results = await asyncio.gather(*tasks)

    # Flatten the list of lists into a single list of embeddings
    all_embeddings = [embedding for chunk in chunk_results for embedding in chunk]

    if len(all_embeddings) != len(texts):
        logger.error("LLM CLIENT: Mismatch in Gemini batch embedding results length. Returning all zero-vectors.")
        return [[0.0] * 768] * len(texts)

    return all_embeddings

async def match_faq_with_gemini(user_query: str, faqs: List[dict]) -> Optional[str]:
    """Match a user query against FAQ list."""
    if not faqs:
        return None
    faq_context = json.dumps(faqs, indent=2)
    prompt = (
        f"You are a helpful customer service assistant. Your task is to match a user's query to the most relevant FAQ from the list below.\n"
        f"If you find a relevant FAQ, respond with ONLY the answer from that FAQ.\n"
        f"If no FAQ is relevant, respond with exactly \"NO_MATCH\".\n"
        f"FAQs:\n{faq_context}\nUser Query: {user_query}"
    )
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = await model.generate_content_async(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.2,
                max_output_tokens=150,
                candidate_count=1
            )
        )
        if not response.candidates:
            logger.warning(f"GEMINI FAQ: Response was blocked or empty.")
            return None
        
        # Safe text extraction - FIXED: Added [0] indexing
        if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
            result = response.text.strip()
            return result if result != "NO_MATCH" else None
        else:
            logger.warning(f"GEMINI FAQ: No valid response parts. Finish reason: {response.candidates[0].finish_reason if response.candidates else 'No candidates'}")
            return None
    except Exception as e:
        logger.error(f"GEMINI FAQ ERROR: {e}")
        return None

async def get_chat_completion(
    prompt_messages: List[dict] = None,
    prompt: str = None,
    model: str = "gemini-2.5-flash",
    temperature: float = 0.7,
    max_tokens: int = 4097,
    response_format: dict = None,
    **kwargs
) -> Optional[str]:
    """Get a chat completion from Google Gemini 2.5 API."""
    try:
        system_instruction = None
        if prompt_messages:
            gemini_messages = []
            for msg in prompt_messages:
                role, content = msg.get('role'), msg.get('content', '')
                if role == 'system':
                    system_instruction = content
                elif role in ['user', 'assistant', 'model']:
                    gemini_messages.append({'role': 'model' if role != 'user' else 'user', 'parts': [content]})
            full_prompt = gemini_messages
        elif prompt:
            full_prompt = prompt
        else:
            raise ValueError("Either prompt_messages or prompt must be provided")

        genai_model = genai.GenerativeModel(model, system_instruction=system_instruction)
        generation_config = genai.types.GenerationConfig(
            temperature=temperature, max_output_tokens=max_tokens, candidate_count=1
        )
        if response_format and response_format.get("type") == "json_object":
            generation_config.response_mime_type = "application/json"
        
        safety_settings = {
            'HARM_CATEGORY_HARASSMENT': 'BLOCK_NONE',
            'HARM_CATEGORY_HATE_SPEECH': 'BLOCK_NONE',
            'HARM_CATEGORY_SEXUALLY_EXPLICIT': 'BLOCK_NONE',
            'HARM_CATEGORY_DANGEROUS_CONTENT': 'BLOCK_NONE',
        }
        
        response = await genai_model.generate_content_async(
            full_prompt, generation_config=generation_config, safety_settings=safety_settings
        )
        
        if not response.candidates:
            logger.warning(f"GEMINI CHAT: Response was blocked or empty.")
            return None
        
        # Safe text extraction with proper error handling - FIXED: Added [0] indexing
        if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
            return response.text.strip()
        else:
            finish_reason = response.candidates[0].finish_reason if response.candidates else "No candidates"
            logger.warning(f"GEMINI CHAT: No valid response parts. Finish reason: {finish_reason}")
            return None
            
    except Exception as e:
        logger.error(f"GEMINI CHAT ERROR: An unexpected error occurred: {e}", exc_info=True)
        return None

async def generate_text_completion(
    prompt_messages: List[dict] = None,
    prompt: str = None,
    model: str = "gemini-2.5-flash",
    temperature: float = 0.7,
    max_tokens: int = 4097,
    response_format: dict = None,
    **kwargs
) -> Optional[str]:
    """Alias for get_chat_completion to maintain compatibility with existing code."""
    return await get_chat_completion(
        prompt_messages=prompt_messages,
        prompt=prompt,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        response_format=response_format,
        **kwargs
    )
