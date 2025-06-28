# File Path: backend/api/rest/nudges.py
# CORRECTED VERSION: Remove references to mock_users_db

from fastapi import APIRouter, HTTPException
from typing import List
from data import crm as crm_service
from data.models.campaign import CampaignBriefing

router = APIRouter()

@router.get("/", response_model=List[dict])
async def get_all_actionable_nudges():
    """
    Get all actionable nudges for the current user.
    CORRECTED: Removed check for mock_users_db since we now use persistent database.
    """
    try:
        # Get all campaigns from the database
        campaigns = crm_service.get_all_campaigns()
        
        # Convert to nudge format for the frontend
        nudges = []
        for campaign in campaigns:
            if campaign.status == "new":  # Only show actionable nudges
                nudges.append({
                    "id": str(campaign.id),
                    "type": campaign.campaign_type,
                    "headline": campaign.headline,
                    "key_intel": campaign.key_intel,
                    "matched_audience": campaign.matched_audience,
                    "status": campaign.status
                })
        
        return nudges
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch nudges: {str(e)}")
