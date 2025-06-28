# File Path: backend/api/rest/nudges.py
# Purpose: Defines the API endpoint for fetching ALL actionable campaign briefings (both 'new' and 'insight'). The frontend will handle the grouping logic.

from fastapi import APIRouter, HTTPException
from typing import List
from uuid import UUID

from data.models.campaign import CampaignBriefing
from data import crm as crm_service

router = APIRouter(
    prefix="/nudges",
    tags=["Nudges"]
)

@router.get("/", response_model=List[CampaignBriefing])
async def get_all_actionable_nudges():
    """
    Retrieves all actionable briefings for the current user.
    This includes high-confidence 'new' nudges and low-confidence 'insights'.
    """
    if not crm_service.mock_users_db:
        raise HTTPException(status_code=404, detail="No users found in the system.")
    
    current_user_id = crm_service.mock_users_db[0].id
    
    # Get all actionable briefings from the CRM service
    actionable_briefings = crm_service.get_new_campaign_briefings_for_user(user_id=current_user_id)
    
    print(f"API: Found {len(actionable_briefings)} total actionable briefings.")
    
    return actionable_briefings