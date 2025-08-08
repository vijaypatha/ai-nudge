# FILE: agent_core/brain/nudge_engine.py
# --- MODIFIED: Added feedback loop to penalize previously dismissed nudges ---

import uuid
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional

from sqlmodel import Session, select
from sqlalchemy.orm.attributes import flag_modified
from data.models.event import MarketEvent
from data.models.campaign import CampaignBriefing, MatchedClient, CampaignStatus
from data.models.user import User
from data.models.client import Client
from data.models.resource import Resource, ResourceCreate
from data import crm as crm_service
from agent_core.agents import conversation as conversation_agent
from agent_core import llm_client

# The engine now imports its entire configuration from the verticals package
from .verticals import VERTICAL_CONFIGS

# --- NEW: Import the similarity function for the feedback loop ---
from .nudge_engine_utils import calculate_cosine_similarity

MATCH_THRESHOLD = 25  # Lowered from 40 to make matching more permissive
FEEDBACK_PENALTY_THRESHOLD = 0.85 # Similarity score above which a penalty is applied
FEEDBACK_PENALTY_FACTOR = 0.1 # Reduce score by 90% if it's too similar to a dismissed nudge

def _get_client_score_for_event(client: Client, event: MarketEvent, resource_embedding: Optional[List[float]], vertical_config: Dict) -> tuple[int, list[str]]:
    """
    This function is now 100% generic. It dynamically calls the
    vertical-specific scoring function provided in the configuration.
    (Functionality unchanged)
    """
    scorer_function = vertical_config.get("scorer")
    
    if not scorer_function:
        logging.warning(f"No scorer function found for vertical.")
        return 0, []
        
    return scorer_function(client, event, resource_embedding, vertical_config)

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
            "content_type": content_type,
            "url": attrs.get("url"),
            "image_url": attrs.get("thumbnail_url") or attrs.get("image_url"),
            "title": attrs.get("title"),
            "description": attrs.get("summary") or attrs.get("description"),
            "details": {
                "author": attrs.get("author"),
                "duration": attrs.get("duration"),
                "channel": attrs.get("channel_name"),
                "views": attrs.get("views"),
                "published_date": attrs.get("published_date"),
                "reading_time": attrs.get("reading_time"),
            }
        }
        logging.info(f"NUDGE_ENGINE: Built web_content preview: {preview}")
        return preview

    if resource.resource_type == "property":
        attrs = resource.attributes
        media_items = attrs.get('Media', [])
        
        # Get all photo URLs for gallery
        all_photos = [media.get('MediaURL') for media in media_items if media.get('MediaCategory') == 'Photo' and media.get('MediaURL')]
        
        # --- THIS IS THE FIX ---
        # 1. Try to find the primary image with Order == 0.
        primary_image = next((media.get('MediaURL') for media in media_items if media.get('Order') == 0), None)
        # 2. If it fails, use the first available photo from the gallery as a fallback.
        hero_image_url = primary_image or (all_photos[0] if all_photos else None)
        # --- END OF FIX ---

        preview = {
            "content_type": "property",
            "url": attrs.get("listing_url"),
            "image_url": hero_image_url,
            "photo_gallery": all_photos,
            "photo_count": len(all_photos),
            "has_photos": len(all_photos) > 0,
            "title": attrs.get("UnparsedAddress", "Property Listing"),
            "description": attrs.get("PublicRemarks"),
            "details": {
                "price": attrs.get("ListPrice"),
                "bedrooms": attrs.get("BedroomsTotal"),
                "bathrooms": attrs.get("BathroomsTotalInteger"),
                "sqft": attrs.get("LivingArea"),
                "status": attrs.get("MlsStatus"),
            }
        }
        logging.info(f"NUDGE_ENGINE: Built property preview with hero image: {hero_image_url}")
        return preview

    logging.warning(f"NUDGE_ENGINE: No content preview builder for resource type {resource.resource_type}. Returning empty.")
    return {}


