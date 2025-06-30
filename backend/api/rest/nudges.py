# ---
# File Path: backend/api/rest/nudges.py
# Purpose: Defines the API endpoint for fetching actionable nudges.
# This is the FINAL, DEFINITIVE fix for the 500 Internal Server Error.
# ---

from fastapi import APIRouter, HTTPException
from typing import List
from data import crm as crm_service
from data.models.campaign import CampaignBriefing
from data.models.user import User # Assuming a default user for now
import uuid # For hardcoded user ID

router = APIRouter(
    prefix="/nudges",
    tags=["Nudges"]
)

@router.get("/", response_model=List[CampaignBriefing])
async def get_all_actionable_nudges():
    """
    Get all actionable nudges for the current user.

    This function now returns the full CampaignBriefing objects directly.
    FastAPI and Pydantic will handle the serialization correctly,
    including converting UUIDs and other special types to JSON.
    This resolves the `500 Internal Server Error`.
    """
    try:
        # For now, we fetch nudges for our single demo user.
        # In the future, this would come from the authenticated user session.
        user_id = uuid.UUID("a8c6f1d7-8f7a-4b6e-8b0f-9e5a7d6c5b4a")
        
        # This CRM function correctly fetches all 'new' or 'insight' campaigns.
        campaigns = crm_service.get_new_campaign_briefings_for_user(user_id)
        
        return campaigns
        
    except Exception as e:
        # Log the exception for debugging
        print(f"ERROR fetching nudges: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch nudges: {str(e)}")