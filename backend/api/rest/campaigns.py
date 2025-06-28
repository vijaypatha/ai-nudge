# File Path: backend/api/rest/campaigns.py
# Purpose: Defines API endpoints for outbound communications.
# CORRECTED VERSION: Fixed syntax errors and improved formatting

from fastapi import APIRouter, HTTPException, status
from typing import Optional
from uuid import UUID
from data.models.message import SendMessageImmediate
from data.models.campaign import CampaignBriefing, CampaignUpdate
from agent_core import orchestrator
from data import crm as crm_service

router = APIRouter(
    prefix="/campaigns",
    tags=["Campaigns"]
)

@router.post("/messages/send-now", status_code=status.HTTP_200_OK)
async def send_message_now(message_data: SendMessageImmediate):
    """
    Sends a message immediately by calling the central orchestrator.
    """
    success = await orchestrator.orchestrate_send_message_now(
        client_id=message_data.client_id,
        content=message_data.content
    )  # FIXED: Added missing closing parenthesis
    
    if success:
        return {"message": "Message sent successfully!", "client_id": message_data.client_id}
    else:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to send message.")

@router.put("/{campaign_id}", response_model=CampaignBriefing)
async def update_campaign_briefing(campaign_id: UUID, update_data: CampaignUpdate):
    """Update a campaign briefing by ID."""
    updated_briefing = crm_service.update_campaign_briefing(campaign_id, update_data)
    if not updated_briefing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign briefing not found.")
    return updated_briefing

@router.get("/", response_model=list[CampaignBriefing])
async def get_all_campaigns():
    """Get all campaigns from the database."""
    try:
        return crm_service.get_all_campaigns()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch campaigns: {str(e)}")

@router.get("/{campaign_id}", response_model=CampaignBriefing)
async def get_campaign_by_id(campaign_id: UUID):
    """Get a specific campaign by ID."""
    campaign = crm_service.get_campaign_briefing_by_id(campaign_id)
    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found.")
    return campaign
