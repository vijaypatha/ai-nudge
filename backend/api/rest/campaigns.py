# File Path: backend/api/rest/campaigns.py
# REFACTORED for robustness and maintainability without removing existing code.

import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Body, Query, Request
from typing import List, Dict, Any, Optional
from uuid import UUID
import uuid
from pydantic import BaseModel
from sqlmodel import Session

# Local application imports
from data.models.user import User
from api.security import get_current_user_from_token
from data.models.message import SendMessageImmediate, Message, MessageStatus, ScheduledMessage
from agent_core.brain.verticals import VERTICAL_CONFIGS
from agent_core.agents import conversation as conversation_agent
from data import crm as crm_service
from workflow import outbound as outbound_workflow
from agent_core.brain import relationship_planner
from workflow import campaigns as campaign_workflow
from data.models.campaign import CampaignBriefing, CampaignUpdate, CampaignStatus, MatchedClient
from agent_core.content_resource_service import get_content_recommendations_for_user
from data.database import get_session
import pytz 
from datetime import datetime, timedelta, date

from agent_core import llm_client

router = APIRouter(
    prefix="/campaigns",
    tags=["Campaigns"]
)

# --- Pydantic Models for Payloads & Responses ---

class AgnosticNudgesResponse(BaseModel):
    nudges: List[Any]
    display_config: Dict[str, Any]

class PlanRelationshipPayload(BaseModel):
    client_id: UUID

class DraftInstantNudgePayload(BaseModel):
    topic: str

class DraftResponse(BaseModel):
    draft: str

class CoPilotActionPayload(BaseModel):
    action_type: str

class ClientNudgeSummary(BaseModel):
    client_id: UUID
    client_name: str
    total_nudges: int
    nudge_type_counts: Dict[str, int]

class ClientNudgeSummaryResponse(BaseModel):
    client_summaries: List[ClientNudgeSummary]
    display_config: Dict[str, Any]

class UpdateAudiencePayload(BaseModel):
    client_ids: List[UUID]

# --- NEW: Reusable Dependency for fetching and validating campaigns ---
def get_campaign_briefing_for_user_from_path(
    campaign_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user_from_token)
) -> CampaignBriefing:
    """
    A reusable dependency that fetches a campaign by its ID from the path,
    and ensures it exists and belongs to the current user.
    Raises a 404 HTTPException if not found.
    """
    campaign = crm_service.get_campaign_briefing_by_id(campaign_id, user_id=current_user.id, session=session)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found.")
    return campaign

# --- Background Task (Unchanged) ---
async def record_dismissal_feedback_task(campaign_id: UUID, user_id: UUID):
    """
    This background task records negative feedback when a user dismisses a nudge.
    """
    logging.info(f"FEEDBACK_TASK: Starting dismissal feedback process for campaign {campaign_id}")
    with Session(crm_service.engine) as session:
        campaign = crm_service.get_campaign_briefing_by_id(campaign_id, user_id, session)
        if not campaign or not campaign.triggering_resource_id:
            logging.warning(f"FEEDBACK_TASK: Campaign {campaign_id} not found or has no resource.")
            return

        resource = crm_service.get_resource_by_id(campaign.triggering_resource_id, user_id, session)
        if not resource:
            logging.warning(f"FEEDBACK_TASK: Resource {campaign.triggering_resource_id} not found.")
            return

        text_to_embed = None
        if resource.resource_type == "property":
            text_to_embed = resource.attributes.get('PublicRemarks')
        elif resource.resource_type == "web_content":
            text_to_embed = resource.attributes.get('summary') or resource.attributes.get('description')

        if not text_to_embed:
            logging.warning(f"FEEDBACK_TASK: No embeddable text found for resource {resource.id}.")
            return

        resource_embedding = await llm_client.generate_embedding(text_to_embed)
        if not resource_embedding:
            return

        for client_info in campaign.matched_audience:
            if client_id_str := client_info.get("client_id"):
                client_id = UUID(client_id_str)
                crm_service.add_negative_preference(
                    client_id=client_id, campaign_id=campaign_id,
                    resource_embedding=resource_embedding, user_id=user_id, session=session
                )
        
        session.commit()
        logging.info(f"FEEDBACK_TASK: Successfully recorded dismissal feedback for campaign {campaign_id}")

# --- API Endpoints ---

@router.get("/client-summaries", response_model=ClientNudgeSummaryResponse)
def get_client_nudge_summary_list(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user_from_token),
):
    """Retrieves a list of all clients who have active nudges."""
    try:
        client_summaries = crm_service.get_client_nudge_summaries(user_id=current_user.id, session=session)
        vertical_config = VERTICAL_CONFIGS.get(current_user.vertical, {})
        campaign_configs = vertical_config.get("campaign_configs", {})
        
        display_config = {
            campaign_type: config.get("display", {})
            for campaign_type, config in campaign_configs.items()
        }
        
        display_config['content_recommendation'] = {
            'icon': 'BookOpen', 'color': 'text-blue-400', 'title': 'Content'
        }

        return ClientNudgeSummaryResponse(
            client_summaries=client_summaries,
            display_config=display_config
        )
    except Exception as e:
        logging.error(f"Error fetching client nudge summaries for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")

