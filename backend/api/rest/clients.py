# File Path: backend/api/rest/clients.py
# Purpose: Defines API endpoints for managing clients.
# This version is UPDATED to call the new database-aware crm service functions.

from fastapi import APIRouter, HTTPException, status
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel

from data.models.client import Client, ClientCreate, ClientUpdate, ClientTagUpdate
from data.models.message import ScheduledMessage
from data import crm as crm_service
from agent_core import audience_builder

router = APIRouter(prefix="/clients", tags=["Clients"])

class ClientSearchQuery(BaseModel):
    natural_language_query: Optional[str] = None
    tags: Optional[List[str]] = None

@router.post("/search", response_model=List[Client])
async def search_clients(query: ClientSearchQuery):
    all_clients = crm_service.get_all_clients()
    audience_builder.build_or_rebuild_client_index(all_clients)
    
    matched_ids = set()
    filter_applied = False

    if query.natural_language_query:
        nl_ids = audience_builder.find_clients_by_semantic_query(query.natural_language_query)
        matched_ids.update(nl_ids)
        filter_applied = True

    if query.tags:
        query_tags_lower = {t.lower() for t in query.tags}
        tag_ids = {c.id for c in all_clients if c.tags and any(ct.lower() in query_tags_lower for ct in c.tags)}
        if filter_applied:
            matched_ids.intersection_update(tag_ids)
        else:
            matched_ids.update(tag_ids)
        filter_applied = True
    
    if not filter_applied:
        return all_clients

    return [client for client in all_clients if client.id in matched_ids]

@router.put("/{client_id}/tags", response_model=Client)
async def update_client_tags_endpoint(client_id: UUID, tag_data: ClientTagUpdate):
    updated_client = crm_service.update_client_tags(client_id, tag_data.tags)
    if not updated_client:
        raise HTTPException(status_code=404, detail="Client not found.")
    return updated_client

@router.get("", response_model=List[Client])
async def get_all_clients_endpoint():
    return crm_service.get_all_clients()

@router.get("/{client_id}", response_model=Client)
async def get_client_by_id_endpoint(client_id: UUID):
    client = crm_service.get_client_by_id(client_id)
    if client:
        return client
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

@router.get("/{client_id}/scheduled-messages", response_model=List[ScheduledMessage])
async def get_client_scheduled_messages(client_id: UUID):
    messages = crm_service.get_scheduled_messages_for_client(client_id)
    return messages

@router.put("/{client_id}", response_model=Client)
async def update_client_details(client_id: UUID, client_data: ClientUpdate):
    updated_client = crm_service.update_client_preferences(client_id=client_id, preferences=client_data.preferences)
    if not updated_client:
        raise HTTPException(status_code=404, detail="Client not found.")
    return updated_client