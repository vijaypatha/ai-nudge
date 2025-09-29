# FILE: backend/api/rest/portal.py

"""

Manages all API endpoints related to the interactive, public-facing client portal.

This includes generating secure access links, displaying curated matches, and

receiving client feedback.

"""

import logging
import asyncio
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
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
from data.models.portal import PortalLink
from data.models.resource import ContentResource
from data.models.event import MarketEvent
from data.models.campaign import CampaignBriefing, CampaignStatus

# Core services and logic
from data import crm as crm_service
from common.config import get_settings
from agent_core.brain.nudge_engine import score_event_against_client
from agent_core.brain.verticals import VERTICAL_CONFIGS
from agent_core.agents import guidance as guidance_agent

# Shared utility for creating and decoding secure portal links
from common.jwt_utils import create_portal_token, decode_portal_token

# Content intelligence integration
from agent_core.content_resource_service import get_content_recommendations_for_user

# Survey intelligence integration
from agent_core.survey_config import get_survey_config, determine_survey_type
from data.models.survey import SurveyTemplate, SurveyQuestion

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
    status: str
    mls_status: Optional[str] = None # NEW: To pass the user-facing MLS status (e.g., Pending, Sold)
    reasons: List[str]

class PortalContentResource(BaseModel):
    """Pydantic-compatible model for ContentResource to include in the response."""
    id: UUID
    title: str
    url: str
    description: Optional[str]
    content_type: str

    class Config:
        orm_mode = True

class ConversationContext(BaseModel):
    """Conversation context generated from client intelligence."""
    opening_message: str
    relationship_context: Optional[str] = None
    personalization_tags: List[str] = []

class RecommendedContent(BaseModel):
    """Content recommendation with reasoning.""" 
    id: UUID
    title: str
    url: str
    description: Optional[str]
    content_type: str
    match_score: float
    reasoning: Optional[str] = None

class PortalDataResponse(BaseModel):
    """Defines the complete data structure for the client portal view."""
    client_name: str
    preferences: Dict[str, Any]
    matches: List[Dict[str, Any]] # Changed to support grouping
    comments: List[Any] # Kept generic for now
    agent_name: Optional[str] = None
    curation_rationale: Optional[str] = None
    survey_completed: bool = False
    survey_template: Optional[Any] = None # For rendering the survey if not complete
    welcome_message: Optional[str] = None
    welcome_pack: List[PortalContentResource] = []
    # NEW: Conversation intelligence
    conversation_context: Optional[ConversationContext] = None
    recommended_content: List[RecommendedContent] = []

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

    # --- MODIFICATION: Find existing link or create a new one ---
    link = crm_service.get_portal_link_for_client(client_id, session)
    if link:
        portal_url = f"{settings.FRONTEND_BASE_URL}/portal/{link.id}"
        return {"portal_url": portal_url}

    # If no link exists, create it (part of the Hub setup)
    from agent_core.brain.nudge_engine import setup_client_portal
    portal_url = await setup_client_portal(client, current_user, session)
    return {"portal_url": portal_url}

def generate_conversation_context(client: Client, user: User) -> ConversationContext:
    """Generate personalized conversation context using client tags and user style."""
    all_tags = (client.ai_tags or []) + (client.user_tags or [])
    
    # Detect relationship indicators from tags
    relationship_indicators = [tag for tag in all_tags 
                             if any(keyword in tag.lower() 
                                  for keyword in ['year', 'established', 'returning', 'previous'])]
    
    # Generate opening message based on relationship context and user style
    if relationship_indicators:
        relationship_context = "established client"
        if user.vertical == "real_estate":
            opening_message = f"Hi {client.full_name}! Great to have you back on our platform. I've been tracking the market in your area and found some exciting opportunities that match your preferences..."
        elif user.vertical == "therapy":
            opening_message = f"Welcome back, {client.full_name}. I hope you're continuing to feel supported in your wellness journey. I have some new resources that might help with your goals..."
        else:
            opening_message = f"Hi {client.full_name}! Wonderful to have you back. I've been thinking about your needs and have some personalized recommendations..."
    else:
        relationship_context = "new client"
        if user.vertical == "real_estate":
            opening_message = f"Hi {client.full_name}! Welcome to your personalized property portal. I'm {user.full_name}, and I'm excited to help you find your perfect home..."
        elif user.vertical == "therapy":
            opening_message = f"Hello {client.full_name}. I'm {user.full_name}, and I'm honored to support you on your wellness journey. I've created this space where we can work together..."
        else:
            opening_message = f"Welcome {client.full_name}! I'm {user.full_name}, and I'm excited to work with you. I've prepared some personalized resources..."
    
    # Apply user's ai_style_guide if available
    if user.ai_style_guide:
        if "warm" in user.ai_style_guide.lower():
            opening_message = opening_message.replace("Hi", "Hello").replace("Great", "Wonderful")
        elif "professional" in user.ai_style_guide.lower():
            opening_message = opening_message.replace("excited", "pleased").replace("perfect", "ideal")
    
    return ConversationContext(
        opening_message=opening_message,
        relationship_context=relationship_context,
        personalization_tags=all_tags[:5]  # Top 5 tags for context
    )

