# File Path: backend/api/rest/campaigns.py
# --- MODIFIED: Added background task to capture dismissal feedback for AI learning ---

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

# --- NEW: Import llm_client for embedding generation in the background task ---
from agent_core import llm_client

router = APIRouter(
    prefix="/campaigns",
    tags=["Campaigns"]
)

# --- Pydantic Models for Payloads & Responses (Unchanged) ---

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

# --- NEW: Background task function for recording feedback ---
async def record_dismissal_feedback_task(campaign_id: UUID, user_id: UUID):
    """
    This background task records negative feedback when a user dismisses a nudge.
    It runs asynchronously to avoid blocking the API response.
    """
    logging.info(f"FEEDBACK_TASK: Starting dismissal feedback process for campaign {campaign_id}")
    with Session(crm_service.engine) as session:
        # 1. Fetch the campaign and its associated resource
        campaign = crm_service.get_campaign_briefing_by_id(campaign_id, user_id, session)
        if not campaign or not campaign.triggering_resource_id:
            logging.warning(f"FEEDBACK_TASK: Campaign {campaign_id} not found or has no resource. Cannot record feedback.")
            return

        resource = crm_service.get_resource_by_id(campaign.triggering_resource_id, user_id)
        if not resource:
            logging.warning(f"FEEDBACK_TASK: Resource {campaign.triggering_resource_id} not found for campaign {campaign_id}. Cannot record feedback.")
            return

        # 2. Generate the embedding for the dismissed resource
        resource_embedding = None
        text_to_embed = None
        if resource.resource_type == "property":
            text_to_embed = resource.attributes.get('PublicRemarks')
        elif resource.resource_type == "web_content":
            text_to_embed = resource.attributes.get('summary') or resource.attributes.get('description')

        if not text_to_embed:
            logging.warning(f"FEEDBACK_TASK: No embeddable text found for resource {resource.id}. Cannot record feedback.")
            return

        try:
            resource_embedding = await llm_client.generate_embedding(text_to_embed)
        except Exception as e:
            logging.error(f"FEEDBACK_TASK: Failed to generate embedding for resource {resource.id}: {e}")
            return

        if not resource_embedding:
            return

        # 3. For each client in the campaign's audience, save the negative preference
        for client_info in campaign.matched_audience:
            client_id_str = client_info.get("client_id")
            if client_id_str:
                client_id = UUID(client_id_str)
                crm_service.add_negative_preference(
                    client_id=client_id,
                    campaign_id=campaign_id,
                    resource_embedding=resource_embedding,
                    user_id=user_id,
                    session=session
                )
        
        session.commit()
        logging.info(f"FEEDBACK_TASK: Successfully recorded dismissal feedback for campaign {campaign_id}")


# --- API Endpoints ---

@router.get("", response_model=AgnosticNudgesResponse)
async def get_all_campaigns(
    current_user: User = Depends(get_current_user_from_token)
):
    """
    Fetches all campaign briefings in DRAFT status for the current user.
    (Functionality unchanged)
    """
    try:
        briefings = crm_service.get_new_campaign_briefings_for_user(user_id=current_user.id)
        content_recommendations = get_content_recommendations_for_user(user_id=current_user.id)
        content_briefings = []
        for recommendation in content_recommendations:
            content_briefing = CampaignBriefing(
                id=recommendation['resource']['id'],
                user_id=current_user.id,
                campaign_type='content_recommendation',
                headline=f"Content: {recommendation['resource']['title']}",
                original_draft=recommendation['generated_message'],
                matched_audience=recommendation['matched_clients'],
                key_intel={
                    'content_preview': {
                        'content_type': recommendation['resource']['content_type'],
                        'url': recommendation['resource']['url'],
                        'title': recommendation['resource']['title'],
                        'description': recommendation['resource']['description'],
                        'categories': recommendation['resource']['categories']
                    },
                    'strategic_context': f"Share this {recommendation['resource']['content_type']} with your client",
                    'trigger_source': 'Content Library'
                },
                status=CampaignStatus.DRAFT
            )
            content_briefings.append(content_briefing)
        
        all_briefings = briefings + content_briefings
        
        vertical_config = VERTICAL_CONFIGS.get(current_user.vertical, {})
        campaign_configs = vertical_config.get("campaign_configs", {})
        
        display_config = {
            campaign_type: config.get("display", {})
            for campaign_type, config in campaign_configs.items()
        }
        
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
    # (Functionality unchanged)
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
    # (Functionality unchanged)
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
    # (Functionality unchanged)
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
    # (Functionality unchanged)
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
    # (Functionality unchanged)
    client = crm_service.get_client_by_id(payload.client_id, user_id=current_user.id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found.")
    await relationship_planner.plan_relationship_campaign(client=client, user=current_user)
    return {"status": "success", "message": f"Relationship campaign planning started for {client.full_name}."}


@router.post("/messages/send-now", status_code=200, response_model=Message)
async def send_instant_nudge_now(message_data: SendMessageImmediate, current_user: User = Depends(get_current_user_from_token)):
    # (Functionality unchanged)
    from agent_core import orchestrator
    from data.models.message import MessageSource

    saved_message = await orchestrator.orchestrate_send_message_now(
        client_id=message_data.client_id,
        content=message_data.content,
        user_id=current_user.id,
        source=MessageSource.INSTANT_NUDGE
    )

    if saved_message:
        return saved_message
    else:
        raise HTTPException(status_code=500, detail="Failed to send instant nudge.")


# --- MODIFIED: This endpoint now triggers the feedback learning mechanism ---
@router.put("/{campaign_id}", response_model=CampaignBriefing)
async def update_campaign_briefing(
    campaign_id: UUID, 
    update_data: CampaignUpdate, 
    background_tasks: BackgroundTasks, # <-- ADDED dependency
    current_user: User = Depends(get_current_user_from_token)
):
    try:
        # The campaign is updated first, ensuring the UI gets a fast response.
        updated_briefing = crm_service.update_campaign_briefing(campaign_id, update_data, user_id=current_user.id)
        if not updated_briefing:
            raise HTTPException(status_code=404, detail="Campaign briefing not found.")

        # --- NEW: Check if the campaign was dismissed ---
        # If so, trigger the background task to record this feedback for the AI.
        if update_data.status == CampaignStatus.DISMISSED:
            logging.info(f"API: Campaign {campaign_id} was dismissed. Adding feedback task to background.")
            background_tasks.add_task(
                record_dismissal_feedback_task, 
                campaign_id=campaign_id,
                user_id=current_user.id
            )

        return updated_briefing
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update campaign: {str(e)}")


@router.get("/{campaign_id}", response_model=CampaignBriefing)
async def get_campaign_by_id(campaign_id: UUID, current_user: User = Depends(get_current_user_from_token)):
    # (Functionality unchanged)
    campaign = crm_service.get_campaign_briefing_by_id(campaign_id, user_id=current_user.id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found.")
    return campaign


@router.post("/{campaign_id}/send", status_code=202)
async def trigger_send_campaign(campaign_id: UUID, background_tasks: BackgroundTasks, current_user: User = Depends(get_current_user_from_token)):
    # (Functionality unchanged)
    campaign = crm_service.get_campaign_briefing_by_id(campaign_id, user_id=current_user.id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found.")
    background_tasks.add_task(outbound_workflow.send_campaign_to_audience, campaign_id, current_user.id)
    return {"message": "Campaign sending process started."}