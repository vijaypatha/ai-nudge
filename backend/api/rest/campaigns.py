# File Path: backend/api/rest/campaigns.py
# --- FINAL FIX v2: Corrected the CRM function call to fetch nudges.

import logging
import asyncio
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Body, Query
from typing import List, Dict, Any, Optional
from uuid import UUID
import uuid
from pydantic import BaseModel
from sqlmodel import Session

from data.models.user import User
from api.security import get_current_user_from_token
from data.models.message import SendMessageImmediate, Message
from data.models.campaign import CampaignBriefing, CampaignUpdate, RecommendationSlateResponse, CampaignStatus
from agent_core.brain.verticals import VERTICAL_CONFIGS
from agent_core.agents import conversation as conversation_agent
from data import crm as crm_service
from workflow import outbound as outbound_workflow
from agent_core.brain import relationship_planner
from workflow import campaigns as campaign_workflow
from agent_core.content_resource_service import get_content_recommendations_for_user

router = APIRouter(
    prefix="/campaigns",
    tags=["Campaigns"]
)

# --- Pydantic Models for Payloads & Responses ---

class AgnosticNudgesResponse(BaseModel):
    nudges: List[CampaignBriefing]
    display_config: Dict[str, Any]

class PlanRelationshipPayload(BaseModel):
    client_id: UUID

class DraftInstantNudgePayload(BaseModel):
    topic: str

class DraftResponse(BaseModel):
    draft: str

class CoPilotActionPayload(BaseModel):
    action_type: str

# --- API Endpoints ---

@router.get("", response_model=AgnosticNudgesResponse)
async def get_all_campaigns(
    current_user: User = Depends(get_current_user_from_token)
):
    """
    Fetches all campaign briefings in DRAFT status for the current user,
    including both traditional opportunities AND content recommendations
    as part of the unified AI suggestions system.
    """
    try:
        # --- FIX: Reverted to the original, correct function call ---
        briefings = crm_service.get_new_campaign_briefings_for_user(user_id=current_user.id)
        
        # --- NEW: Include content recommendations as part of AI suggestions ---
        # Content resources are part of the Perceive layer that feeds into AI reasoning
        content_recommendations = get_content_recommendations_for_user(user_id=current_user.id)
        
        # Convert content recommendations to campaign briefings format
        content_briefings = []
        for recommendation in content_recommendations:
            # Create a campaign briefing for each content recommendation
            content_briefing = CampaignBriefing(
                id=recommendation['resource']['id'],
                campaign_type='content_recommendation',
                title=f"Content: {recommendation['resource']['title']}",
                description=recommendation['resource']['description'],
                matched_audience=recommendation['matched_clients'],
                edited_draft=recommendation['generated_message'],
                status='DRAFT',
                created_at=recommendation['resource']['created_at'],
                updated_at=recommendation['resource']['updated_at']
            )
            content_briefings.append(content_briefing)
        
        # Combine traditional briefings with content briefings
        all_briefings = briefings + content_briefings
        
        vertical_config = VERTICAL_CONFIGS.get(current_user.vertical, {})
        campaign_configs = vertical_config.get("campaign_configs", {})
        
        # Add display config for content recommendations
        display_config = {
            campaign_type: config.get("display", {})
            for campaign_type, config in campaign_configs.items()
        }
        
        # Add content recommendation display config
        display_config['content_recommendation'] = {
            'icon': 'BookOpen',
            'color': 'text-blue-400',
            'title': 'Content'
        }
        
        return AgnosticNudgesResponse(nudges=all_briefings, display_config=display_config)

    except Exception as e:
        logging.error(f"Error fetching campaigns for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred while fetching campaigns.")


@router.post("/draft-instant-nudge", response_model=DraftResponse)
async def draft_instant_nudge_endpoint(
    payload: DraftInstantNudgePayload,
    current_user: User = Depends(get_current_user_from_token)
):
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


@router.post("/{briefing_id}/action", status_code=200, response_model=dict)
async def handle_campaign_action(
    briefing_id: UUID,
    payload: CoPilotActionPayload,
    current_user: User = Depends(get_current_user_from_token)
):
    try:
        result = await campaign_workflow.handle_copilot_action(
            briefing_id=briefing_id,
            action_type=payload.action_type,
            user_id=current_user.id
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logging.error(f"API: Error handling co-pilot action for briefing {briefing_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to handle co-pilot action.")


@router.post("/{campaign_id}/approve", response_model=CampaignBriefing)
async def approve_campaign_plan(
    campaign_id: UUID,
    current_user: User = Depends(get_current_user_from_token)
):
    try:
        updated_plan = await campaign_workflow.approve_and_schedule_precomputed_plan(
            plan_id=campaign_id,
            user_id=current_user.id
        )
        return updated_plan
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(f"Failed to approve campaign {campaign_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to approve campaign plan.")


@router.post("/briefings/{briefing_id}/complete", response_model=RecommendationSlateResponse)
async def complete_briefing(
    briefing_id: uuid.UUID,
    current_user: User = Depends(get_current_user_from_token)
):
    with Session(crm_service.engine) as session:
        updated_slate = crm_service.update_slate_status(
            slate_id=briefing_id,
            new_status=CampaignStatus.COMPLETED,
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


@router.post("/messages/send-now", status_code=200, response_model=Message)
async def send_instant_nudge_now(message_data: SendMessageImmediate, current_user: User = Depends(get_current_user_from_token)):
    """ Sends an instant nudge and logs it with the correct source. """
    from agent_core import orchestrator
    from data.models.message import MessageSource

    saved_message = await orchestrator.orchestrate_send_message_now(
        client_id=message_data.client_id,
        content=message_data.content,
        user_id=current_user.id,
        source=MessageSource.INSTANT_NUDGE # Pass the correct source
    )

    if saved_message:
        return saved_message
    else:
        raise HTTPException(status_code=500, detail="Failed to send instant nudge.")


@router.put("/{campaign_id}", response_model=CampaignBriefing)
async def update_campaign_briefing(campaign_id: UUID, update_data: CampaignUpdate, current_user: User = Depends(get_current_user_from_token)):
    try:
        updated_briefing = crm_service.update_campaign_briefing(campaign_id, update_data, user_id=current_user.id)
        if not updated_briefing:
            raise HTTPException(status_code=404, detail="Campaign briefing not found.")
        return updated_briefing
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update campaign: {str(e)}")


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