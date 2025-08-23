# FILE: backend/api/rest/portal.py
"""
Manages all API endpoints related to the interactive, public-facing client portal.
This includes generating secure access links, displaying curated matches, and
receiving client feedback.
"""

import logging
import asyncio
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from uuid import UUID
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

# --- Local Application Imports ---
# Database and authentication dependencies
from data.database import get_session
from backend.api.security import get_current_user_from_token

# Data models used in this module
from data.models.user import User
from data.models.client import Client
from data.models.resource import Resource, ResourceType, ResourceStatus
from data.models.portal import PortalComment, CommenterType
from data.models.event import MarketEvent

# Core services and logic
from data import crm as crm_service
from common.config import get_settings
from agent_core.brain.nudge_engine import score_event_against_client
from agent_core.brain.verticals import VERTICAL_CONFIGS
from agent_core.agents import guidance as guidance_agent

# Shared utility for creating and decoding secure portal links
from backend.common.jwt_utils import create_portal_token, decode_portal_token


# --- Router Setup ---
# Initializes the FastAPI router for all portal-related endpoints.
router = APIRouter(prefix="/portal", tags=["Client Portal"])
logger = logging.getLogger(__name__)
settings = get_settings()


# --- Pydantic Models for a Clean API Contract ---

class PortalFeedbackPayload(BaseModel):
    """Defines the data structure for a client's feedback submission from the portal."""
    resource_id: UUID
    action: str
    reason: Optional[str] = None
    comment_text: Optional[str] = None

class PortalMatch(BaseModel):
    """Defines the data structure for a single matched property sent to the portal."""
    id: UUID
    attributes: Dict[str, Any]
    score: int
    reasons: List[str]

class PortalDataResponse(BaseModel):
    """Defines the complete data structure for the client portal view."""
    client_name: str
    preferences: Dict[str, Any]
    matches: List[PortalMatch]
    comments: List[PortalComment]
    agent_name: Optional[str] = None
    curation_rationale: Optional[str] = None


# --- Agent-Facing Endpoint ---

@router.post("/{client_id}/generate-link")
async def generate_portal_link(
    client_id: UUID,
    current_user: User = Depends(get_current_user_from_token),
    session: Session = Depends(get_session)
):
    """
    Generates a secure, long-lived portal URL for a specific client.
    This endpoint is intended to be called by the agent from the main application.
    """
    # Verify that the requested client belongs to the currently authenticated agent
    client = crm_service.get_client_by_id(client_id, current_user.id, session)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    # Create a secure JWT that encodes the client's and user's IDs
    token = create_portal_token(client_id, current_user.id)
    
    # Construct the full URL that the client will use to access the portal
    portal_url = f"{settings.FRONTEND_BASE_URL}/portal/{token}"
    
    return {"portal_url": portal_url}


# --- Public, Client-Facing Endpoints ---

@router.get("/view/{short_id}", response_model=PortalDataResponse)
async def get_portal_data(short_id: str, session: Session = Depends(get_session)):
    """
    FINAL VERSION: Resolves a short link and displays the EXACT curated list of matches
    from the associated campaign briefing, ensuring a consistent experience.
    """
    from data.models.portal import PortalLink
    from data.models.campaign import CampaignBriefing
    from sqlmodel import select

    # 1. Find the link record in the database
    link_record = session.get(PortalLink, short_id)
    expires_at_aware = link_record.expires_at.replace(tzinfo=timezone.utc) if link_record and link_record.expires_at.tzinfo is None else link_record.expires_at if link_record else None
    if not link_record or not link_record.is_active or not expires_at_aware or expires_at_aware < datetime.now(timezone.utc):
        raise HTTPException(status_code=404, detail="This portal link is invalid or has expired.")

    # 2. Decode the token to get user/client IDs
    try:
        payload = decode_portal_token(link_record.token)
        client_id = UUID(payload["sub"])
        user_id = UUID(payload["user_id"])
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))

    # 3. Fetch all necessary data
    campaign = session.get(CampaignBriefing, link_record.campaign_id)
    client = session.get(Client, client_id)
    user = session.get(User, user_id)
    if not campaign or not client or not user or client.user_id != user_id:
        raise HTTPException(status_code=404, detail="Associated campaign, client, or agent not found.")

    # 4. Get the pre-computed, curated list of matches from the campaign
    curated_matches_data = campaign.key_intel.get("matched_resource_ids", [])
    
    # 5. Hydrate the resource data for the frontend
    resource_ids = [UUID(match["resource_id"]) for match in curated_matches_data]
    if not resource_ids:
        top_matches = []
    else:
        resources = session.exec(select(Resource).where(Resource.id.in_(resource_ids))).all()
        resource_map = {str(r.id): r.attributes for r in resources}

        top_matches = []
        for match_data in curated_matches_data:
            resource_attributes = resource_map.get(match_data["resource_id"])
            if resource_attributes:
                resource_attributes["agent_commentary"] = match_data.get("agent_commentary")
                top_matches.append(PortalMatch(
                    id=UUID(match_data["resource_id"]),
                    attributes=resource_attributes,
                    score=match_data.get("score", 0),
                    reasons=match_data.get("reasons", [])
                ))
    
    comments = []
    curation_rationale = campaign.key_intel.get("curation_rationale")

    return PortalDataResponse(
        client_name=client.full_name,
        preferences=client.preferences,
        matches=top_matches,
        comments=comments,
        agent_name=user.full_name,
        curation_rationale=curation_rationale
    )

@router.post("/feedback/{token}")
async def submit_portal_feedback(
    token: str, 
    payload: PortalFeedbackPayload, 
    session: Session = Depends(get_session)
):
    """
    Public endpoint for the client to submit feedback (likes, dislikes, comments)
    from the portal. This feedback is used to automatically update the client's
    profile, triggering the reactive "Instant Match" pipeline.
    """
    try:
        # Securely decode the token to identify the client
        token_payload = decode_portal_token(token)
        client_id = UUID(token_payload["sub"])
        user_id = UUID(token_payload["user_id"])
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))

    # Verify the client and user exist
    user = crm_service.get_user_by_id(user_id, session)
    client = crm_service.get_client_by_id(client_id, user_id, session)
    if not client or not user:
        raise HTTPException(status_code=404, detail="Client not found")

    note_to_add = None
    # If the client left a comment, save it and format it as a note
    if payload.comment_text:
        new_comment = PortalComment(
            user_id=user_id, client_id=client_id, resource_id=payload.resource_id,
            commenter_type=CommenterType.CLIENT, comment_text=payload.comment_text
        )
        session.add(new_comment)
        note_to_add = f"Client commented on a portal property: '{payload.comment_text}'"

    # If the client used a feedback button (love, like, dislike), format it as a note
    elif payload.action in ["love", "like", "dislike"]:
        note_to_add = f"Client feedback on a portal property: '{payload.action.upper()}'"
        if payload.reason:
            note_to_add += f" Reason: {payload.reason}"

    # If a note was created, update the client's profile with this new intel
    if note_to_add:
        # This CRM function automatically triggers a re-synthesis of the client's
        # profile, which in turn runs the "Instant Match" reactive pipeline.
        await crm_service.update_client_intel(client_id, user_id, notes_to_add=note_to_add)
    
    session.commit()
    logger.info(f"PORTAL API: Received feedback from client {client_id}.")
    return {"status": "success", "message": "Feedback received"}