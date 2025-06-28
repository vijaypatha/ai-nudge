# File Path: backend/api/rest/nudges.py
# CORRECTED VERSION: Added missing prefix

from fastapi import APIRouter, HTTPException
from typing import List
from data import crm as crm_service
from data.models.campaign import CampaignBriefing

# FIXED: Add prefix to router definition
router = APIRouter(prefix="/nudges")

@router.get("/", response_model=List[dict])
async def get_all_actionable_nudges():
    """
    Get all actionable nudges for the current user.
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
