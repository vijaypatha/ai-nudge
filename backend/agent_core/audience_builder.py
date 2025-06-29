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
    clients = crm_service.get_all_clients()
    clients_with_notes = [c for c in clients if c.preferences.get("notes")]
    
    if not clients_with_notes:
        print("AUDIENCE BUILDER: No client notes found to build index.")
        return

    print(f"AUDIENCE BUILDER: Generating embeddings for {len(clients_with_notes)} clients via Gemini API...")
    all_notes = [" ".join(c.preferences.get("notes", [])) for c in clients_with_notes]
    embeddings = [await gemini_integration.get_text_embedding(note) for note in all_notes]

    item_ids = np.arange(len(clients_with_notes))
    faiss_index.add_with_ids(np.array(embeddings).astype('float32'), item_ids)
    index_to_client_id = [c.id for c in clients_with_notes]
    
    print(f"AUDIENCE BUILDER: Index built successfully with {faiss_index.ntotal} vectors.")

async def find_clients_by_semantic_query(query: str, top_k: int = 5) -> List[UUID]:
    """
    Searches the pre-built index for relevant clients.
    """
    if faiss_index.ntotal == 0:
        print("AUDIENCE BUILDER WARNING: Search attempted but index is empty.")
        return []

    print(f"AUDIENCE BUILDER: Generating embedding for query '{query}' via Gemini API...")
    query_embedding = await gemini_integration.get_text_embedding(query)
    
    # Ensure k is not greater than the number of items in the index
    k = min(top_k, faiss_index.ntotal)
    
    distances, indices = faiss_index.search(np.array([query_embedding]).astype('float32'), k=k)
    
    # CORRECTED: The distance threshold was too strict. Increased to allow for relevant matches.
    # L2 distance is different from cosine similarity; a higher value can still be a good match.
    # We also print the distances for debugging.
    DISTANCE_THRESHOLD = 1.2
    
    print(f"AUDIENCE BUILDER: Search results (Distances): {distances[0]}")
    
    matched_client_ids = [
        index_to_client_id[i] for i, dist in zip(indices[0], distances[0])
        if i != -1 and dist < DISTANCE_THRESHOLD
    ]

    print(f"AUDIENCE BUILDER: Found {len(matched_client_ids)} relevant clients for query '{query}'.")
    return matched_client_ids