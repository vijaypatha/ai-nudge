# File Path: backend/api/rest/clients.py
# --- DEFINITIVE FIX: The /intel endpoint no longer clears the recommendation slate, allowing multiple actions.

import logging
from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel
from sqlmodel import Session

from data.models.user import User, UserUpdate
from api.security import get_current_user_from_token

from data.models.client import Client, ClientCreate, ClientUpdate, ClientTagUpdate
from data.models.message import ScheduledMessage
from data import crm as crm_service
from agent_core import audience_builder

router = APIRouter(prefix="/clients", tags=["Clients"])

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

@router.post("/manual", response_model=Client)
async def add_manual_client(
    client_data: ClientCreate,
    current_user: User = Depends(get_current_user_from_token)
):
    """
    Creates a single new client and updates the user's onboarding state.
    """
    client, _ = crm_service.create_or_update_client(
        user_id=current_user.id, 
        client_data=client_data
    )
    
    try:
        if not current_user.onboarding_state.get('contacts_imported'):
            logging.info(f"Updating onboarding state for user {current_user.id} after manual contact add.")
            updated_state = current_user.onboarding_state.copy()
            updated_state['contacts_imported'] = True
            
            update_data = UserUpdate(onboarding_state=updated_state)
            crm_service.update_user(user_id=current_user.id, update_data=update_data)
            logging.info(f"Successfully updated onboarding state for user {current_user.id}.")
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
    It can add tags and add notes. The recommendation slate itself is cleared
    separately when the conversation progresses (e.g., a message is sent).
    """
    # --- MODIFICATION START ---
    # This call now only updates the client's data (tags, notes).
    updated_client = crm_service.update_client_intel(
        client_id=client_id,
        user_id=current_user.id,
        tags_to_add=payload.tags_to_add,
        notes_to_add=payload.notes_to_add
    )

    if not updated_client:
        raise HTTPException(status_code=404, detail="Client not found or failed to update.")

    # REMOVED: The logic to mark the slate as 'completed' has been removed.
    # This is the key change to prevent the UI from disappearing prematurely.
    # The slate is now cleared only when a message is sent or received,
    # handled by a different process.
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
    updated_client = crm_service.update_client_notes(
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

    updated_client = crm_service.add_client_tags(
        client_id=client_id, 
        tags_to_add=payload.tags,
        user_id=current_user.id
    )

    if not updated_client:
        raise HTTPException(status_code=500, detail="Failed to update client tags.")

    return updated_client

@router.put("/{client_id}/tags", response_model=Client)
async def update_client_tags_endpoint(client_id: UUID, tag_data: ClientTagUpdate, current_user: User = Depends(get_current_user_from_token)):
    updated_client = crm_service.update_client_tags(client_id, tag_data.user_tags, user_id=current_user.id)
    if not updated_client:
        raise HTTPException(status_code=404, detail="Client not found.")
    return updated_client

@router.get("", response_model=List[Client])
async def get_all_clients_endpoint(current_user: User = Depends(get_current_user_from_token)):
    return crm_service.get_all_clients(user_id=current_user.id)

@router.get("/{client_id}", response_model=Client)
async def get_client_by_id_endpoint(client_id: UUID, current_user: User = Depends(get_current_user_from_token)):
    client = crm_service.get_client_by_id(client_id=client_id, user_id=current_user.id)
    if client:
        return client
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

@router.get("/{client_id}/scheduled-messages", response_model=List[ScheduledMessage])
async def get_client_scheduled_messages(client_id: UUID, current_user: User = Depends(get_current_user_from_token)):
    messages = crm_service.get_scheduled_messages_for_client(client_id=client_id, user_id=current_user.id)
    return messages

@router.put("/{client_id}", response_model=Client)
async def update_client_details(
    client_id: UUID, 
    client_data: ClientUpdate, 
    current_user: User = Depends(get_current_user_from_token)
):
    """
    Updates a client's details, including preferences, notes, or timezone.
    """
    updated_client = crm_service.update_client(
        client_id=client_id, 
        update_data=client_data, 
        user_id=current_user.id
    )
    if not updated_client:
        raise HTTPException(status_code=404, detail="Client not found.")
    return updated_client

@router.delete("/{client_id}/scheduled-messages", status_code=status.HTTP_204_NO_CONTENT)
async def delete_client_scheduled_messages(client_id: UUID, current_user: User = Depends(get_current_user_from_token)):
    print(f"API: Received request to delete all scheduled messages for client {client_id}")
    crm_service.delete_scheduled_messages_for_client(client_id=client_id, user_id=current_user.id)
    return None