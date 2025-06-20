# backend/data/crm.py

from typing import Optional, List # For type hinting
from backend.data.models.client import Client # Import the Client model
import uuid # For UUIDs
from datetime import datetime, timezone # For timestamps

# This is a mock database for clients.
# In a real application, this module would interact with a proper database.
# It uses the same mock_clients_db that was in api/rest/clients.py, but now centralized here.
# We will move existing mock data from clients.py into this file soon to centralize it.
mock_clients_db: List[Client] = []

# Add some initial mock clients for testing purposes.
mock_clients_db.append(Client(
    full_name="Sarah Smith",
    email="sarah.smith@example.com",
    phone="123-456-7890",
    tags=["hot lead", "buyer", "realtor-focus"],
    last_interaction="2025-06-18"
))
mock_clients_db.append(Client(
    full_name="John Doe",
    email="john.doe@example.com",
    phone="987-654-3210",
    tags=["seller"],
    last_interaction="2025-06-15"
))
mock_clients_db.append(Client( # Add one more for varied testing
    full_name="Alex Johnson",
    email="alex.johnson@example.com",
    phone="555-111-2222",
    tags=["investor"],
    last_interaction="2025-06-10"
))

def get_client_by_id_mock(client_id: uuid.UUID) -> Optional[Client]:
    """
    Simulates fetching a client by ID from the CRM database.
    How it works for the robot: This is like the robot quickly looking up a friend's
    details in its small, temporary friend list.
    """
    for client in mock_clients_db:
        if client.id == client_id:
            return client
    return None

def add_client_mock(client: Client) -> None:
    """
    Simulates adding a client to the CRM database.
    (Used by other parts to populate mock data)
    """
    mock_clients_db.append(client)

def get_all_clients_mock() -> List[Client]:
    """
    Simulates fetching all clients from the CRM database.
    """
    return mock_clients_db