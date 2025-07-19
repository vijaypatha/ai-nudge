# ---
# File Path: backend/agent_core/audience_builder.py
# Purpose: This version has the DEFINITIVE, data-driven fix for the search feature.
# The similarity threshold has been tuned based on diagnostic logging.
# ---
import faiss
import numpy as np
from typing import List
from uuid import UUID

from data.models.client import Client
from data import crm as crm_service
from agent_core.llm_client import generate_embedding # Use the central client
import logging

DIMENSION = 1536
faiss_index = faiss.IndexFlatIP(DIMENSION)
faiss_index = faiss.IndexIDMap(faiss_index)
index_to_client_id: List[UUID] = []

async def initialize_client_index():
    """
    Builds the index from pre-generated embeddings on application startup.
    """
    global index_to_client_id
    faiss_index.reset()
    index_to_client_id = []

    logging.info("AUDIENCE BUILDER: Initializing client index...")
    clients = crm_service._get_all_clients_for_system_indexing()
    
    clients_with_embedding = [c for c in clients if c.notes and c.notes_embedding]
    
    if not clients_with_embedding:
        logging.warning("AUDIENCE BUILDER: No clients with pre-generated embeddings found. Index will be empty.")
        return

    logging.info(f"AUDIENCE BUILDER: Loading {len(clients_with_embedding)} existing client embeddings into index...")

    embeddings = np.array([c.notes_embedding for c in clients_with_embedding]).astype('float32')
    faiss.normalize_L2(embeddings)
    
    item_ids = np.arange(len(clients_with_embedding))

    faiss_index.add_with_ids(embeddings, item_ids)
    index_to_client_id = [c.id for c in clients_with_embedding]
    
    logging.info(f"AUDIENCE BUILDER: Index built successfully with {faiss_index.ntotal} vectors.")

async def find_clients_by_semantic_query(query: str, top_k: int = 5, user_id: UUID = None) -> List[UUID]:
    """
    Searches the pre-built index for relevant clients using Cosine Similarity.
    """
    if faiss_index.ntotal == 0:
        logging.warning("AUDIENCE BUILDER WARNING: Search attempted but index is empty.")
        return []

    logging.info(f"AUDIENCE BUILDER: Generating embedding for query: '{query}'")
    query_embedding = await generate_embedding(query)

    if query_embedding is None:
        return []
    
    k = min(top_k, faiss_index.ntotal)
    
    query_vector = np.array([query_embedding]).astype('float32')
    faiss.normalize_L2(query_vector)
    
    similarities, indices = faiss_index.search(query_vector, k=k)
    
    # --- THE FINAL FIX: Lowered threshold based on diagnostic data ---
    # The previous threshold of 0.8 was too high. The logs show that scores for
    # relevant queries are in the 0.3-0.5 range. This new value will
    # correctly capture these results.
    SIMILARITY_THRESHOLD = 0.35
    
    logging.info(f"AUDIENCE BUILDER DIAGNOSTICS: Raw similarities: {similarities[0]}")
    
    all_matched_client_ids = {
        index_to_client_id[i] for i, sim in zip(indices[0], similarities[0])
        if i != -1 and sim > SIMILARITY_THRESHOLD
    }
    
    logging.info(f"AUDIENCE BUILDER DIAGNOSTICS: Matched IDs post-similarity filter: {all_matched_client_ids}")

    if not user_id:
        return list(all_matched_client_ids)

    user_clients = crm_service.get_all_clients(user_id=user_id)
    user_client_ids = {c.id for c in user_clients}
    
    logging.info(f"AUDIENCE BUILDER DIAGNOSTICS: Client IDs for current user '{user_id}': {user_client_ids}")
    
    final_matched_ids = list(all_matched_client_ids.intersection(user_client_ids))

    logging.info(f"AUDIENCE BUILDER: Found {len(final_matched_ids)} relevant clients for query '{query}' for user {user_id}.")
    return final_matched_ids