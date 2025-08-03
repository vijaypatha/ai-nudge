# File Path: backend/api/rest/nudges.py
from fastapi import APIRouter, HTTPException, Depends
from typing import List
from data import crm as crm_service
from data.models.campaign import CampaignBriefing

# --- MODIFIED: Import User model and security dependency ---
from data.models.user import User
from api.security import get_current_user_from_token

router = APIRouter(
    prefix="/nudges",
    tags=["Nudges"]
)

# --- MODIFIED: Added security dependency and removed hardcoded user ID ---
@router.get("/", response_model=List[CampaignBriefing])
async def get_all_actionable_nudges(current_user: User = Depends(get_current_user_from_token)):
    """
    Get all actionable nudges for the current user.
    """
    try:
        # Replaced hardcoded user ID with the authenticated user's ID
        campaigns = crm_service.get_new_campaign_briefings_for_user(current_user.id)
        return campaigns
    except Exception as e:
        print(f"ERROR fetching nudges: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch nudges: {str(e)}")