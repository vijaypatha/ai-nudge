# ---
# File Path: backend/api/rest/nudges.py
# Purpose: Defines the API endpoints for fetching AI-generated Campaign Briefings.
# ---

from fastapi import APIRouter, HTTPException
from typing import List
from uuid import UUID

# Import the new CampaignBriefing model and the CRM service
from data.models.campaign import CampaignBriefing
from data import crm as crm_service

router = APIRouter(
    prefix="/nudges",
    tags=["Nudges"]
)

@router.get("/", response_model=List[CampaignBriefing])
async def get_all_new_nudges():
    """
    Retrieves all 'new' Campaign Briefings for the current user.
    """
    if not crm_service.mock_users_db:
        raise HTTPException(status_code=404, detail="No users found in the system.")
    
    current_user_id = crm_service.mock_users_db[0].id
    
    # Use the new CRM function to fetch campaign briefings.
    new_briefings = crm_service.get_new_campaign_briefings_for_user(user_id=current_user_id)
    
    print(f"API: Found {len(new_briefings)} new campaign briefings for user {current_user_id}.")
    
    return new_briefings