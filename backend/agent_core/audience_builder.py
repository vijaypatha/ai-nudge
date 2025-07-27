# FILE: backend/agent_core/audience_builder.py
# --- REFACTORED: This module is now a simple pass-through to the centralized semantic_service ---

from typing import List
from uuid import UUID
import logging

# --- NEW: Import the centralized semantic service ---
from agent_core import semantic_service

async def initialize_client_index():
    """
    Initializes the in-memory vector index by calling the semantic service.
    """
    logging.info("AUDIENCE BUILDER: Delegating index initialization to Semantic Service.")
    await semantic_service.initialize_vector_index()

async def find_clients_by_semantic_query(query: str, top_k: int = 5, user_id: UUID = None) -> List[UUID]:
    """
    Finds clients by semantic query by calling the semantic service.
    Maintains the same function signature for compatibility with API endpoints.
    """
    logging.info(f"AUDIENCE BUILDER: Delegating semantic search for user {user_id} to Semantic Service.")
    return await semantic_service.find_similar_clients(
        query_text=query,
        user_id=user_id,
        top_k=top_k
    )