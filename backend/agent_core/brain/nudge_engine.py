# FILE: agent_core/brain/nudge_engine.py
# NEW VERSION: Refactored for a modular, two-pipeline architecture.

import uuid
import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple

from sqlmodel import Session
from sqlalchemy.orm.attributes import flag_modified
from data.models.event import MarketEvent
from data.models.campaign import CampaignBriefing, MatchedClient, CampaignStatus
from data.models.user import User
from data.models.client import Client
from data.models.resource import Resource, ResourceCreate
from data import crm as crm_service
from agent_core.agents import conversation as conversation_agent
from agent_core import llm_client
from .verticals import VERTICAL_CONFIGS
from .nudge_engine_utils import calculate_cosine_similarity

# --- [UNCHANGED] Constants ---
MATCH_THRESHOLD = 25
FEEDBACK_PENALTY_THRESHOLD = 0.85
FEEDBACK_PENALTY_FACTOR = 0.1

# --- [NEW] Reusable Scoring Primitive ---
async def score_event_against_client(
    client: Client,
    event: MarketEvent,
    resource: Resource,
    vertical_config: dict,
    session: Session
) -> Tuple[int, List[str]]:
    """
    Calculates a compatibility score for a single client and a single event.
    This is the core, reusable scoring logic for both pipelines.
    """
    scorer_function = vertical_config.get("scorer")
    if not scorer_function:
        return 0, []

    # 1. Get base score from vertical-specific logic
    resource_embedding = None
    if resource.resource_type == "property" and resource.attributes.get('PublicRemarks'):
        resource_embedding = await llm_client.generate_embedding(resource.attributes['PublicRemarks'])
    
    score, reasons = scorer_function(client, event, resource_embedding, vertical_config)

    # 2. Apply penalty if the nudge is similar to a previously dismissed one
    if resource_embedding:
        negative_preferences = crm_service.get_negative_preferences(client_id=client.id, session=session)
        if negative_preferences:
            is_penalized = any(
                calculate_cosine_similarity(resource_embedding, dismissed_embedding) > FEEDBACK_PENALTY_THRESHOLD
                for dismissed_embedding in negative_preferences
            )
            if is_penalized:
                score *= FEEDBACK_PENALTY_FACTOR
                reasons.append("🎯 Penalized: Similar to a previously dismissed nudge.")
    
    return score, reasons

# --- [NEW] Logic for the Proactive Pipeline ---
async def find_best_match_for_event(event: MarketEvent, user: User, resource: Resource, db_session: Session) -> None:
    """
    For the proactive pipeline. Finds the single best client for a new event
    and creates one nudge, adding other good matches to the audience.
    """
    vertical_config = VERTICAL_CONFIGS.get(user.vertical, {})
    if not vertical_config:
        return

    all_clients = crm_service.get_all_clients(user_id=user.id, session=db_session)
    if not all_clients:
        return

    scored_clients = []
    for client in all_clients:
        # Prevent creating a nudge if one already exists for this client/resource pair
        if crm_service.does_nudge_exist_for_client_and_resource(client.id, resource.id, db_session, event.event_type):
            continue

        score, reasons = await score_event_against_client(client, event, resource, vertical_config, db_session)
        if score >= MATCH_THRESHOLD:
            # Use a timezone-aware min datetime if last_interaction is None
            last_interaction_ts = client.last_interaction or datetime.min.replace(tzinfo=timezone.utc)
            scored_clients.append({
                "client": client,
                "score": score,
                "reasons": reasons,
                "last_interaction": last_interaction_ts
            })

    if not scored_clients:
        logging.info(f"NUDGE_ENGINE: No clients matched threshold for event {event.id}.")
        return

    # Sort by score (desc) and then by last_interaction (desc) as a tie-breaker
    scored_clients.sort(key=lambda x: (x['score'], x['last_interaction']), reverse=True)

    best_match = scored_clients[0]
    primary_matched_client = MatchedClient(
        client_id=best_match['client'].id,
        client_name=best_match['client'].full_name,
        match_score=best_match['score'],
        match_reasons=best_match['reasons']
    )
    
    secondary_audience = [
        MatchedClient(
            client_id=sc['client'].id, client_name=sc['client'].full_name, 
            match_score=sc['score'], match_reasons=sc['reasons']
        ) for sc in scored_clients[1:]
    ]
    
    full_audience = [primary_matched_client] + secondary_audience

    logging.info(f"NUDGE_ENGINE: Found best match for event {event.id}: Client {best_match['client'].id} with score {best_match['score']}.")
    await _create_campaign_from_event(event, user, resource, full_audience, db_session, best_match['client'].id)

