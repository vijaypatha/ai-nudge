# FILE: backend/agent_core/semantic_service.py
# --- NEW FILE ---

import faiss
import numpy as np
import logging
import json
from typing import List
from uuid import UUID

from sqlmodel import Session
from data.models.client import Client
from data import crm as crm_service
from agent_core.llm_client import generate_embedding

# --- Configuration ---
DIMENSION = 1536
SIMILARITY_THRESHOLD = 0.35

# --- In-Memory Vector Index ---
# This setup is suitable for thousands of clients. For millions, a managed
# vector DB (like Pinecone, Weaviate, or Postgres w/ pg_vector) would be the next step.
faiss_index = faiss.IndexFlatIP(DIMENSION)
faiss_index = faiss.IndexIDMap(faiss_index)
index_to_client_id_map: List[UUID] = []


# --- Index Management ---

async def initialize_vector_index():
    """
    Builds the FAISS index from the composite client embeddings on application startup.
    This logic is moved from the old audience_builder.py.
    """
    global index_to_client_id_map
    faiss_index.reset()
    index_to_client_id_map = []

    logging.info("SEMANTIC SERVICE: Initializing client vector index...")
    # Note: Uses a private CRM function for a system-wide operation.
    clients = crm_service._get_all_clients_for_system_indexing()
    
    clients_with_embedding = [c for c in clients if c.notes_embedding]
    
    if not clients_with_embedding:
        logging.warning("SEMANTIC SERVICE: No clients with embeddings found. Index will be empty.")
        return

    logging.info(f"SEMANTIC SERVICE: Loading {len(clients_with_embedding)} composite client embeddings into index...")

    embeddings = np.array([c.notes_embedding for c in clients_with_embedding]).astype('float32')
    faiss.normalize_L2(embeddings)
    
    item_ids = np.arange(len(clients_with_embedding))

    faiss_index.add_with_ids(embeddings, item_ids)
    index_to_client_id_map = [c.id for c in clients_with_embedding]
    
    logging.info(f"SEMANTIC SERVICE: Index built successfully with {faiss_index.ntotal} vectors.")


# --- Embedding Generation ---

async def update_client_embedding(client: Client, session: Session):
    """
    Builds a composite document, generates a new embedding, and updates the client record.
    This logic is moved from the old crm.py.
    """
    if not client or not client.id or not client.user_id:
        logging.warning("SEMANTIC SERVICE: Attempted to build embedding for an invalid client object.")
        return

    # 1. Gather data sources
    notes = client.notes or ""
    user_tags = client.user_tags or []
    ai_tags = client.ai_tags or []
    preferences = client.preferences or {}
    
    try:
        recent_messages = crm_service.get_recent_messages(client_id=client.id, user_id=client.user_id, limit=5)
        conversation_context = "\n".join([f"- {msg.content}" for msg in recent_messages])
    except Exception as e:
        logging.error(f"SEMANTIC SERVICE: Failed to get recent messages for client {client.id}: {e}")
        conversation_context = ""

    # 2. Construct the weighted composite document
    all_tags = sorted(list(set(user_tags + ai_tags)))
    tags_block = f"Client Tags: {', '.join(all_tags)}\n" * 3 if all_tags else "Client Tags: None\n"
    prefs_block = f"Client Preferences: {json.dumps(preferences)}\n" if preferences else "Client Preferences: None\n"
    conversation_block = f"Recent Conversation Highlights:\n{conversation_context}\n" if conversation_context else "Recent Conversation Highlights: None\n"
    notes_block = f"Historical Notes:\n{notes}"

    composite_document = "\n---\n".join([tags_block, prefs_block, conversation_block, notes_block])

    # 3. Generate and update embedding
    if composite_document.strip():
        logging.info(f"SEMANTIC SERVICE: Updating composite embedding for client {client.id}")
        embedding = await generate_embedding(composite_document)
        client.notes_embedding = embedding
    else:
        logging.info(f"SEMANTIC SERVICE: No content for composite embedding for client {client.id}. Clearing.")
        client.notes_embedding = None

    session.add(client)
    # The calling function (e.g., in crm.py) will be responsible for the final commit.


# --- Semantic Search ---

async def find_similar_clients(
    query_text: str,
    user_id: UUID,
    top_k: int = 10
) -> List[UUID]:
    """
    Finds clients semantically similar to a natural language query for a specific user.
    This logic is moved from the old audience_builder.py.
    """
    if faiss_index.ntotal == 0:
        logging.warning("SEMANTIC SERVICE: Search attempted but index is empty.")
        return []

    logging.info(f"SEMANTIC SERVICE: Searching for clients matching query: '{query_text}'")
    query_embedding = await generate_embedding(query_text)

    if query_embedding is None:
        return []
    
    k = min(top_k, faiss_index.ntotal)
    
    query_vector = np.array([query_embedding]).astype('float32')
    faiss.normalize_L2(query_vector)
    
    similarities, indices = faiss_index.search(query_vector, k=k)
    
    all_matched_client_ids = {
        index_to_client_id_map[i] for i, sim in zip(indices[0], similarities[0])
        if i != -1 and sim > SIMILARITY_THRESHOLD
    }
    
    if not all_matched_client_ids:
        return []

    # Filter the global matches to only those belonging to the current user
    user_clients = crm_service.get_all_clients(user_id=user_id)
    user_client_ids = {c.id for c in user_clients}
    
    final_matched_ids = list(all_matched_client_ids.intersection(user_client_ids))

    logging.info(f"SEMANTIC SERVICE: Found {len(final_matched_ids)} relevant clients for user {user_id}.")
    return final_matched_ids