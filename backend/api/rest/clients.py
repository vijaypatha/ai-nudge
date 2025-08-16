# File Path: backend/api/rest/clients.py
# --- DEFINITIVE FIX: The /intel endpoint no longer clears the recommendation slate, allowing multiple actions.

import logging
import json # Correctly placed import
from datetime import datetime
from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel
from sqlmodel import Session

# --- ADDED: Imports for Redis client and app settings ---
import redis
from common.config import get_settings

from data.models.user import User, UserUpdate
from api.security import get_current_user_from_token

from data.models.client import Client, ClientCreate, ClientUpdate, ClientTagUpdate
from data.models.message import ScheduledMessage
from data import crm as crm_service
from data.database import engine
from agent_core import audience_builder
from api.websocket_manager import manager as websocket_manager
from celery_tasks import initial_data_fetch_for_user_task, backfill_nudges_for_client_task
from data.models.campaign import MatchedClient

router = APIRouter(prefix="/clients", tags=["Clients"])

# --- ADDED: Initialize a Redis client for publishing messages ---
settings = get_settings()
redis_client = redis.from_url(settings.REDIS_URL)
USER_NOTIFICATION_CHANNEL = "user-notifications" # Must match the channel in main.py

class ClientSearchQuery(BaseModel):
    natural_language_query: Optional[str] = None
    tags: Optional[List[str]] = None

class AddTagsPayload(BaseModel):
    tags: List[str]

# --- NEW: Pydantic model for the consolidated intel update payload ---
class UpdateIntelPayload(BaseModel):
    tags_to_add: Optional[List[str]] = None
    notes_to_add: Optional[str] = None
    active_recommendation_id: Optional[UUID] = None

# --- NEW: Pydantic model for the manual notes update payload ---
class UpdateNotesPayload(BaseModel):
    notes: str

# --- NEW: Pydantic models for the client-centric nudge response ---
class NudgeResource(BaseModel):
    address: Optional[str] = None
    price: Optional[float] = None
    beds: Optional[int] = None
    baths: Optional[int] = None
    attributes: Dict[str, Any] = {}

class ClientNudgeResponse(BaseModel):
    id: UUID
    campaign_id: UUID
    headline: str
    campaign_type: str
    resource: NudgeResource
    key_intel: Dict[str, Any] = {}
    original_draft: str
    edited_draft: Optional[str] = None
    matched_audience: List[MatchedClient]


@router.post("/manual", response_model=Client)
async def add_manual_client(
    client_data: ClientCreate,
    current_user: User = Depends(get_current_user_from_token)
):
    """
    Creates a single new client, triggers the backfill pipeline, and updates onboarding state.
    """
    client, is_new = await crm_service.create_or_update_client(
        user_id=current_user.id, 
        client_data=client_data
    )
    
    # --- ADDED: Dispatch backfill task for new clients ---
    if is_new:
        logging.info(f"API: New client {client.id} created, dispatching backfill task.")
        backfill_nudges_for_client_task.delay(client_id=str(client.id))
    
    # This logic appears to be for the *user's* first contact, not a new client in general.
    # It correctly triggers the *user's* initial data fetch.
    try:
        if not current_user.onboarding_state.get('contacts_imported'):
            logging.info(f"Updating onboarding state for user {current_user.id} after manual contact add.")
            updated_state = current_user.onboarding_state.copy()
            updated_state['contacts_imported'] = True
            
            update_data = UserUpdate(onboarding_state=updated_state)
            crm_service.update_user(user_id=current_user.id, update_data=update_data)
            logging.info(f"Successfully updated onboarding state for user {current_user.id}.")
            logging.info(f"Triggering initial data fetch for user {current_user.id}.")
            initial_data_fetch_for_user_task.delay(user_id=str(current_user.id))
    except Exception as e:
        logging.error(f"Could not update onboarding_state for user {current_user.id} after manual add: {e}")
    
    return client