@router.get("", response_model=AgnosticNudgesResponse)
async def get_all_campaigns(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user_from_token)
):
    """Fetches all campaign briefings in DRAFT status for the current user."""

    # Make nested structures JSON-safe (UUIDs -> str, datetimes -> ISO8601)
    def json_sanitize(data: Any) -> Any:
        if isinstance(data, dict):
            return {k: json_sanitize(v) for k, v in data.items()}
        if isinstance(data, list):
            return [json_sanitize(i) for i in data]
        if isinstance(data, uuid.UUID):
            return str(data)
        if isinstance(data, (datetime, date)):
            return data.isoformat()
        return data

    try:
        briefings_from_db = crm_service.get_new_campaign_briefings_for_user(user_id=current_user.id, session=session)
        content_recommendations = get_content_recommendations_for_user(user_id=current_user.id)
        
        newly_created_content_briefings = []
        if content_recommendations:
            for rec in content_recommendations:
                # Sanitize the data before creating or updating the SQLModel object.
                sanitized_resource = json_sanitize(rec['resource'])
                sanitized_clients = json_sanitize(rec['matched_clients'])

                briefing_id = uuid.UUID(str(rec['resource']['id']))

                # Deduplication: if a briefing with this ID already exists, update it instead of inserting
                existing = session.get(CampaignBriefing, briefing_id)
                if existing:
                    existing.user_id = current_user.id
                    existing.campaign_type = 'content_recommendation'
                    existing.headline = f"Content: {rec['resource']['title']}"
                    existing.original_draft = rec['generated_message']
                    existing.matched_audience = sanitized_clients
                    existing.key_intel = {
                        'content_preview': sanitized_resource,
                        'strategic_context': f"Share this {rec['resource']['content_type']} with your client",
                        'trigger_source': 'Content Library'
                    }
                    if existing.status != CampaignStatus.DRAFT:
                        existing.status = CampaignStatus.DRAFT
                    session.add(existing)
                    newly_created_content_briefings.append(existing)
                    continue

                new_briefing = CampaignBriefing(
                    id=briefing_id,
                    user_id=current_user.id,
                    campaign_type='content_recommendation',
                    headline=f"Content: {rec['resource']['title']}",
                    original_draft=rec['generated_message'],
                    matched_audience=sanitized_clients,
                    key_intel={
                        'content_preview': sanitized_resource,
                        'strategic_context': f"Share this {rec['resource']['content_type']} with your client",
                        'trigger_source': 'Content Library'
                    },
                    status=CampaignStatus.DRAFT,
                )
                crm_service.save_campaign_briefing(new_briefing, session=session)
                newly_created_content_briefings.append(new_briefing)

            session.commit()
        
        all_briefings = briefings_from_db + newly_created_content_briefings
        
        vertical_config = VERTICAL_CONFIGS.get(current_user.vertical, {})
        campaign_configs = vertical_config.get("campaign_configs", {})
        
        display_config = {
            campaign_type: config.get("display", {}) for campaign_type, config in campaign_configs.items()
        }
        display_config['content_recommendation'] = {'icon': 'BookOpen', 'color': 'text-blue-400', 'title': 'Content'}
        
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
        draft_content = await conversation_agent.draft_instant_nudge_message(realtor=current_user, topic=payload.topic)
        return DraftResponse(draft=draft_content)
    except Exception as e:
        logging.error(f"Error drafting instant nudge for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate AI draft.")

@router.post("/{campaign_id}/action", status_code=200, response_model=dict)
async def handle_campaign_action(
    payload: CoPilotActionPayload,
    campaign: CampaignBriefing = Depends(get_campaign_briefing_for_user_from_path), # Using the dependency
    current_user: User = Depends(get_current_user_from_token)
):
    try:
        result = await campaign_workflow.handle_copilot_action(
            briefing_id=campaign.id, action_type=payload.action_type, user_id=current_user.id
        )
        if result is None:
            raise HTTPException(status_code=404, detail="Campaign action not found or not available.")
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logging.error(f"API: Error handling co-pilot action for briefing {campaign.id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to handle co-pilot action.")

