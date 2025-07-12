# File Path: backend/api/rest/campaigns.py
# --- DEFINITIVE FIX: Corrects the import for 'Session' to resolve the startup error.

import logging
# --- MODIFIED: Removed 'Session' from the fastapi import ---
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Body
from typing import List, Dict, Any, Optional
from uuid import UUID
import uuid
from pydantic import BaseModel
# --- ADDED: Imported 'Session' from the correct library, sqlmodel ---
from sqlmodel import Session

from data.models.user import User
from api.security import get_current_user_from_token
from data.models.message import SendMessageImmediate
from data.models.campaign import CampaignBriefing, CampaignUpdate, RecommendationSlateResponse
from agent_core import orchestrator
from agent_core.agents import conversation as conversation_agent
from data import crm as crm_service
from workflow import outbound as outbound_workflow
from agent_core.brain import relationship_planner

router = APIRouter(
    prefix="/campaigns",
    tags=["Campaigns"]
)

# --- Pydantic Models for Payloads & Responses ---

class PlanRelationshipPayload(BaseModel):
    client_id: UUID

class DraftInstantNudgePayload(BaseModel):
    topic: str

class DraftResponse(BaseModel):
    draft: str

# --- API Endpoints ---

@router.post("/draft-instant-nudge", response_model=DraftResponse)
async def draft_instant_nudge_endpoint(
    payload: DraftInstantNudgePayload, 
    current_user: User = Depends(get_current_user_from_token)
):
    """
    Generates a message draft for the 'Instant Nudge' feature based on a topic.
    """
    if not payload.topic or not payload.topic.strip():
        raise HTTPException(status_code=400, detail="Topic cannot be empty.")
    try:
        draft_content = await conversation_agent.draft_instant_nudge_message(
            realtor=current_user,
            topic=payload.topic
        )
        return DraftResponse(draft=draft_content)
    except Exception as e:
        logging.error(f"Error drafting instant nudge for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate AI draft.")
    
@router.post("/briefings/{briefing_id}/complete", response_model=RecommendationSlateResponse)
async def complete_briefing(
    briefing_id: uuid.UUID, 
    current_user: User = Depends(get_current_user_from_token)
):
    """
    Marks a campaign briefing (or recommendation slate) as 'completed'.
    This is called when a user acts on a recommendation, like adding a tag,
    which triggers the "fall-off" UI behavior.
    """
    with Session(crm_service.engine) as session:
        updated_slate = crm_service.update_slate_status(
            slate_id=briefing_id, 
            new_status='completed', 
            user_id=current_user.id,
            session=session
        )
        if not updated_slate:
            raise HTTPException(status_code=404, detail="Briefing not found or you do not have permission to edit it.")
        
        session.commit()
        session.refresh(updated_slate)
        logging.info(f"API: Marked slate {briefing_id} as completed for user {current_user.id}")
        return updated_slate

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

@router.get("", response_model=List[CampaignBriefing])
async def get_all_campaigns(current_user: User = Depends(get_current_user_from_token)):
    try:
        return crm_service.get_new_campaign_briefings_for_user(user_id=current_user.id)
    except Exception as e:
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