@router.post("/search", response_model=List[Client])
async def search_clients(query: ClientSearchQuery, current_user: User = Depends(get_current_user_from_token)):
    all_clients = crm_service.get_all_clients(user_id=current_user.id)
    final_results = set()

    if query.natural_language_query:
        matched_ids = await audience_builder.find_clients_by_semantic_query(query.natural_language_query, user_id=current_user.id)
        final_results.update(matched_ids)

    if query.tags:
        query_tags_lower = {t.lower() for t in query.tags}
        tag_ids = {
            c.id for c in all_clients 
            if (c.user_tags and any(ut.lower() in query_tags_lower for ut in c.user_tags)) or \
               (c.ai_tags and any(at.lower() in query_tags_lower for at in c.ai_tags))
        }
        
        if query.natural_language_query:
            final_results.intersection_update(tag_ids)
        else:
            final_results.update(tag_ids)

    if not query.natural_language_query and not query.tags:
        return all_clients

    return [client for client in all_clients if client.id in final_results]

@router.post("/{client_id}/intel", response_model=Client)
async def update_client_intel_endpoint(
    client_id: UUID,
    payload: UpdateIntelPayload,
    current_user: User = Depends(get_current_user_from_token),
):
    """
    A single, powerful endpoint to update client intel based on AI recommendations.
    """
    # --- MODIFIED: Added 'await' for the async CRM function ---
    updated_client = await crm_service.update_client_intel(
        client_id=client_id,
        user_id=current_user.id,
        tags_to_add=payload.tags_to_add,
        notes_to_add=payload.notes_to_add
    )
    # If notes were added via an accepted AI suggestion, we must re-run the
    # relationship planner to parse those notes for any actionable dates.
    if payload.notes_to_add and updated_client:
        try:
            from agent_core.brain import relationship_planner
            logging.info(f"API: Notes added via intel, triggering relationship planner for client {client_id}")
            await relationship_planner.plan_relationship_campaign(client=updated_client, user=current_user)
        except Exception as e:
            # Log the error but do not fail the request, as the intel was still saved.
            logging.error(f"API: Failed to trigger relationship planner after intel update for client {client_id}: {e}")

    if not updated_client:
        raise HTTPException(status_code=404, detail="Client not found or failed to update.")

    if payload.active_recommendation_id:
        logging.info(f"API: Processed intel action for client {client_id} from slate {payload.active_recommendation_id}. Slate status was not changed.")

    return updated_client

@router.put("/{client_id}/notes", response_model=Client)
async def update_client_notes_endpoint(
    client_id: UUID,
    payload: UpdateNotesPayload,
    current_user: User = Depends(get_current_user_from_token)
):
    """
    Updates the client's notes from a manual user edit. This overwrites the notes.
    """
    # --- MODIFIED: Added 'await' for the async CRM function ---
    updated_client = await crm_service.update_client_notes(
        client_id=client_id,
        notes=payload.notes,
        user_id=current_user.id
    )
    if not updated_client:
        raise HTTPException(status_code=404, detail="Client not found.")
    return updated_client


@router.post("/{client_id}/recommendations/clear", status_code=status.HTTP_204_NO_CONTENT)
async def clear_client_recommendations_endpoint(
    client_id: UUID,
    current_user: User = Depends(get_current_user_from_token)
):
    """
    Clears all 'active' recommendation slates for a given client.
    This is called by the frontend when new messages arrive to prevent stale suggestions.
    """
    success = crm_service.clear_active_recommendations(
        client_id=client_id,
        user_id=current_user.id
    )
    if not success:
        # Note: We don't raise 404 here to avoid frontend errors if the client exists but has no slates.
        logging.warning(f"API: Call to clear recommendations for client {client_id} completed. Success: {success}")
    return None


