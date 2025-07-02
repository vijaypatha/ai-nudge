# File Path: backend/api/rest/campaigns.py
# --- ARCHITECTURE FIX ---
# - Moved the relationship campaign planning logic here from clients.py.
# - The new endpoint is `POST /campaigns/plan-relationship`.

from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from typing import Optional
from uuid import UUID
from pydantic import BaseModel
from data.models.message import SendMessageImmediate
from data.models.campaign import CampaignBriefing, CampaignUpdate
from agent_core import orchestrator
from data import crm as crm_service
from workflow import outbound as outbound_workflow
from agent_core.brain import relationship_planner # Import the planner

router = APIRouter(
    prefix="/campaigns",
    tags=["Campaigns"]
)

# --- NEW: Pydantic model for the request body ---
class PlanRelationshipPayload(BaseModel):
    client_id: UUID

# --- NEW: Endpoint for planning a relationship campaign ---
@router.post("/plan-relationship", status_code=status.HTTP_202_ACCEPTED)
async def plan_relationship_campaign_endpoint(payload: PlanRelationshipPayload):
    """
    Triggers the AI to generate a long-term relationship campaign for a specific client.
    This is the architecturally correct location for this endpoint.
    """
    client = crm_service.get_client_by_id(payload.client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found.")
    
    # Use the hardcoded demo user as the realtor
    realtor_id = UUID("a8c6f1d7-8f7a-4b6e-8b0f-9e5a7d6c5b4a")
    realtor = crm_service.get_user_by_id(realtor_id)
    if not realtor:
        raise HTTPException(status_code=500, detail="Default realtor user not found.")

    await relationship_planner.plan_relationship_campaign(client=client, realtor=realtor)
    
    return {"status": "success", "message": f"Relationship campaign planning started for {client.full_name}."}


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
    try:
        updated_briefing = crm_service.update_campaign_briefing(campaign_id, update_data)
        if not updated_briefing:
            raise HTTPException(status_code=404, detail="Campaign briefing not found.")
        return updated_briefing
    except Exception as e:
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
    background_tasks.add_task(outbound_workflow.send_campaign_to_audience, campaign_id)
    return {"message": "Campaign sending process started."}