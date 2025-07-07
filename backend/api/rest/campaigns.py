# File Path: backend/api/rest/campaigns.py
# DEFINITIVE FIX: Corrects the function call to match the actual function name
# in the crm service layer, resolving the 500 error. Also keeps the path fix.

import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from typing import List
from uuid import UUID
from pydantic import BaseModel

from data.models.user import User
from api.security import get_current_user_from_token
from data.models.message import SendMessageImmediate
from data.models.campaign import CampaignBriefing, CampaignUpdate
from agent_core import orchestrator
from data import crm as crm_service
from workflow import outbound as outbound_workflow
from agent_core.brain import relationship_planner

router = APIRouter(
    prefix="/campaigns",
    tags=["Campaigns"]
)

class PlanRelationshipPayload(BaseModel):
    client_id: UUID

@router.post("/plan-relationship", status_code=202)
async def plan_relationship_campaign_endpoint(payload: PlanRelationshipPayload, current_user: User = Depends(get_current_user_from_token)):
    client = crm_service.get_client_by_id(payload.client_id, user_id=current_user.id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found.")
    
    await relationship_planner.plan_relationship_campaign(client=client, realtor=current_user)
    
    return {"status": "success", "message": f"Relationship campaign planning started for {client.full_name}."}


@router.post("/messages/send-now", status_code=200)
async def send_message_now(message_data: SendMessageImmediate, current_user: User = Depends(get_current_user_from_token)):
    success = await orchestrator.orchestrate_send_message_now(
        client_id=message_data.client_id,
        content=message_data.content,
        user_id=current_user.id
    )
    
    if success:
        return {"message": "Message sent successfully!", "client_id": message_data.client_id}
    else:
        raise HTTPException(status_code=500, detail="Failed to send message.")

@router.put("/{campaign_id}", response_model=CampaignBriefing)
async def update_campaign_briefing(campaign_id: UUID, update_data: CampaignUpdate, current_user: User = Depends(get_current_user_from_token)):
    try:
        updated_briefing = crm_service.update_campaign_briefing(campaign_id, update_data, user_id=current_user.id)
        if not updated_briefing:
            raise HTTPException(status_code=404, detail="Campaign briefing not found.")
        return updated_briefing
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update campaign: {str(e)}")

# --- MODIFIED: Calling the correct function `get_new_campaign_briefings_for_user`. ---
@router.get("", response_model=List[CampaignBriefing])
async def get_all_campaigns(current_user: User = Depends(get_current_user_from_token)):
    """Get all campaigns from the database for the current user."""
    try:
        # BUGFIX: The function was incorrectly named. Changed to the existing crm service function.
        return crm_service.get_new_campaign_briefings_for_user(user_id=current_user.id)
    except Exception as e:
        # Logging the actual error helps in debugging.
        logging.error(f"Error fetching campaigns for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch campaigns: {str(e)}")

@router.get("/{campaign_id}", response_model=CampaignBriefing)
async def get_campaign_by_id(campaign_id: UUID, current_user: User = Depends(get_current_user_from_token)):
    campaign = crm_service.get_campaign_briefing_by_id(campaign_id, user_id=current_user.id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found.")
    return campaign

@router.post("/{campaign_id}/send", status_code=202)
async def trigger_send_campaign(campaign_id: UUID, background_tasks: BackgroundTasks, current_user: User = Depends(get_current_user_from_token)):
    campaign = crm_service.get_campaign_briefing_by_id(campaign_id, user_id=current_user.id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found.")
    
    background_tasks.add_task(outbound_workflow.send_campaign_to_audience, campaign_id, current_user.id)
    return {"message": "Campaign sending process started."}