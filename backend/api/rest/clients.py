# File Path: backend/api/rest/clients.py
# Purpose: Defines API endpoints for managing clients. This version implements the "first-action-clears-data" logic by calling the CRM cleanup service before creating new clients.

from fastapi import APIRouter, HTTPException, status, File, UploadFile, BackgroundTasks
from typing import List, Dict, Any
from uuid import UUID
import csv
import io

from data.models.client import Client, ClientCreate, ClientUpdate
from data.models.message import ScheduledMessage
from data import crm as crm_service
from agent_core.brain import relationship_planner


router = APIRouter(
    prefix="/clients",
    tags=["Clients"]
)

async def _process_csv_data(csv_data: str):
    """
    (Helper Function) Parses CSV data and creates clients in the background. It now triggers the demo data cleanup.
    """
    # Clear any existing demo data before importing the user's real data.
    crm_service.clear_demo_data_if_present()

    realtor = crm_service.mock_users_db[0]
    csv_file = io.StringIO(csv_data)
    reader = csv.DictReader(csv_file)

    for row in reader:
        # Assumes CSV has columns 'full_name', 'email', 'phone', 'tags', 'intel'
        client_intel = row.get("intel", "")
        # Simple parsing for unstructured intel: split by semicolon
        notes = [note.strip() for note in client_intel.split(';') if note.strip()]

        new_client_data = ClientCreate(
            full_name=row.get("full_name", ""),
            email=row.get("email", ""),
            phone=row.get("phone"),
            tags=[tag.strip() for tag in row.get("tags", "").split(',')],
            preferences={"notes": notes}
        )
        # Create the full Client model before saving
        client_to_save = Client(**new_client_data.model_dump())
        crm_service.save_client(client_to_save)
        print(f"CSV_IMPORT: Saved client -> {client_to_save.full_name}")
        
        await relationship_planner.plan_relationship_campaign(client_to_save, realtor)


@router.post("/import-csv", status_code=status.HTTP_202_ACCEPTED)
async def import_clients_from_csv(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """
    (API Endpoint) Accepts a CSV file and processes it in the background. This is a primary trigger for clearing demo data.
    """
    if file.content_type != 'text/csv':
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a CSV.")

    csv_content = await file.read()

    # Run the CSV processing in the background to avoid long request times
    background_tasks.add_task(_process_csv_data, csv_content.decode('utf-8'))

    return {"message": "Client import process started. Clients will be available shortly."}


@router.post("", response_model=Client, status_code=status.HTTP_201_CREATED)
async def create_client(client_data: ClientCreate):
    """
    (API Endpoint) Creates a single new client. This is a primary trigger for clearing demo data.
    """
    # Clear any existing demo data before creating the user's first real client.
    crm_service.clear_demo_data_if_present()

    new_client = Client(**client_data.model_dump())
    crm_service.save_client(new_client)

    # Trigger the relationship planner for the new client.
    if crm_service.mock_users_db:
        realtor = crm_service.mock_users_db[0]
        await relationship_planner.plan_relationship_campaign(new_client, realtor)

    return new_client

@router.get("", response_model=List[Client])
async def get_all_clients():
    """(API Endpoint) Retrieves a list of all clients."""
    return crm_service.get_all_clients_mock()

@router.get("/{client_id}", response_model=Client)
async def get_client_by_id(client_id: UUID):
    """(API Endpoint) Retrieves a single client by their unique ID."""
    client = crm_service.get_client_by_id_mock(client_id)
    if client:
        return client
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

@router.get("/{client_id}/scheduled-messages", response_model=List[ScheduledMessage])
async def get_client_scheduled_messages(client_id: UUID):
    """
    (API Endpoint) Retrieves all future scheduled messages for a specific client.
    """
    client = crm_service.get_client_by_id_mock(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    messages = crm_service.get_scheduled_messages_for_client(client_id)
    return messages

@router.put("/{client_id}", response_model=Client)
async def update_client_details(client_id: UUID, client_data: ClientUpdate):
    """(API Endpoint) Updates a client's preferences (intel)."""
    updated_client = crm_service.update_client_preferences(
        client_id=client_id,
        preferences=client_data.preferences
    )
    if not updated_client:
        raise HTTPException(status_code=404, detail="Client not found.")
    return updated_client

@router.post("/{client_id}/plan-campaign", status_code=status.HTTP_202_ACCEPTED)
async def plan_client_campaign(client_id: UUID):
    """
    (API Endpoint) Triggers the Relationship Planner for a specific client.
    """
    client = crm_service.get_client_by_id_mock(client_id)
    realtor = crm_service.mock_users_db[0] if crm_service.mock_users_db else None

    if not client or not realtor:
        raise HTTPException(status_code=404, detail="Client or Realtor not found.")

    crm_service.delete_scheduled_messages_for_client(client_id)
    await relationship_planner.plan_relationship_campaign(client, realtor)
    return {"message": f"New relationship campaign has been planned for {client.full_name}."}