async def get_intelligent_content_recommendations(client: Client, user: User) -> List[RecommendedContent]:
    """Get content recommendations using existing content service.""" 
    try:
        raw_recommendations = get_content_recommendations_for_user(user.id, use_fuzzy=True, fuzzy_threshold=0.7)
        
        recommendations = []
        for rec in raw_recommendations[:5]:  # Top 5 recommendations
            # Fix data structure mismatch - content service returns nested 'resource' object
            resource_data = rec.get("resource", {})
            if not resource_data:
                continue
                
            recommendations.append(RecommendedContent(
                id=UUID(str(resource_data["id"])),
                title=resource_data.get("title", "Untitled"),
                url=resource_data.get("url", ""),
                description=resource_data.get("description"),
                content_type=resource_data.get("content_type", "article"),
                match_score=rec.get("match_score", 0.0),
                reasoning=rec.get("generated_message", "Matched based on your profile and preferences")
            ))
        return recommendations
    except Exception as e:
        logger.error(f"Error getting content recommendations for client {client.id}: {e}")
        return []

def find_best_survey_match(client_tags: List[str], custom_surveys: List[SurveyTemplate]) -> Optional[SurveyTemplate]:
    """
    Use client tags to intelligently match the best custom survey template.
    """
    if not custom_surveys or not client_tags:
        return None
    
    # Score each survey based on tag matches
    survey_scores = []
    
    for survey in custom_surveys:
        score = 0
        survey_name_lower = survey.name.lower()
        survey_desc_lower = (survey.description or "").lower()
        
        for tag in client_tags:
            tag_lower = tag.lower()
            # Higher score for exact matches in survey name
            if tag_lower in survey_name_lower:
                score += 5
            # Medium score for matches in description
            if tag_lower in survey_desc_lower:
                score += 2
            # Special scoring for common therapy patterns
            if tag_lower == "depression" and "depression" in survey_name_lower:
                score += 10
            if tag_lower == "anxiety" and ("anxiety" in survey_name_lower or "stress" in survey_name_lower):
                score += 8
            if tag_lower == "trauma" and "trauma" in survey_name_lower:
                score += 10
            # Generic patterns
            if "new" in tag_lower and ("intake" in survey_name_lower or "initial" in survey_name_lower):
                score += 6
            if "follow" in tag_lower and ("progress" in survey_name_lower or "follow" in survey_name_lower):
                score += 6
        
        survey_scores.append((survey, score))
    
    # Return survey with highest score, or first survey if no matches
    survey_scores.sort(key=lambda x: x[1], reverse=True)
    best_survey = survey_scores[0][0] if survey_scores[0][1] > 0 else custom_surveys[0]
    
    logger.info(f"PORTAL API: Selected survey '{best_survey.name}' with score {survey_scores[0][1]} for client tags: {client_tags}")
    return best_survey

async def get_survey_template_for_client(client: Client, user: User, session: Session) -> Optional[Dict[str, Any]]:
    """
    Get the appropriate survey template using intelligent tag-based matching.
    Priority: Custom surveys → Default surveys
    """
    # Get client tags for intelligent matching
    all_tags = (client.ai_tags or []) + (client.user_tags or [])
    
    # PRIORITY 1: Check for custom user survey templates
    custom_surveys = session.exec(
        select(SurveyTemplate).where(SurveyTemplate.user_id == user.id)
    ).all()
    
    if custom_surveys:
        # Use intelligent tag matching to select best survey
        selected_survey = find_best_survey_match(all_tags, custom_surveys)
        if selected_survey:
            # Get questions for this survey
            questions = session.exec(
                select(SurveyQuestion).where(SurveyQuestion.template_id == selected_survey.id)
            ).all()
            
            return {
                "template_id": str(selected_survey.id),
                "title": selected_survey.name,
                "description": selected_survey.description,
                "questions": [
                    {
                        "id": str(q.id),
                        "question": q.question_text,
                        "type": q.question_type,
                        "required": q.is_required or False,
                        "options": q.options or [],
                        "preference_key": q.preference_key
                    } for q in questions
                ]
            }
    
    # PRIORITY 2: Fall back to default surveys
    survey_type = determine_survey_type(user.vertical, all_tags)
    if survey_type:
        survey_config = get_survey_config(survey_type, user, session)
        if survey_config:
            return {
                "template_id": survey_type,  # Use survey type as ID for default surveys
                "title": survey_config.title,
                "description": survey_config.description,
                "questions": [
                    {
                        "id": q.id,
                        "question": q.question,
                        "type": q.type.value,
                        "required": q.required,
                        "options": q.options,
                        "preference_key": q.preference_key
                    } for q in survey_config.questions
                ]
            }
    
    return None