# --- [UNCHANGED] Kept for compatibility ---
def _get_client_score_for_event(client: Client, event: MarketEvent, resource_embedding: Optional[List[float]], vertical_config: Dict) -> tuple[int, list[str]]:
    scorer_function = vertical_config.get("scorer")
    if not scorer_function:
        logging.warning(f"No scorer function found for vertical.")
        return 0, []
    return scorer_function(client, event, resource_embedding, vertical_config)

# --- [UNCHANGED] Helper function from original file ---
def _build_content_preview(event: MarketEvent, resource: Resource) -> Dict[str, Any]:
    """
    Builds a standardized content_preview object for the frontend ActionDeck.
    """
    logging.info(f"NUDGE_ENGINE: Building content preview for resource {resource.id} of type {resource.resource_type}")
    
    if resource.resource_type == "web_content":
        attrs = resource.attributes
        content_type = attrs.get("content_type", "article")
        if "youtube.com" in attrs.get("url", "") or "youtu.be" in attrs.get("url", ""):
            content_type = "youtube"
        preview = {
            "content_type": content_type, "url": attrs.get("url"),
            "image_url": attrs.get("thumbnail_url") or attrs.get("image_url"),
            "title": attrs.get("title"), "description": attrs.get("summary") or attrs.get("description"),
            "details": { "author": attrs.get("author"), "duration": attrs.get("duration"), "channel": attrs.get("channel_name"),
                         "views": attrs.get("views"), "published_date": attrs.get("published_date"), "reading_time": attrs.get("reading_time"),
            }
        }
        logging.info(f"NUDGE_ENGINE: Built web_content preview: {preview}")
        return preview

    if resource.resource_type == "property":
        attrs = resource.attributes
        media_items = attrs.get('Media', [])
        all_photos = [media.get('MediaURL') for media in media_items if media.get('MediaCategory') == 'Photo' and media.get('MediaURL')]
        primary_image = next((media.get('MediaURL') for media in media_items if media.get('Order') == 0), None)
        hero_image_url = primary_image or (all_photos[0] if all_photos else None)
        preview = {
            "content_type": "property", "url": attrs.get("listing_url"), "image_url": hero_image_url,
            "photo_gallery": all_photos, "photo_count": len(all_photos), "has_photos": len(all_photos) > 0,
            "title": attrs.get("UnparsedAddress", "Property Listing"), "description": attrs.get("PublicRemarks"),
            "details": { "price": attrs.get("ListPrice"), "bedrooms": attrs.get("BedroomsTotal"),
                         "bathrooms": attrs.get("BathroomsTotalInteger"), "sqft": attrs.get("LivingArea"), "status": attrs.get("MlsStatus"),
            }
        }
        logging.info(f"NUDGE_ENGINE: Built property preview with hero image: {hero_image_url}")
        return preview

    logging.warning(f"NUDGE_ENGINE: No content preview builder for resource type {resource.resource_type}. Returning empty.")
    return {}

# --- [MODIFIED] Helper for creating CampaignBriefing ---
async def _create_campaign_from_event(event: MarketEvent, user: User, resource: Resource, matched_audience: list[MatchedClient], db_session: Session, primary_client_id: uuid.UUID, source: str = "proactive_pipeline"):
    """
    Creates a CampaignBriefing. Now accepts a primary_client_id and a source.
    """
    if crm_service.get_campaign_briefing_by_resource_id(resource.id, db_session):
        logging.warning(f"NUDGE_ENGINE: CampaignBriefing for resource {resource.id} already exists. Skipping creation.")
        return

    vertical_config = VERTICAL_CONFIGS.get(user.vertical, {})
    campaign_config = vertical_config.get("campaign_configs", {}).get(event.event_type)
    if not campaign_config:
        return

    headline = campaign_config["headline"].format(address=resource.attributes.get('UnparsedAddress', 'N/A'))
    key_intel = campaign_config["intel_builder"](event, resource)
    key_intel["content_preview"] = _build_content_preview(event, resource)
    
    ai_draft = await conversation_agent.draft_outbound_campaign_message(
        realtor=user, resource=resource, event_type=event.event_type, matched_audience=matched_audience
    )
    audience_for_db = [m.model_dump(mode='json') for m in matched_audience]
    
    new_briefing = CampaignBriefing(
        id=uuid.uuid4(), user_id=user.id, client_id=primary_client_id,
        triggering_resource_id=resource.id, campaign_type=event.event_type,
        status=CampaignStatus.DRAFT, headline=headline, key_intel=key_intel,
        original_draft=ai_draft, matched_audience=audience_for_db,
        source=source # Add the source of creation
    )
    db_session.add(new_briefing)
    logging.info(f"NUDGE_ENGINE: Successfully created CampaignBriefing {new_briefing.id} for event {event.id}.")

# --- [REMOVED IN THIS VERSION] ---
# The old process_market_event and rescore_client_against_events functions
# have been removed entirely as their logic is now handled by the new modular functions
# and the Celery tasks that call them.