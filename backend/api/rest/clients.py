# File Path: backend/api/rest/clients.py
from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel

from data.models.user import User
from api.security import get_current_user_from_token

from data.models.client import Client, ClientCreate, ClientUpdate, ClientTagUpdate
from data.models.message import ScheduledMessage
from data import crm as crm_service
from agent_core import audience_builder

router = APIRouter(prefix="/clients", tags=["Clients"])

class ClientSearchQuery(BaseModel):
    natural_language_query: Optional[str] = None
    tags: Optional[List[str]] = None

# --- DEFINITIVE FIX: ADDED MANUAL CLIENT ENDPOINT ---
# This was the missing piece. This endpoint now exists to handle the POST
# request from your manual entry form.
@router.post("/manual", response_model=Client)
async def add_manual_client(
    client_data: ClientCreate,
    current_user: User = Depends(get_current_user_from_token)
):
    """
    Creates a single new client or updates an existing one based on deduplication.
    """
    client, _ = crm_service.create_or_update_client(
        user_id=current_user.id, 
        client_data=client_data
    )
    return client
# --- END OF FIX ---


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
async def update_client_details(client_id: UUID, client_data: ClientUpdate, current_user: User = Depends(get_current_user_from_token)):
    updated_client = crm_service.update_client_preferences(client_id=client_id, preferences=client_data.preferences, user_id=current_user.id)
    if not updated_client:
        raise HTTPException(status_code=404, detail="Client not found.")
    return updated_client

@router.delete("/{client_id}/scheduled-messages", status_code=status.HTTP_204_NO_CONTENT)
async def delete_client_scheduled_messages(client_id: UUID, current_user: User = Depends(get_current_user_from_token)):
    print(f"API: Received request to delete all scheduled messages for client {client_id}")
    crm_service.delete_scheduled_messages_for_client(client_id=client_id, user_id=current_user.id)
    return None