async def _create_campaign_from_event(event: MarketEvent, user: User, resource: Resource, matched_audience: list[MatchedClient], db_session: Session):
    """
    Creates a CampaignBriefing from a market event.
    (Functionality unchanged)
    """
    vertical_config = VERTICAL_CONFIGS.get(user.vertical, {})
    campaign_config = vertical_config.get("campaign_configs", {}).get(event.event_type)
    if not campaign_config:
        logging.warning(f"NUDGE_ENGINE: No campaign config found for event type {event.event_type}. Cannot create campaign.")
        return

    headline_context = {
        "address": resource.attributes.get('UnparsedAddress', 'N/A'),
        "client_name": resource.attributes.get('full_name', 'N/A')
    }
    headline = campaign_config["headline"].format(**headline_context)
    key_intel = campaign_config["intel_builder"](event, resource)
    key_intel["content_preview"] = _build_content_preview(event, resource)
    logging.info(f"NUDGE_ENGINE: Final key_intel for campaign: {key_intel}")

    ai_draft = await conversation_agent.draft_outbound_campaign_message(
        realtor=user, resource=resource, event_type=event.event_type, matched_audience=matched_audience
    )

    # --- FIX: Properly serialize matched_audience to JSON ---
    audience_for_db = []
    for m in matched_audience:
        client_data = {
            "client_id": str(m.client_id),
            "client_name": m.client_name,
            "match_score": m.match_score,
            "match_reasons": m.match_reasons
        }
        audience_for_db.append(client_data)
    
    new_briefing = CampaignBriefing(
        id=uuid.uuid4(),
        user_id=user.id,
        triggering_resource_id=resource.id,
        campaign_type=event.event_type,
        status=CampaignStatus.DRAFT,
        headline=headline,
        key_intel=key_intel,
        original_draft=ai_draft,
        matched_audience=audience_for_db
    )
    db_session.add(new_briefing)
    logging.info(f"NUDGE_ENGINE: Successfully created CampaignBriefing {new_briefing.id} for event {event.id}.")

