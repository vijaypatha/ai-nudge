# File Path: backend/api/rest/community.py
# Purpose: API endpoint for the new "Community" feature.

from fastapi import APIRouter, Depends
from typing import List
from uuid import UUID
from sqlmodel import SQLModel

from data.models.user import User
from api.security import get_current_user_from_token
from data import crm as crm_service
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

# --- API Endpoint ---
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