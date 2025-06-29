# File Path: backend/api/rest/campaigns.py
# CORRECTED VERSION: Added missing prefix

from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from typing import Optional
from uuid import UUID
from data.models.message import SendMessageImmediate
from data.models.campaign import CampaignBriefing, CampaignUpdate
from agent_core import orchestrator
from data import crm as crm_service
from workflow import outbound as outbound_workflow


# FIXED: Add prefix to router definition
router = APIRouter(prefix="/campaigns")

@router.post("/messages/send-now", status_code=status.HTTP_200_OK)
async def send_message_now(message_data: SendMessageImmediate):
    """Sends a message immediately by calling the central orchestrator."""
    success = await orchestrator.orchestrate_send_message_now(
        client_id=message_data.client_id,
        content=message_data.content
    )
    
    if success:
        return {"message": "Message sent successfully!", "client_id": message_data.client_id}
    else:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to send message.")

@router.put("/{campaign_id}", response_model=CampaignBriefing)
async def update_campaign_briefing(campaign_id: UUID, update_data: CampaignUpdate):
    """Update a campaign briefing by ID."""
    print(f"CAMPAIGNS: Received update request for campaign {campaign_id}")
    print(f"CAMPAIGNS: Update data: {update_data}")
    
    try:
        updated_briefing = crm_service.update_campaign_briefing(campaign_id, update_data)
        if not updated_briefing:
            print(f"CAMPAIGNS: Campaign {campaign_id} not found")
            raise HTTPException(status_code=404, detail="Campaign briefing not found.")
        
        print(f"CAMPAIGNS: Successfully updated campaign {campaign_id}")
        return updated_briefing
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"CAMPAIGNS: Error updating campaign {campaign_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update campaign: {str(e)}")


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

@router.post("/{campaign_id}/send", status_code=status.HTTP_202_ACCEPTED)
async def trigger_send_campaign(campaign_id: UUID, background_tasks: BackgroundTasks):
    """
    Triggers the sending of a campaign to its audience in the background.
    """
    print(f"CAMPAIGN API: Received request to send campaign {campaign_id}")
    # Run the potentially long-running send operation in the background
    # so the API can respond to the UI immediately.
    background_tasks.add_task(outbound_workflow.send_campaign_to_audience, campaign_id)
    return {"message": "Campaign sending process started."}