# --- Public, Client-Facing Endpoints ---

@router.get("/view/{short_id}", response_model=PortalDataResponse)
async def get_portal_data(short_id: str, session: Session = Depends(get_session)):
    """
    MODIFIED: Resolves the permanent short link, fetches all curated content,
    and includes survey status to power the two-stage Living Hub.
    """
    from data.models.portal import PortalLink
    from sqlmodel import select

    # 1. Find the link record in the database
    link_record = session.get(PortalLink, short_id)
    if not link_record or not link_record.is_active:
        raise HTTPException(status_code=404, detail="This portal link is invalid or has expired.")

    expires_at_aware = link_record.expires_at.replace(tzinfo=timezone.utc) if link_record.expires_at.tzinfo is None else link_record.expires_at
    if expires_at_aware < datetime.now(timezone.utc):
        raise HTTPException(status_code=403, detail="This portal link has expired.")

    # 2. Decode the token to get user/client IDs
    try:
        payload = decode_portal_token(link_record.token)
        client_id = UUID(payload["sub"])
        user_id = UUID(payload["user_id"])
    except (ValueError, Exception) as e:
        logger.error(f"Portal token decoding failed for short_id {short_id}: {e}")
        raise HTTPException(status_code=403, detail="Invalid token.")

    # 3. Fetch all necessary data
    client = session.get(Client, client_id)
    user = session.get(User, user_id)
    if not client or not user or client.user_id != user_id:
        raise HTTPException(status_code=404, detail="Associated client or agent not found.")

    # --- START: WELCOME PACK LOGIC ---
    welcome_pack_resources = []

    # Use the 'client_role' field from the now-provided client.py model
    client_role = getattr(client, 'client_role', None)

    if client_role and user.welcome_packs_config and client_role in user.welcome_packs_config:
        ordered_resource_ids_str = user.welcome_packs_config[client_role]
        
        if ordered_resource_ids_str:
            try:
                # Convert string IDs to UUIDs for the query
                ordered_resource_ids = [UUID(rid) for rid in ordered_resource_ids_str]
                
                # Fetch all resources in a single query
                resources_stmt = select(ContentResource).where(ContentResource.id.in_(ordered_resource_ids))
                fetched_resources = session.exec(resources_stmt).all()
                
                # Create a map for quick lookup
                resources_map = {res.id: res for res in fetched_resources}
                
                # Re-order the fetched resources to match the configured order
                # FIX: Transform ContentResource to PortalContentResource
                for res_id in ordered_resource_ids:
                    if res_id in resources_map:
                        resource = resources_map[res_id]
                        # Transform to PortalContentResource format
                        portal_resource = PortalContentResource(
                            id=resource.id,
                            title=resource.title,
                            url=resource.url,
                            description=resource.description,
                            content_type=resource.content_type
                        )
                        welcome_pack_resources.append(portal_resource)
                        
            except (ValueError, TypeError) as e:
                logger.error(f"Error processing welcome pack for user {user.id}, client {client.id}: {e}")

    # --- END: WELCOME PACK LOGIC ---

    # 4. Find all active curation campaigns for this client.
    statement = select(CampaignBriefing).where(
        CampaignBriefing.client_id == client_id,
        CampaignBriefing.campaign_type == "consolidated_initial_matches",
        CampaignBriefing.status == CampaignStatus.DRAFT
    ).order_by(CampaignBriefing.created_at.desc())

    active_campaigns = session.exec(statement).all()

    # 5. Process each campaign to build a grouped list of matches.
    grouped_matches = []
    all_resource_ids = set()

    for camp in active_campaigns:
        curated_matches_data = camp.key_intel.get("matched_resource_ids", [])
        if not curated_matches_data: continue

        resource_ids = [UUID(match["resource_id"]) for match in curated_matches_data]
        all_resource_ids.update(resource_ids)

        grouped_matches.append({
            "curation_date": camp.created_at.isoformat(),
            "matches": curated_matches_data
        })

    # 6. Hydrate all unique resources in a single query
    resource_map = {}
    comments_map = {}

    if all_resource_ids:
        resources = session.exec(select(Resource).where(Resource.id.in_(list(all_resource_ids)))).all()
        resource_map = {str(r.id): r for r in resources}

        comments_query = session.exec(select(PortalComment).where(PortalComment.resource_id.in_(list(all_resource_ids)))).all()
        for comment in comments_query:
            res_id_str = str(comment.resource_id)
            if res_id_str not in comments_map: comments_map[res_id_str] = []
            comments_map[res_id_str].append(comment.model_dump(mode='json'))

        for group in grouped_matches:
            for match in group["matches"]:
                resource = resource_map.get(match["resource_id"])
                if resource:
                    match["resource"] = resource.model_dump()
                    match["resource"]["comments"] = comments_map.get(match["resource_id"], [])

    curation_rationale = active_campaigns[0].key_intel.get("curation_rationale") if active_campaigns else "Welcome to your portal!"

    # --- SURVEY STATUS AND TEMPLATE LOGIC ---
    survey_completed = getattr(client, 'intake_survey_completed', False)
    survey_template = None

    # Get intelligent survey template for client
    if not survey_completed:
        survey_template = await get_survey_template_for_client(client, user, session)
        logger.info(f"PORTAL API: {'Found' if survey_template else 'No'} survey template for client {client.id}")

    # Generate conversation context using client intelligence  
    conversation_context = generate_conversation_context(client, user)
    
    # Get intelligent content recommendations
    recommended_content = await get_intelligent_content_recommendations(client, user)

    logger.info(f"PORTAL API: Generated {len(recommended_content)} content recommendations for client {client.id}")
    logger.info(f"PORTAL API: Conversation context - {conversation_context.relationship_context} with {len(conversation_context.personalization_tags)} tags")

    return PortalDataResponse(
        client_name=client.full_name,
        preferences=client.preferences or {},
        matches=grouped_matches,
        comments=[], # Comments are now nested in each match
        agent_name=user.full_name,
        curation_rationale=curation_rationale,
        survey_completed=survey_completed,
        survey_template=survey_template,
        welcome_message=user.welcome_pack_message,
        welcome_pack=welcome_pack_resources,
        conversation_context=conversation_context,
        recommended_content=recommended_content
    )


