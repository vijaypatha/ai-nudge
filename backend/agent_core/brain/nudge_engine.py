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

MATCH_THRESHOLD = 40

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

async def _create_campaign_from_event(event: MarketEvent, user: User, resource: Resource, matched_audience: list[MatchedClient], db_session: Session):
    vertical_config = VERTICAL_CONFIGS.get(user.vertical, {})
    campaign_config = vertical_config.get("campaign_configs", {}).get(event.event_type)
    if not campaign_config:
        return

    headline_context = {
        "address": resource.attributes.get('UnparsedAddress', 'N/A'),
        "client_name": resource.attributes.get('full_name', 'N/A')
    }
    headline = campaign_config["headline"].format(**headline_context)
    key_intel = campaign_config["intel_builder"](event, resource)

    ai_draft = await conversation_agent.draft_outbound_campaign_message(
        realtor=user, resource=resource, event_type=event.event_type, matched_audience=matched_audience
    )

    audience_for_db = [m.model_dump(mode='json') for m in matched_audience]
    new_briefing = CampaignBriefing(
        id=uuid.uuid4(),
        user_id=user.id,
        triggering_resource_id=resource.id,
        campaign_type=event.event_type,
        status=CampaignStatus.DRAFT,
        headline=headline,
        key_intel=key_intel,
        listing_url=resource.attributes.get('listing_url'),
        original_draft=ai_draft,
        matched_audience=audience_for_db
    )
    db_session.add(new_briefing)

async def process_market_event(event: MarketEvent, user: User, db_session: Session):
    vertical_config = VERTICAL_CONFIGS.get(user.vertical)
    if not event.payload or not vertical_config:
        return

    resource_payload = event.payload
    resource = None

    if vertical_config.get("resource_type") == "property":
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
                resource_type="property", status="active", attributes=resource_payload, entity_id=event.entity_id
            )
            resource = Resource.model_validate(resource_create_payload, update={'user_id': user.id})
            db_session.add(resource)
            db_session.flush() # Flush to get the ID for the new resource
            db_session.refresh(resource)

    # --- Generate embedding based on the final state of the resource (new or updated) ---
    remarks = resource.attributes.get('PublicRemarks') if resource else None
    resource_embedding = await llm_client.generate_embedding(remarks) if remarks else None

    all_clients = crm_service.get_all_clients(user_id=user.id)
    matched_audience = []

    for client in all_clients:
        if vertical_config.get("resource_type") == "client_profile":
             resource = Resource(id=client.id, attributes={"full_name": client.full_name}, user_id=user.id)

        score, reasons = _get_client_score_for_event(client, event, resource_embedding, vertical_config)
        
        if score >= MATCH_THRESHOLD:
            if resource and crm_service.does_nudge_exist_for_client_and_resource(client_id=client.id, resource_id=resource.id, session=db_session, event_type=event.event_type):
                logging.info(f"Nudge for event type '{event.event_type}' already exists for client {client.id} and resource {resource.id}. Skipping.")
                continue

            matched_audience.append(MatchedClient(
                client_id=client.id, client_name=client.full_name, match_score=score, match_reasons=reasons
            ))

    if matched_audience and resource:
        await _create_campaign_from_event(event, user, resource, matched_audience, db_session=db_session)
