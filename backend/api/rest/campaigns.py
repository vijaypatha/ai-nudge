# ---
# File Path: backend/api/rest/campaigns.py
# Purpose: Defines API endpoints for outbound communications by calling the orchestrator.
# ---

from fastapi import APIRouter, HTTPException, status
from typing import Optional
from uuid import UUID

from data.models.message import SendMessageImmediate
from data.models.campaign import CampaignBriefing, CampaignUpdate # This is the key import
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
    This keeps the API layer clean and free of business logic.
    """
    # The API layer's only job is to validate input and call the service layer.
    success = await orchestrator.orchestrate_send_message_now(
        client_id=message_data.client_id,
        content=message_data.content
    )
    
    if success:
        return {"message": "Message sent successfully!", "client_id": message_data.client_id}
    else:
        # The orchestrator handles logging details; the API returns a generic error.
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to send message.")



@router.put("/{campaign_id}", response_model=CampaignBriefing)
async def update_campaign_briefing(campaign_id: UUID, update_data: CampaignUpdate):
    """
    (API Endpoint) Updates a specific campaign briefing. This is used to save an
    edited draft or change its status (e.g., to 'approved' or 'dismissed').
    """
    briefing_to_update = crm_service.get_campaign_briefing_by_id(campaign_id)
    
    if not briefing_to_update:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign briefing not found.")

    if update_data.edited_draft is not None:
        briefing_to_update.edited_draft = update_data.edited_draft
        print(f"CAMPAIGN API: Updated draft for campaign {campaign_id}")

    if update_data.status is not None:
        briefing_to_update.status = update_data.status
        print(f"CAMPAIGN API: Updated status to '{update_data.status}' for campaign {campaign_id}")
    
    return briefing_to_update
