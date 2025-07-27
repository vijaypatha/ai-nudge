# FILE: agent_core/brain/nudge_engine.py
# --- CORE ENGINE - FINAL, FULLY GENERIC VERSION ---
# FIX: Added logic to update existing resources with new event data.

import uuid
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional

from sqlmodel import Session
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

MATCH_THRESHOLD = 25  # Lowered from 40 to make matching more permissive

def _get_client_score_for_event(client: Client, event: MarketEvent, resource_embedding: Optional[List[float]], vertical_config: Dict) -> tuple[int, list[str]]:
    """
    This function is now 100% generic. It dynamically calls the
    vertical-specific scoring function provided in the configuration.
    """
    scorer_function = vertical_config.get("scorer")
    
    if not scorer_function:
        logging.warning(f"No scorer function found for vertical.")
        return 0, []
        
    # Directly call the function from the vertical's config file
    return scorer_function(client, event, resource_embedding, vertical_config)

def _build_content_preview(event: MarketEvent, resource: Resource) -> Dict[str, Any]:
    """
    Builds a standardized content_preview object for the frontend ActionDeck.
    This function centralizes the logic for extracting preview data from various
    resource and event types, ensuring a consistent data structure.
    """
    logging.info(f"NUDGE_ENGINE: Building content preview for resource {resource.id} of type {resource.resource_type}")
    
    # Handle 'web_content' resources (e.g., YouTube videos, articles)
    if resource.resource_type == "web_content":
        attrs = resource.attributes
        content_type = attrs.get("content_type", "article") # Default to article
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

    # Handle 'property' resources from MLS events
    if resource.resource_type == "property":
        attrs = resource.attributes
        preview = {
            "content_type": "property",
            "url": attrs.get("listing_url"),
            "image_url": next((media.get('MediaURL') for media in attrs.get('Media', []) if media.get('Order') == 0), None),
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
        logging.info(f"NUDGE_ENGINE: Built property preview: {preview}")
        return preview

    logging.warning(f"NUDGE_ENGINE: No content preview builder found for resource type {resource.resource_type}. Returning empty object.")
    return {}


async def _create_campaign_from_event(event: MarketEvent, user: User, resource: Resource, matched_audience: list[MatchedClient], db_session: Session):
    """
    Creates a CampaignBriefing from a market event, now with a standardized
    'content_preview' object within the key_intel field for the frontend.
    """
    vertical_config = VERTICAL_CONFIGS.get(user.vertical, {})
    campaign_config = vertical_config.get("campaign_configs", {}).get(event.event_type)
    if not campaign_config:
        logging.warning(f"NUDGE_ENGINE: No campaign config found for event type {event.event_type}. Cannot create campaign.")
        return

    # --- Build Headline and Base Intel ---
    headline_context = {
        "address": resource.attributes.get('UnparsedAddress', 'N/A'),
        "client_name": resource.attributes.get('full_name', 'N/A')
    }
    headline = campaign_config["headline"].format(**headline_context)
    key_intel = campaign_config["intel_builder"](event, resource)

    # --- SURGICAL MODIFICATION: Add the standardized content preview ---
    # This ensures the frontend ActionDeck always has the data it needs.
    key_intel["content_preview"] = _build_content_preview(event, resource)
    logging.info(f"NUDGE_ENGINE: Final key_intel for campaign: {key_intel}")
    # --- END MODIFICATION ---

    # --- Generate AI Draft ---
    ai_draft = await conversation_agent.draft_outbound_campaign_message(
        realtor=user, resource=resource, event_type=event.event_type, matched_audience=matched_audience
    )

    # --- Create and Save the CampaignBriefing ---
    audience_for_db = [m.model_dump(mode='json') for m in matched_audience]
    new_briefing = CampaignBriefing(
        id=uuid.uuid4(),
        user_id=user.id,
        triggering_resource_id=resource.id,
        campaign_type=event.event_type,
        status=CampaignStatus.DRAFT,
        headline=headline,
        key_intel=key_intel, # This now contains the content_preview
        original_draft=ai_draft,
        matched_audience=audience_for_db
    )
    db_session.add(new_briefing)
    logging.info(f"NUDGE_ENGINE: Successfully created CampaignBriefing {new_briefing.id} for event {event.id}.")

async def process_market_event(event: MarketEvent, user: User, db_session: Session = None):
    # Set the user_id for the event
    event.user_id = user.id
    
    # Create session if not provided
    if db_session is None:
        from data.database import engine
        from sqlmodel import Session
        db_session = Session(engine)
    
    # Save the event to the database first
    db_session.add(event)
    db_session.commit()
    db_session.refresh(event)
    
    vertical_config = VERTICAL_CONFIGS.get(user.vertical)
    if not event.payload or not vertical_config:
        return

    resource_payload = event.payload
    resource = None

    # Determine resource type from vertical config, or specifically for 'content_suggestion'
    resource_type_from_config = vertical_config.get("resource_type")

    # --- START SURGICAL MODIFICATION ---
    if event.event_type == 'content_suggestion':
        resource_type = "web_content"
        entity_identifier = resource_payload.get('url')
        if not entity_identifier:
            logging.error(f"NUDGE_ENGINE: Content suggestion event {event.id} missing URL. Cannot create resource.")
            return

        existing_resource = db_session.query(Resource).filter(
            Resource.entity_id == entity_identifier,
            Resource.user_id == user.id,
            Resource.resource_type == resource_type
        ).first()

        if existing_resource:
            resource = existing_resource
            logging.info(f"NUDGE_ENGINE: Re-using existing resource {resource.id} for content event {event.id}.")
            resource.attributes.update(resource_payload)
            db_session.add(resource)
        else:
            resource_create_payload = ResourceCreate(
                user_id=user.id,
                resource_type=resource_type,
                status="active",
                attributes=resource_payload,
                entity_id=entity_identifier
            )
            resource = Resource.model_validate(resource_create_payload)
            db_session.add(resource)
            db_session.flush()
            db_session.refresh(resource)
            logging.info(f"NUDGE_ENGINE: Created new resource {resource.id} (type: {resource_type}) for content event {event.id}.")

    # --- END SURGICAL MODIFICATION ---
    elif resource_type_from_config == "property":
        resource = crm_service.get_resource_by_entity_id(event.entity_id, db_session)
        
        if resource:
            # --- FIX: If resource exists, update it with the latest data ---
            logging.info(f"Found existing resource {resource.id}. Updating with new event data.")
            resource.attributes.update(resource_payload)
            db_session.add(resource) # Mark it for the session
        else:
            # If it's a new resource, create it
            logging.info(f"No existing resource found for entity_id {event.entity_id}. Creating new one.")
            resource_payload['listing_url'] = next((media['MediaURL'] for media in resource_payload.get('Media', []) if media.get('Order') == 0), None)
            resource_create_payload = ResourceCreate(
                user_id=user.id,
                resource_type="property", status="active", attributes=resource_payload, entity_id=str(event.entity_id)
            )
            resource = Resource.model_validate(resource_create_payload)
            db_session.add(resource)
            db_session.flush() # Flush to get the ID for the new resource
            db_session.refresh(resource)

    elif resource_type_from_config == "client_profile":
         resource = Resource(id=event.entity_id, attributes={"full_name": resource_payload.get('full_name', 'N/A')}, user_id=user.id)

    else:
        # If neither content_suggestion nor a configured resource_type matches, log and return
        logging.warning(f"NUDGE_ENGINE: Unhandled event type '{event.event_type}' or resource type '{resource_type_from_config}'. Skipping resource processing.")
        return # Exit if resource cannot be handled/created

    if not resource:
        logging.error(f"NUDGE_ENGINE: Resource could not be determined or created for event {event.id}. Skipping further processing.")
        return

    # --- Generate embedding based on the final state of the resource (new or updated) ---
    # This logic needs to be adapted for 'web_content'
    resource_embedding = None
    if resource.resource_type == "web_content" and resource.attributes.get('summary'):
        resource_embedding = await llm_client.generate_embedding(resource.attributes['summary'])
        logging.info(f"NUDGE_ENGINE: Generated embedding for web_content summary.")
    elif resource.resource_type == "property":
        remarks = resource.attributes.get('PublicRemarks')
        if remarks:
            resource_embedding = await llm_client.generate_embedding(remarks)
            logging.info(f"NUDGE_ENGINE: Generated embedding for property remarks.")
    # No embedding needed for client_profile based scoring in current setup.

    all_clients = crm_service.get_all_clients(user_id=user.id)
    logging.info(f"NUDGE_ENGINE: Found {len(all_clients)} clients for user {user.id} to score against event {event.id}.")

    matched_audience = []

    for client in all_clients:
        if crm_service.does_nudge_exist_for_client_and_resource(client_id=client.id, resource_id=resource.id, session=db_session, event_type=event.event_type):
            logging.info(f"NUDGE_ENGINE: Nudge for event type '{event.event_type}' already exists for client {client.id} and resource {resource.id}. Skipping client {client.full_name}.")
            continue

        score, reasons = _get_client_score_for_event(client, event, resource_embedding, vertical_config)
        
        if score >= MATCH_THRESHOLD:
            logging.info(f"NUDGE_ENGINE: Client {client.id} ({client.full_name}) matched event {event.id} with score {score}. Reasons: {reasons}")
            matched_audience.append(MatchedClient(
                client_id=client.id, client_name=client.full_name, match_score=score, match_reasons=reasons
            ))
        else:
            logging.info(f"NUDGE_ENGINE: Client {client.id} ({client.full_name}) did not match event {event.id}. Score: {score}")

    if matched_audience and resource:
        logging.info(f"NUDGE_ENGINE: Creating campaign for {len(matched_audience)} matched clients for event {event.id}.")
        await _create_campaign_from_event(event, user, resource, matched_audience, db_session=db_session)
    else:
        logging.info(f"NUDGE_ENGINE: No clients matched for event {event.id}. No campaign created.")