@router.post("/{campaign_id}/approve", response_model=CampaignBriefing)
async def approve_campaign_plan(
    campaign: CampaignBriefing = Depends(get_campaign_briefing_for_user_from_path), # Using the dependency
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user_from_token)
):
    if not campaign.is_plan or campaign.status != CampaignStatus.DRAFT:
        raise HTTPException(status_code=404, detail="Draft plan not found or is not a valid plan.")

    plan_steps = campaign.key_intel.get("steps", [])
    if not plan_steps:
        raise HTTPException(status_code=400, detail="Plan contains no steps to schedule.")

    user_timezone_str = current_user.timezone or "America/New_York"
    user_tz = pytz.timezone(user_timezone_str)
    now_in_user_tz = datetime.now(user_tz)

    for step in plan_steps:
        if not (content := step.get("generated_draft")):
            continue
        
        delay_days = step.get("delay_days", 0)
        target_date = now_in_user_tz + timedelta(days=delay_days)
        local_scheduled_time = target_date.replace(hour=10, minute=30, second=0, microsecond=0)
        
        message = ScheduledMessage(
            client_id=campaign.client_id, user_id=current_user.id, parent_plan_id=campaign.id,
            content=content, scheduled_at_utc=local_scheduled_time.astimezone(pytz.utc),
            timezone=user_timezone_str, status=MessageStatus.PENDING,
            playbook_touchpoint_id=step.get("touchpoint_id")
        )
        session.add(message)

    campaign.status = CampaignStatus.ACTIVE
    session.add(campaign)
    session.commit()
    session.refresh(campaign)

    logging.info(f"API: Approved and scheduled {len(plan_steps)} messages for plan {campaign.id}")
    return campaign

@router.post("/briefings/{briefing_id}/complete", response_model=CampaignBriefing)
async def complete_briefing(
    briefing_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user_from_token)
):
    updated_slate = crm_service.update_slate_status(
        slate_id=briefing_id, new_status=CampaignStatus.COMPLETED,
        user_id=current_user.id, session=session
    )
    if not updated_slate:
        raise HTTPException(status_code=404, detail="Briefing not found or you do not have permission to edit it.")

    session.commit()
    session.refresh(updated_slate)
    logging.info(f"API: Marked slate {briefing_id} as completed for user {current_user.id}")
    return updated_slate

@router.post("/plan-relationship", status_code=202)
async def plan_relationship_campaign_endpoint(
    payload: PlanRelationshipPayload,
    current_user: User = Depends(get_current_user_from_token),
    session: Session = Depends(get_session)
):
    client = crm_service.get_client_by_id(payload.client_id, user_id=current_user.id, session=session)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found.")
    await relationship_planner.plan_relationship_campaign(client=client, user=current_user)
    return {"status": "success", "message": f"Relationship campaign planning started for {client.full_name}."}

@router.post("/messages/send-now", status_code=200, response_model=Message)
async def send_instant_nudge_now(
    message_data: SendMessageImmediate,
    current_user: User = Depends(get_current_user_from_token)
):
    from agent_core import orchestrator
    from data.models.message import MessageSource

    saved_message = await orchestrator.orchestrate_send_message_now(
        client_id=message_data.client_id, content=message_data.content,
        user_id=current_user.id, source=MessageSource.INSTANT_NUDGE
    )
    if not saved_message:
        raise HTTPException(status_code=500, detail="Failed to send instant nudge.")
    return saved_message

@router.put("/{campaign_id}", response_model=CampaignBriefing)
async def update_campaign_briefing(
    update_data: CampaignUpdate,
    background_tasks: BackgroundTasks,
    campaign: CampaignBriefing = Depends(get_campaign_briefing_for_user_from_path), # Using the dependency
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user_from_token)
):
    update_data_dict = update_data.model_dump(exclude_unset=True)
    for key, value in update_data_dict.items():
        setattr(campaign, key, value)
    
    session.add(campaign)
    session.commit()
    session.refresh(campaign)

    if campaign.status == CampaignStatus.DISMISSED:
        background_tasks.add_task(
            record_dismissal_feedback_task, campaign_id=campaign.id, user_id=current_user.id
        )

    return campaign

@router.put("/{campaign_id}/audience", response_model=CampaignBriefing)
def update_campaign_audience(
    payload: UpdateAudiencePayload,
    campaign: CampaignBriefing = Depends(get_campaign_briefing_for_user_from_path), # Using the dependency
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user_from_token),
):
    clients = crm_service.get_clients_by_ids(payload.client_ids, user_id=current_user.id)
    if len(clients) != len(payload.client_ids):
        raise HTTPException(status_code=404, detail="One or more clients not found.")
    
    new_audience = [
        MatchedClient(
            client_id=c.id,
            client_name=c.full_name,
            # FIX: Add the missing 'match_score' field, which is required by the Pydantic model.
            match_score=0,
            match_reasons=["Manually Added"]
        )
        for c in clients
    ]
    
    campaign.matched_audience = [mc.model_dump(mode='json') for mc in new_audience]
    session.add(campaign)
    session.commit()
    session.refresh(campaign)
    return campaign

@router.get("/{campaign_id}", response_model=CampaignBriefing)
def get_campaign_by_id(
    campaign: CampaignBriefing = Depends(get_campaign_briefing_for_user_from_path) # Using the dependency
):
    return campaign

@router.post("/{campaign_id}/send", status_code=202)
def trigger_send_campaign(
    background_tasks: BackgroundTasks,
    campaign: CampaignBriefing = Depends(get_campaign_briefing_for_user_from_path), # Using the dependency
    current_user: User = Depends(get_current_user_from_token)
):
    logging.info(
        f"API: Triggering send for campaign {campaign.id} (user {current_user.id})."
    )
    background_tasks.add_task(
        outbound_workflow.send_campaign_to_audience, campaign.id, current_user.id
    )
    return {"message": "Campaign sending process started."}