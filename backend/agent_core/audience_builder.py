# File Path: backend/agent_core/audience_builder.py
# Purpose: Implements semantic search logic to find clients based on natural language queries.

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Optional
from uuid import UUID

from data.models.client import Client

# Load a pre-trained model for creating sentence embeddings.
# This model is optimized for semantic search.
model = SentenceTransformer('all-MiniLM-L6-v2')

# In-memory FAISS index. For a production environment, this would be persisted.
# The dimension (384) is specific to the 'all-MiniLM-L6-v2' model.
dimension = 384
faiss_index = faiss.IndexFlatL2(dimension)
faiss_index = faiss.IndexIDMap(faiss_index)

# A mapping from FAISS index IDs to our internal client UUIDs.
# The integer ID in the map corresponds to the client's position in the original list.
index_to_client_id: List[UUID] = []

def build_or_rebuild_client_index(clients: List[Client]):
    """
    (Core Logic) Clears and rebuilds the FAISS index from a list of clients.
    It vectorizes the 'notes' from each client's preferences.
    """
    global index_to_client_id
    faiss_index.reset()
    index_to_client_id = []

    # Collect all notes to be embedded.
    client_notes = [
        " ".join(client.preferences.get("notes", [])) for client in clients
        if client.preferences.get("notes")
    ]
    
    # Store corresponding client IDs for notes that exist.
    client_ids_with_notes = [
        client.id for client in clients if client.preferences.get("notes")
    ]
    
    if not client_notes:
        print("AUDIENCE BUILDER: No client notes found to build index.")
        return

    print(f"AUDIENCE BUILDER: Building index for {len(client_notes)} clients with notes.")
    
    # Generate embeddings for all notes in a single batch.
    embeddings = model.encode(client_notes, convert_to_tensor=False)
    
    # The IDs we add to FAISS are just integer positions (0, 1, 2, ...).
    item_ids = np.arange(len(client_ids_with_notes))

    # Add the embeddings and their integer IDs to the index.
    faiss_index.add_with_ids(np.array(embeddings).astype('float32'), item_ids)
    
    # Store the actual client UUIDs at the corresponding integer position.
    index_to_client_id = client_ids_with_notes
    print(f"AUDIENCE BUILDER: Index built successfully with {faiss_index.ntotal} vectors.")


def find_clients_by_semantic_query(query: str, top_k: int = 5) -> List[UUID]:
    """
    (Core Logic) Searches the FAISS index for clients whose notes match a natural language query.
    """
    if faiss_index.ntotal == 0:
        print("AUDIENCE BUILDER: Index is empty, cannot perform search.")
        return []

    # Encode the user's query into a vector.
    query_embedding = model.encode([query], convert_to_tensor=False)
    
    # Search the index for the 'top_k' most similar vectors.
    distances, indices = faiss_index.search(np.array(query_embedding).astype('float32'), top_k)
    
    # The 'indices' returned by FAISS are the integer IDs we stored.
    # We map these back to our actual client UUIDs.
    matched_client_ids = [index_to_client_id[i] for i in indices[0] if i != -1]
    
    print(f"AUDIENCE BUILDER: Found {len(matched_client_ids)} clients for query '{query}'.")
    return matched_client_ids