@router.post("/{client_id}/tags", response_model=Client)
async def add_tags_to_client(
    client_id: UUID,
    payload: AddTagsPayload,
    current_user: User = Depends(get_current_user_from_token),
):
    """
    Appends one or more tags to a client's user_tags list.
    NOTE: This endpoint is now superseded by the more powerful /intel endpoint,
    but is kept for potential direct use.
    """
    client = crm_service.get_client_by_id(client_id=client_id, user_id=current_user.id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found.")

    updated_client = await crm_service.add_client_tags(
        client_id=client_id, 
        tags_to_add=payload.tags,
        user_id=current_user.id
    )

    if not updated_client:
        raise HTTPException(status_code=500, detail="Failed to update client tags.")

    return updated_client

@router.put("/{client_id}/tags", response_model=Client)
async def update_client_tags_endpoint(client_id: UUID, tag_data: ClientTagUpdate, current_user: User = Depends(get_current_user_from_token)):
    updated_client = await crm_service.update_client_tags(client_id, tag_data.user_tags, user_id=current_user.id)
    if not updated_client:
        raise HTTPException(status_code=404, detail="Client not found.")
    return updated_client

@router.get("", response_model=List[Client])
async def get_all_clients_endpoint(current_user: User = Depends(get_current_user_from_token)):
    return crm_service.get_all_clients(user_id=current_user.id)

@router.get("/debug/list-ids")
async def list_client_ids(current_user: User = Depends(get_current_user_from_token)):
    """Debug endpoint to list all client IDs for the current user."""
    clients = crm_service.get_all_clients(user_id=current_user.id)
    return {
        "user_id": str(current_user.id),
        "client_count": len(clients),
        "clients": [
            {
                "id": str(client.id),
                "name": client.full_name,
                "phone": client.phone
            }
            for client in clients
        ]
    }

@router.get("/{client_id}", response_model=Client)
async def get_client_by_id_endpoint(client_id: UUID, current_user: User = Depends(get_current_user_from_token)):
    logging.info(f"API: Requesting client {client_id} for user {current_user.id}")
    client = crm_service.get_client_by_id(client_id=client_id, user_id=current_user.id)
    if not client:
        logging.warning(f"API: Client {client_id} not found for user {current_user.id}")
    else:
        logging.info(f"API: Found client {client_id} ({client.full_name}) for user {current_user.id}")
    if client:
        return client
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

@router.get("/{client_id}/scheduled-messages", response_model=List[ScheduledMessage])
async def get_client_scheduled_messages(client_id: UUID, current_user: User = Depends(get_current_user_from_token)):
    messages = crm_service.get_scheduled_messages_for_client(client_id=client_id, user_id=current_user.id)
    return messages

# --- NEW ENDPOINT FOR CLIENT-CENTRIC NUDGE VIEW ---
@router.get("/{client_id}/nudges", response_model=List[ClientNudgeResponse])
async def get_nudges_for_client(
    client_id: UUID,
    current_user: User = Depends(get_current_user_from_token)
):
    """
    Retrieves all active nudges for a single client, safely handling
    potentially incomplete audience data and data type mismatches.
    """
    client_nudges = []
    with Session(engine) as session:
        all_draft_campaigns = crm_service.get_new_campaign_briefings_for_user(user_id=current_user.id, session=session)

        for campaign in all_draft_campaigns:
            is_match = any(
                str(audience_member.get("client_id")) == str(client_id)
                for audience_member in campaign.matched_audience
            )
            if not is_match:
                continue
            
            nudge_resource = NudgeResource(attributes={})
            if campaign.triggering_resource_id:
                resource = crm_service.get_resource_by_id(
                    resource_id=campaign.triggering_resource_id,
                    user_id=current_user.id,
                    session=session
                )
                if resource and resource.attributes:
                    # FIX: Safely cast numeric types to prevent validation errors
                    try:
                        price = float(resource.attributes.get("ListPrice")) if resource.attributes.get("ListPrice") is not None else None
                        beds = int(resource.attributes.get("BedroomsTotal")) if resource.attributes.get("BedroomsTotal") is not None else None
                        baths = int(resource.attributes.get("BathroomsTotalInteger")) if resource.attributes.get("BathroomsTotalInteger") is not None else None
                        nudge_resource = NudgeResource(
                            address=resource.attributes.get("UnparsedAddress"),
                            price=price,
                            beds=beds,
                            baths=baths,
                            attributes=resource.attributes
                        )
                    except (ValueError, TypeError):
                        # If casting fails, still proceed but with empty resource details
                        logging.warning(f"Could not parse resource attributes for campaign {campaign.id}")

            sanitized_audience = [
                MatchedClient(
                    client_id=member.get("client_id"),
                    client_name=member.get("client_name"),
                    match_score=member.get("match_score", 0),
                    match_reasons=member.get("match_reasons", [])
                ) for member in campaign.matched_audience
            ]
            
            client_nudge = ClientNudgeResponse(
                id=campaign.id, campaign_id=campaign.id, headline=campaign.headline,
                campaign_type=campaign.campaign_type, resource=nudge_resource,
                key_intel=campaign.key_intel, original_draft=campaign.original_draft,
                edited_draft=campaign.edited_draft, matched_audience=sanitized_audience
            )
            client_nudges.append(client_nudge)
    return client_nudges

@router.put("/{client_id}", response_model=Client)
async def update_client_details(
    client_id: UUID, 
    client_data: ClientUpdate, 
    current_user: User = Depends(get_current_user_from_token)
):
    """
    MODIFIED: Updates a client's details and, if notes or preferences were changed,
    triggers the relationship planner and PUBLISHES a notification to Redis.
    """
    logging.info(f"API: Received PUT request for client {client_id} with payload: {client_data.model_dump(exclude_unset=True)}")

    updated_client, notes_were_updated = await crm_service.update_client(
        client_id=client_id, 
        update_data=client_data, 
        user_id=current_user.id
    )
    if not updated_client:
        raise HTTPException(status_code=404, detail="Client not found.")

    # If notes or preferences were updated, regenerate the relationship plan.
    if notes_were_updated:
        try:
            from agent_core.brain import relationship_planner
            logging.info(f"API: Notes updated, automatically triggering relationship planner for client {client_id}")
            await relationship_planner.plan_relationship_campaign(client=updated_client, user=current_user)

            # --- THIS IS THE FINAL FIX ---
            # Instead of calling the old websocket manager, we publish to Redis.
            # This ensures any process can notify the frontend.
            notification_payload = {
                "user_id": str(current_user.id),
                "payload": {
                    "event": "PLAN_UPDATED", 
                    "clientId": str(client_id)
                }
            }
            redis_client.publish(USER_NOTIFICATION_CHANNEL, json.dumps(notification_payload))
            logging.info(f"API: Published PLAN_UPDATED event for client {client_id} to user {current_user.id}")

        except Exception as e:
            logging.error(f"API: Failed to trigger relationship planner or publish for client {client_id}: {e}", exc_info=True)

    return updated_client

@router.delete("/{client_id}")
async def delete_client(
    client_id: UUID,
    current_user: User = Depends(get_current_user_from_token)
):
    """
    Deletes a client and all associated data.
    """
    logging.info(f"API: Received DELETE request for client {client_id} from user {current_user.id}")
    
    success = await crm_service.delete_client(
        client_id=client_id,
        user_id=current_user.id
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Client not found")
    
    logging.info(f"API: Successfully deleted client {client_id} for user {current_user.id}")
    return {"message": "Client deleted successfully"}

# --- TEMPORARY ENDPOINT TO FIX PHONE NUMBER FORMATTING ---
@router.post("/fix-phone-formatting", response_model=List[Client])
async def fix_phone_number_formatting(
    current_user: User = Depends(get_current_user_from_token)
):
    """
    Temporary endpoint to fix phone number formatting for existing clients.
    This adds +1 prefix to US phone numbers that don't have it.
    """
    from data.crm import format_phone_number
    
    clients = crm_service.get_all_clients(user_id=current_user.id)
    updated_clients = []
    
    for client in clients:
        if client.phone and not client.phone.startswith('+'):
            # Format the phone number
            formatted_phone = format_phone_number(client.phone)
            if formatted_phone != client.phone:
                # Update the client with the formatted phone number
                update_data = ClientUpdate(phone=formatted_phone)
                updated_client, _ = await crm_service.update_client(
                    client_id=client.id,
                    update_data=update_data,
                    user_id=current_user.id
                )
                if updated_client:
                    updated_clients.append(updated_client)
                    logging.info(f"API: Fixed phone number for client {client.id}: {client.phone} -> {formatted_phone}")
    
    return updated_clients

@router.delete("/{client_id}/scheduled-messages", status_code=status.HTTP_204_NO_CONTENT)
async def delete_client_scheduled_messages(client_id: UUID, current_user: User = Depends(get_current_user_from_token)):
    print(f"API: Received request to delete all scheduled messages for client {client_id}")
    crm_service.delete_scheduled_messages_for_client(client_id=client_id, user_id=current_user.id)
    return None

#endpoint to fetch the timeline data.
class TimelineEvent(BaseModel):
    type: str  # e.g., 'message_inbound', 'message_outbound', 'nudge_sent'
    date: datetime
    description: str
    
@router.get("/{client_id}/timeline", response_model=List[TimelineEvent])
async def get_client_timeline(
    client_id: UUID,
    current_user: User = Depends(get_current_user_from_token)
):
    """
    Retrieves a brief, consolidated history of recent interactions for a client.
    """
    if not client_id:
        raise HTTPException(status_code=400, detail="Client ID is required.")
        
    timeline_events = crm_service.get_relationship_timeline_for_client(
        client_id=client_id,
        user_id=current_user.id
    )
    
    if timeline_events is None:
        raise HTTPException(status_code=404, detail="Client not found or error fetching timeline.")
        
    return timeline_events

# --- NEW: Pydantic model for Interactive Search results ---
class InteractiveSearchResponse(BaseModel):
    event_id: UUID
    headline: str
    resource: NudgeResource # Re-use the existing resource model
    score: int
    reasons: List[str]

# --- NEW: Endpoint for Interactive Search ---
@router.get("/{client_id}/search-matches", response_model=List[InteractiveSearchResponse])
async def interactive_search_for_client(
    client_id: UUID,
    current_user: User = Depends(get_current_user_from_token),
    page: int = 1,
    page_size: int = 20,
):
    """
    Performs a fast, paginated, on-demand search for a single client
    against recent events. This powers the "Search for Matches" button.
    """
    from agent_core.brain.nudge_engine import score_event_against_client, MATCH_THRESHOLD
    from data.database import engine
    from agent_core.brain.verticals import VERTICAL_CONFIGS
    
    with Session(engine) as session:
        client = crm_service.get_client_by_id(client_id, current_user.id, session)
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")

        vertical_config = VERTICAL_CONFIGS.get(current_user.vertical, {})
        if not vertical_config:
            return []

        events_to_search = crm_service.get_active_events_in_batches(
            session=session, lookback_days=90, batch_size=page_size, page=page
        )
        
        matches = []
        for event in events_to_search:
            resource = crm_service.get_resource_by_entity_id(event.entity_id, session)
            if not resource:
                continue
            
            score, reasons = await score_event_against_client(client, event, resource, vertical_config, session)

            if score >= MATCH_THRESHOLD:
                # --- THIS IS THE FIX ---
                # Properly create the NudgeResource object before appending.
                nudge_resource = NudgeResource(
                    address=resource.attributes.get("UnparsedAddress"),
                    price=resource.attributes.get("ListPrice"),
                    beds=resource.attributes.get("BedroomsTotal"),
                    baths=resource.attributes.get("BathroomsTotalInteger"),
                    attributes=resource.attributes
                )
                matches.append(
                    InteractiveSearchResponse(
                        event_id=event.id,
                        headline=resource.attributes.get("UnparsedAddress", "New Opportunity"),
                        resource=nudge_resource,
                        score=score,
                        reasons=reasons
                    )
                )
        return matches