async def process_market_event(event: MarketEvent, user: User, db_session: Session = None):
    # The 'user' parameter is kept for compatibility but will be replaced by the correct user.
    if db_session is None:
        from data.database import engine
        db_session = Session(engine)

    # --- FIX 1: Ensure we operate with the correct user for this specific event ---
    if not event.user_id:
        logging.error(f"NUDGE_ENGINE: MarketEvent {event.id} is missing a user_id. Cannot process.")
        return

    correct_user = crm_service.get_user_by_id(user_id=event.user_id, session=db_session)
    if not correct_user:
        logging.error(f"NUDGE_ENGINE: Could not find user with ID {event.user_id} from event {event.id}.")
        return
    user = correct_user
    # --- END OF FIX 1 ---

    db_session.add(event)
    db_session.commit()
    db_session.refresh(event)
    
    vertical_config = VERTICAL_CONFIGS.get(user.vertical)
    if not event.payload or not vertical_config:
        return

    resource_payload = event.payload
    resource = None
    resource_type_from_config = vertical_config.get("resource_type")

    if event.event_type == 'content_suggestion':
        resource_type = "web_content"
        entity_identifier = resource_payload.get('url')
        if not entity_identifier: return
        existing_resource = db_session.query(Resource).filter(
            Resource.entity_id == entity_identifier,
            Resource.user_id == user.id,
            Resource.resource_type == resource_type
        ).first()
        if existing_resource:
            resource = existing_resource
            resource.attributes.update(resource_payload)
        else:
            resource = Resource.model_validate(ResourceCreate(
                user_id=user.id, resource_type=resource_type, status="active",
                attributes=resource_payload, entity_id=entity_identifier
            ))
    elif resource_type_from_config == "property":
        resource = crm_service.get_resource_by_entity_id(event.entity_id, db_session)
        if resource:
            resource.attributes.update(resource_payload)
        else:
            resource_payload['listing_url'] = next((media['MediaURL'] for media in resource_payload.get('Media', []) if media.get('Order') == 0), None)
            resource = Resource.model_validate(ResourceCreate(
                user_id=user.id, resource_type="property", status="active",
                attributes=resource_payload, entity_id=str(event.entity_id)
            ))
    elif resource_type_from_config == "client_profile":
         resource = Resource(id=event.entity_id, attributes={"full_name": resource_payload.get('full_name', 'N/A')}, user_id=user.id)
    else:
        logging.warning(f"NUDGE_ENGINE: Unhandled event type '{event.event_type}'. Skipping.")
        return

    if not resource: return
    db_session.add(resource)
    db_session.flush()
    db_session.refresh(resource)

    resource_embedding = None
    if resource.resource_type == "web_content" and resource.attributes.get('summary'):
        resource_embedding = await llm_client.generate_embedding(resource.attributes['summary'])
    elif resource.resource_type == "property" and resource.attributes.get('PublicRemarks'):
        resource_embedding = await llm_client.generate_embedding(resource.attributes['PublicRemarks'])

    # --- FIX 2: Process clients in batches to conserve memory ---
    matched_audience = []
    page = 1
    batch_size = 5  # Process 500 clients at a time

    while True:
        logging.info(f"NUDGE_ENGINE: Processing client batch, page {page}, for user {user.id}...")
        client_batch = crm_service.get_clients_in_batches(
            user_id=user.id, session=db_session, batch_size=batch_size, page=page
        )
        
        # When an empty batch is returned, we have processed all clients.
        if not client_batch:
            logging.info(f"NUDGE_ENGINE: No more clients to process for user {user.id}.")
            break

        logging.info(f"NUDGE_ENGINE: Scoring {len(client_batch)} clients in batch {page} against event {event.id}.")

        for client in client_batch:
            if crm_service.does_nudge_exist_for_client_and_resource(client.id, resource.id, db_session, event.event_type):
                continue

            score, reasons = _get_client_score_for_event(client, event, resource_embedding, vertical_config)
            
            if resource_embedding:
                negative_preferences = crm_service.get_negative_preferences(client_id=client.id, session=db_session)
                if negative_preferences:
                    is_penalized = any(
                        calculate_cosine_similarity(resource_embedding, dismissed_embedding) > FEEDBACK_PENALTY_THRESHOLD
                        for dismissed_embedding in negative_preferences
                    )
                    if is_penalized:
                        score *= FEEDBACK_PENALTY_FACTOR
                        reasons.append("🎯 Penalized: Similar to a previously dismissed nudge.")

            if score >= MATCH_THRESHOLD:
                matched_audience.append(MatchedClient(
                    client_id=client.id, client_name=client.full_name, match_score=score, match_reasons=reasons
                ))
        
        # Move to the next page for the next iteration
        page += 1
    # --- END OF FIX 2 ---

    if matched_audience and resource:
        logging.info(f"NUDGE_ENGINE: Creating campaign for {len(matched_audience)} matched clients for event {event.id}.")
        await _create_campaign_from_event(event, user, resource, matched_audience, db_session=db_session)
    else:
        logging.info(f"NUDGE_ENGINE: No clients matched for event {event.id}. No campaign created.")

