# File Path: backend/api/rest/community.py
# Purpose: API endpoint for the new "Community" feature.

from fastapi import APIRouter, Depends
from typing import List, Optional
from uuid import UUID
from sqlmodel import SQLModel
from pydantic import BaseModel

from data.models.user import User
from api.security import get_current_user_from_token
from data import crm as crm_service
from agent_core import audience_builder
import logging

# --- Router Setup ---
router = APIRouter(prefix="/community", tags=["Community"])

# --- Response Model ---
class CommunityMember(SQLModel):
    """
    Defines the data structure for a client shown in the Community Gallery.
    Includes calculated "health" metrics for strategic overview.
    """
    client_id: UUID
    full_name: str
    email: str | None
    phone: str | None
    user_tags: List[str]
    ai_tags: List[str]
    last_interaction_days: int | None # Days since last interaction
    health_score: int # Score from 0-100

# --- NEW: Pydantic model for the search payload ---
class CommunitySearchQuery(BaseModel):
    natural_language_query: str

# --- API Endpoints ---
@router.get("", response_model=List[CommunityMember])
def get_community_overview_endpoint(
    current_user: User = Depends(get_current_user_from_token)
):
    """
    Retrieves all clients for the user and enriches them with "health" metrics
    for the Community Gallery view.
    """
    logging.info(f"API: Fetching community overview for user_id: {current_user.id}")
    community_members = crm_service.get_community_overview(user_id=current_user.id)
    return community_members

@router.post("/search", response_model=List[CommunityMember])
async def search_community_members_endpoint(
    query: CommunitySearchQuery,
    current_user: User = Depends(get_current_user_from_token)
):
    """
    Finds clients using a natural language query and returns them enriched
    with "health" metrics for the Community Gallery view.
    --- NEW ---
    """
    logging.info(f"API: Searching community for user '{current_user.id}' with query: '{query.natural_language_query}'")
    
    # 1. Find matching client IDs using semantic search
    matched_ids = await audience_builder.find_clients_by_semantic_query(
        query.natural_language_query, 
        user_id=current_user.id
    )
    if not matched_ids:
        return []

    # 2. Fetch the full client objects for the matched IDs
    clients = crm_service.get_clients_by_ids(
        client_ids=matched_ids, 
        user_id=current_user.id
    )

    # 3. Enrich the client data with health scores and other metrics
    enriched_members = crm_service.enrich_clients_for_community_view(clients)
    
    # Optional: Preserve the order from the semantic search if it's relevant
    id_to_member_map = {str(member['client_id']): member for member in enriched_members}
    ordered_results = [id_to_member_map[str(client_id)] for client_id in matched_ids if str(client_id) in id_to_member_map]

    logging.info(f"API: Found {len(ordered_results)} enriched community members for query.")
    return ordered_results