@router.post("/feedback/{short_id}")
async def submit_portal_feedback(
    short_id: str,
    payload: PortalFeedbackPayload,
    session: Session = Depends(get_session)
):
    """
    Public endpoint for the client to submit feedback (likes, dislikes, comments)
    from the portal. Works with the permanent short_id.
    """
    # 1. Find the link record to get the full token
    link_record = session.get(PortalLink, short_id)
    if not link_record or not link_record.is_active:
        raise HTTPException(status_code=403, detail="This feedback link is invalid or has expired.")

    expires_at_aware = link_record.expires_at.replace(tzinfo=timezone.utc) if link_record.expires_at.tzinfo is None else link_record.expires_at
    if expires_at_aware < datetime.now(timezone.utc):
        raise HTTPException(status_code=403, detail="This feedback link has expired.")

    try:
        token_payload = decode_portal_token(link_record.token)
        client_id = UUID(token_payload["sub"])
        user_id = UUID(token_payload["user_id"])
    except (ValueError, Exception) as e:
        logger.error(f"Portal feedback token decoding failed for short_id {short_id}: {e}")
        raise HTTPException(status_code=403, detail="Invalid token.")

    # Verify the client and user exist
    user = crm_service.get_user_by_id(user_id, session)
    client = crm_service.get_client_by_id(client_id, user_id, session)
    if not client or not user:
        raise HTTPException(status_code=404, detail="Client not found")

    resource = session.get(Resource, payload.resource_id)
    address = resource.attributes.get("UnparsedAddress", "a property") if resource else "an unknown property"

    note_to_add = None

    # If the client left a comment, save it and format it as a note
    if payload.comment_text:
        new_comment = PortalComment(
            user_id=user_id, 
            client_id=client_id, 
            resource_id=payload.resource_id, 
            commenter_type=CommenterType.CLIENT, 
            comment_text=payload.comment_text
        )
        session.add(new_comment)
        note_to_add = f"Client commented on '{address}': '{payload.comment_text}'"

    # If the client used a feedback button (love, like, dislike), format it as a note
    elif payload.action in ["love", "like", "dislike"]:
        note_to_add = f"Client feedback on '{address}': '{payload.action.upper()}'"
        if payload.reason: note_to_add += f" Reason: {payload.reason}"

    # If a note was created, update the client's profile with this new intel
    if note_to_add:
        await crm_service.update_client_intel(client_id, user_id, notes_to_add=note_to_add)

    session.commit()

    logger.info(f"PORTAL API: Received feedback from client {client_id}.")
    return {"status": "success", "message": "Feedback received"}
