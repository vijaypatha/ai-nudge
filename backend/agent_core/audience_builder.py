# ---
# File Path: backend/agent_core/audience_builder.py
# Purpose: This version is RE-ARCHITECTED to build the index only once on startup.
# It also adjusts the distance threshold for better relevance.
# ---
import faiss
import numpy as np
from typing import List
from uuid import UUID

from data.models.client import Client
from data import crm as crm_service
from integrations import gemini as gemini_integration

DIMENSION = 768
faiss_index = faiss.IndexFlatL2(DIMENSION)
faiss_index = faiss.IndexIDMap(faiss_index)
index_to_client_id: List[UUID] = []

async def initialize_client_index():
    """
    NEW: This function gets all clients and builds the index.
    It is called only once when the application starts.
    """
    global index_to_client_id
    faiss_index.reset()
    index_to_client_id = []

    print("AUDIENCE BUILDER: Initializing client index...")
    # --- MODIFIED: Call the new system-level function ---
    clients = crm_service._get_all_clients_for_system_indexing()
    clients_with_notes = [c for c in clients if c.preferences and c.preferences.get("notes")]
    
    if not clients_with_notes:
        print("AUDIENCE BUILDER: No client notes found to build index.")
        return

    print(f"AUDIENCE BUILDER: Generating embeddings for {len(clients_with_notes)} clients via Gemini API...")
    all_notes = [" ".join(c.preferences.get("notes", [])) for c in clients_with_notes]
    embeddings = [await gemini_integration.get_text_embedding(note) for note in all_notes]

    # Filter out any potential None values from embeddings before converting to numpy array
    valid_embeddings = [emb for emb in embeddings if emb is not None]
    valid_clients = [client for client, emb in zip(clients_with_notes, embeddings) if emb is not None]

    if not valid_embeddings:
        print("AUDIENCE BUILDER: No valid embeddings were generated. Index will not be built.")
        return

    item_ids = np.arange(len(valid_clients))
    faiss_index.add_with_ids(np.array(valid_embeddings).astype('float32'), item_ids)
    index_to_client_id = [c.id for c in valid_clients]
    
    print(f"AUDIENCE BUILDER: Index built successfully with {faiss_index.ntotal} vectors.")

async def find_clients_by_semantic_query(query: str, top_k: int = 5, user_id: UUID = None) -> List[UUID]:
    """
    Searches the pre-built index for relevant clients.
    Now accepts a user_id to filter results.
    """
    if faiss_index.ntotal == 0:
        print("AUDIENCE BUILDER WARNING: Search attempted but index is empty.")
        return []

    print(f"AUDIENCE BUILDER: Generating embedding for query '{query}' via Gemini API...")
    query_embedding = await gemini_integration.get_text_embedding(query)

    if query_embedding is None:
        return []
    
    k = min(top_k, faiss_index.ntotal)
    
    distances, indices = faiss_index.search(np.array([query_embedding]).astype('float32'), k=k)
    
    DISTANCE_THRESHOLD = 1.2
    
    print(f"AUDIENCE BUILDER: Search results (Distances): {distances[0]}")
    
    all_matched_client_ids = {
        index_to_client_id[i] for i, dist in zip(indices[0], distances[0])
        if i != -1 and dist < DISTANCE_THRESHOLD
    }

    if not user_id:
        return list(all_matched_client_ids)

    # Filter the results to only include clients belonging to the specified user
    user_clients = crm_service.get_all_clients(user_id=user_id)
    user_client_ids = {c.id for c in user_clients}
    
    final_matched_ids = list(all_matched_client_ids.intersection(user_client_ids))

    print(f"AUDIENCE BUILDER: Found {len(final_matched_ids)} relevant clients for query '{query}' for user {user_id}.")
    return final_matched_ids