# Handles re-evaluating a single client against existing events.
async def rescore_client_against_events(client_id: uuid.UUID, user_id: uuid.UUID, lookback_days: int = 30):
    """
    Re-evaluates a single client against recent, active events and updates their
    nudges (CampaignBriefings). This is triggered when a client's profile changes.
    --- MODIFIED: Manages a single session to ensure data consistency. ---
    """
    logging.info(f"NUDGE_ENGINE (RE-SCORE): Starting re-score for client {client_id}.")
    from data.database import engine
    
    with Session(engine) as session:
        # First, clear any old, now-irrelevant draft nudges for this client.
        crm_service.delete_draft_campaigns_for_client(client_id, user_id, session)
        
        # Now fetch the client and user using the SAME session to guarantee we have the latest data.
        client = crm_service.get_client_by_id(client_id, user_id, session=session)
        user = crm_service.get_user_by_id(user_id, session=session)
        
        if not client or not user:
            logging.error(f"NUDGE_ENGINE (RE-SCORE): Client {client_id} or User {user_id} not found.")
            session.rollback() # Rollback if essential data is missing
            return

        vertical_config = VERTICAL_CONFIGS.get(user.vertical)
        if not vertical_config:
            logging.error(f"NUDGE_ENGINE (RE-SCORE): No vertical config for user {user.id}.")
            return

        active_events = crm_service.get_active_events_in_range(lookback_days=lookback_days, session=session)
        logging.info(f"NUDGE_ENGINE (RE-SCORE): Found {len(active_events)} active events to re-score against.")

        for event in active_events:
            resource = crm_service.get_resource_by_entity_id(event.entity_id, session)
            if not resource:
                continue

            resource_embedding = None
            if resource.resource_type == "property" and resource.attributes.get('PublicRemarks'):
                resource_embedding = await llm_client.generate_embedding(resource.attributes['PublicRemarks'])
            elif resource.resource_type == "web_content" and resource.attributes.get('summary'):
                resource_embedding = await llm_client.generate_embedding(resource.attributes['summary'])

            score, reasons = _get_client_score_for_event(client, event, resource_embedding, vertical_config)
            
            if resource_embedding:
                negative_preferences = crm_service.get_negative_preferences(client_id=client.id, session=session)
                is_penalized = any(
                    calculate_cosine_similarity(resource_embedding, dismissed_embedding) > FEEDBACK_PENALTY_THRESHOLD
                    for dismissed_embedding in negative_preferences
                )
                if is_penalized:
                    score *= FEEDBACK_PENALTY_FACTOR
                    reasons.append("🎯 Penalized: Similar to a previously dismissed nudge.")

            draft_nudge_for_event = session.exec(
                select(CampaignBriefing).where(
                    CampaignBriefing.triggering_resource_id == resource.id,
                    CampaignBriefing.campaign_type == event.event_type,
                    CampaignBriefing.status == CampaignStatus.DRAFT
                )
            ).first()

            if score >= MATCH_THRESHOLD:
                logging.info(f"NUDGE_ENGINE (RE-SCORE): Client {client.id} MATCHED resource {resource.id} with new score {score}.")
                new_match_data = MatchedClient(
                    client_id=client.id, client_name=client.full_name, match_score=score, match_reasons=reasons
                )
                
                if draft_nudge_for_event:
                    audience = list(draft_nudge_for_event.matched_audience)
                    client_found = False
                    for i, member in enumerate(audience):
                        if member.get("client_id") == str(client.id):
                            audience[i] = new_match_data.model_dump(mode='json')
                            client_found = True
                            break
                    if not client_found:
                        audience.append(new_match_data.model_dump(mode='json'))
                    
                    draft_nudge_for_event.matched_audience = audience
                    flag_modified(draft_nudge_for_event, "matched_audience")
                    session.add(draft_nudge_for_event)
                else:
                    await _create_campaign_from_event(event, user, resource, [new_match_data], db_session=session)
            
            else:
                if draft_nudge_for_event:
                    initial_audience = list(draft_nudge_for_event.matched_audience)
                    updated_audience = [
                        member for member in initial_audience 
                        if member.get("client_id") != str(client.id)
                    ]
                    
                    if len(updated_audience) < len(initial_audience):
                        logging.info(f"NUDGE_ENGINE (CLEANUP): Removing client {client.id} from nudge {draft_nudge_for_event.id}.")
                        draft_nudge_for_event.matched_audience = updated_audience
                        flag_modified(draft_nudge_for_event, "matched_audience")
                        session.add(draft_nudge_for_event)
        
        # A single commit at the end handles all additions, updates, and deletions.
        session.commit()
        logging.info(f"NUDGE_ENGINE (RE-SCORE): Finished re-scoring for client {client_id}.")