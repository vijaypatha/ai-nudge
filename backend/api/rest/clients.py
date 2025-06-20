# ---
# File Path: backend/api/rest/clients.py
# Purpose: Defines the API endpoints for managing client data (CRUD operations).
# ---

from fastapi import APIRouter, HTTPException, status
from typing import List
from uuid import UUID

# Import the Pydantic models for data validation
from backend.data.models.client import Client, ClientCreate
# Import the centralized CRM data service, which now handles all data storage and retrieval.
from backend.data import crm as crm_service

# Initialize an API router. All routes here will be prefixed with /clients.
router = APIRouter(
    prefix="/clients",
    tags=["Clients"]
)

# Note: The mock data initialization and storage has been moved to backend/data/crm.py
# to centralize data management. This API file now correctly uses the crm_service
# to access that data.

# CORRECTED: The path is now "" to represent the root of the prefix, making it consistent.
@router.post("", response_model=Client, status_code=status.HTTP_201_CREATED)
async def create_client(client_data: ClientCreate):
    """
    Creates a new client. The logic is delegated to the centralized CRM service.
    An empty path "" corresponds to the router's prefix, so this route is POST /clients.
    """
    new_client = Client(**client_data.model_dump())
    # The logic is delegated to the centralized CRM service.
    crm_service.add_client_mock(new_client)
    return new_client

# CORRECTED: The path is now "" to represent the root of the prefix, making it consistent.
@router.get("", response_model=List[Client])
async def get_all_clients():
    """
    Retrieves a list of all clients from the CRM service.
    An empty path "" corresponds to the router's prefix, so this route is GET /clients.
    """
    # The data is retrieved from the centralized CRM service.
    # CORRECTED: The function name is now pluralized to match the likely CRM service method.
    return crm_service.get_all_clients_mock()


@router.get("/{client_id}", response_model=Client)
async def get_client_by_id(client_id: UUID):
    """Retrieves a single client by their unique ID from the CRM service."""
    client = crm_service.get_client_by_id_mock(client_id)
    if client:
        return client
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")