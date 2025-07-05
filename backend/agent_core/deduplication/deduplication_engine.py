# File Path: backend/agent_core/deduplication/deduplication_engine.py

import logging
from typing import Optional
from uuid import UUID
from sqlmodel import Session, select
from thefuzz import fuzz

from backend.data.models.client import Client, ClientCreate

# Set up logger for observability
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants for matching thresholds
NAME_SIMILARITY_THRESHOLD = 85  # Fuzzy match score (0-100). Tune as needed.

def find_strong_duplicate(db: Session, user_id: UUID, new_contact: ClientCreate) -> Optional[Client]:
    """
    Finds a high-confidence duplicate for a new contact for a specific user.

    This function checks for duplicates using three strategies in order of confidence:
    1. Exact email match (highest confidence).
    2. Normalized phone number match.
    3. Fuzzy name match for contacts that lack both email and phone.

    Args:
        db: The database session.
        user_id: The UUID of the user owning the contacts.
        new_contact: The Pydantic model of the new contact to check.

    Returns:
        An existing Client object if a strong duplicate is found, otherwise None.
    """
    # --- Strategy 1: Exact Email Match ---
    # This is the most reliable way to identify a duplicate.
    if new_contact.email:
        statement = select(Client).where(Client.user_id == user_id, Client.email == new_contact.email)
        existing_client = db.exec(statement).first()
        if existing_client:
            logger.info(f"[Deduplication] Found strong duplicate for user {user_id} by exact email: {new_contact.email}")
            return existing_client

    # --- Strategy 2: Normalized Phone Number Match ---
    # Useful for imports where email might be missing.
    if new_contact.phone:
        # Basic normalization: remove common non-digit characters to ensure consistent matching.
        normalized_phone = "".join(filter(str.isdigit, new_contact.phone))
        
        # We only proceed if the normalized number is a reasonable length.
        if len(normalized_phone) >= 10:
            # This assumes phone numbers in the DB are stored in a consistent, perhaps normalized, format.
            # If not, this query would need to be more complex.
            statement = select(Client).where(Client.user_id == user_id, Client.phone == normalized_phone)
            existing_client = db.exec(statement).first()
            if existing_client:
                logger.info(f"[Deduplication] Found strong duplicate for user {user_id} by normalized phone: {normalized_phone}")
                return existing_client

    # --- Strategy 3: Fuzzy Name Match ---
    # This is a fallback for contacts without unique identifiers like email or phone.
    # It's less precise and should be used cautiously.
    statement = select(Client).where(Client.user_id == user_id, Client.email == None, Client.phone == None)
    clients_without_identifiers = db.exec(statement).all()
    
    for client in clients_without_identifiers:
        # Using token_sort_ratio to handle names that are slightly out of order (e.g., "Doe, John" vs "John Doe")
        name_similarity = fuzz.token_sort_ratio(new_contact.full_name, client.full_name)
        
        if name_similarity >= NAME_SIMILARITY_THRESHOLD:
            logger.info(f"[Deduplication] Found potential duplicate for user {user_id} by name similarity: '{new_contact.full_name}' vs '{client.full_name}' ({name_similarity}%)")
            return client

    # If no duplicates are found after all checks, return None.
    logger.info(f"[Deduplication] No strong duplicate found for '{new_contact.full_name}'. A new client will be created.")
    return None