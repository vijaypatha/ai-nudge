# File Path: backend/data/crm.py
# Purpose: Acts as a centralized in-memory mock database service. This version includes a specific function to clear only demo data, leaving real user data untouched.

from typing import Optional, List, Dict, Tuple, Any
import uuid

# Import all data models
from .models.client import Client
from .models.user import User
from .models.property import Property
from .models.campaign import CampaignBriefing 
from .models.message import ScheduledMessage

# --- In-Memory Data Storage ---
mock_users_db: List[User] = []
mock_clients_db: List[Client] = []
mock_properties_db: List[Property] = []
mock_client_property_links: List[Tuple[uuid.UUID, uuid.UUID]] = []
mock_campaigns_db: List[CampaignBriefing] = [] 
mock_scheduled_messages_db: List[ScheduledMessage] = []

# --- Data Management Functions ---

def clear_all_data():
    """
    (Helper Function) Clears all mock data lists. Called by the seeder on startup to ensure a clean slate.
    """
    mock_users_db.clear()
    mock_clients_db.clear()
    mock_properties_db.clear()
    mock_client_property_links.clear()
    mock_campaigns_db.clear()
    mock_scheduled_messages_db.clear()

def clear_demo_data_if_present():
    """
    (Core Cleanup Logic) Finds clients marked as demo data, records their IDs, and then removes them and their associated scheduled messages. This is the trigger for the "first-action-clears-data" strategy.
    """
    # Find all clients with the demo flag
    demo_client_ids = [
        client.id for client in mock_clients_db
        if client.preferences.get("source") == "demo"
    ]

    # If no demo clients are found, exit immediately
    if not demo_client_ids:
        return

    print(f"CRM_CLEANUP: Found {len(demo_client_ids)} demo clients to remove.")

    # Filter out demo clients from the main list
    globals()['mock_clients_db'] = [
        client for client in mock_clients_db if client.id not in demo_client_ids
    ]

    # Filter out scheduled messages linked to those demo clients
    globals()['mock_scheduled_messages_db'] = [
        msg for msg in mock_scheduled_messages_db if msg.client_id not in demo_client_ids
    ]
    print("CRM_CLEANUP: Demo data cleared successfully.")


def save_user(user: User):
    """Saves a user to the mock database."""
    mock_users_db.append(user)

def get_user_by_id(user_id: uuid.UUID) -> Optional[User]:
    """Retrieves a user by their ID."""
    for user in mock_users_db:
        if user.id == user_id: return user
    return None

def save_client(client: Client):
    """Saves a client to the mock database."""
    mock_clients_db.append(client)

def get_client_by_id_mock(client_id: uuid.UUID) -> Optional[Client]:
    """Retrieves a client by their ID."""
    for client in mock_clients_db:
        if client.id == client_id: return client
    return None

def get_all_clients_mock() -> List[Client]:
    """Retrieves all clients."""
    return mock_clients_db

def add_client_mock(client: Client):
    """Adds a client to the mock database."""
    save_client(client)

def update_client_preferences(client_id: uuid.UUID, preferences: Dict[str, Any]) -> Optional[Client]:
    """Finds a client and updates their preferences dictionary."""
    client = get_client_by_id_mock(client_id)
    if client:
        client.preferences = preferences
        print(f"CRM: Updated preferences for client -> {client.full_name}")
        return client
    return None

def save_property(property_item: Property):
    """Saves a property record to the mock database."""
    mock_properties_db.append(property_item)

def get_property_by_id(property_id: uuid.UUID) -> Optional[Property]:
    """Retrieves a property by its ID."""
    for prop in mock_properties_db:
        if prop.id == property_id:
            return prop
    return None

def get_all_properties_mock() -> List[Property]:
    """Retrieves all properties."""
    return mock_properties_db

def link_client_to_property(client_id: uuid.UUID, property_id: uuid.UUID):
    """Links a client and property."""
    link = (client_id, property_id)
    if link not in mock_client_property_links:
        mock_client_property_links.append(link)

def get_clients_linked_to_property(property_id: uuid.UUID) -> List[uuid.UUID]:
    """Retrieves clients linked to a property."""
    return [client_id for client_id, prop_id in mock_client_property_links if prop_id == property_id]

def save_campaign_briefing(briefing: CampaignBriefing):
    """Saves a newly generated campaign briefing to the mock database."""
    mock_campaigns_db.append(briefing)
    print(f"NUDGE ENGINE: Saved new Campaign Briefing -> {briefing.headline}")

def get_new_campaign_briefings_for_user(user_id: uuid.UUID) -> List[CampaignBriefing]:
    """Retrieves all 'new' campaign briefings for a specific user."""
    return [briefing for briefing in mock_campaigns_db if briefing.user_id == user_id and briefing.status == "new"]

def get_campaign_briefing_by_id(campaign_id: uuid.UUID) -> Optional[CampaignBriefing]:
    """Retrieves a single campaign briefing by its unique ID."""
    for briefing in mock_campaigns_db:
        if briefing.id == campaign_id:
            return briefing
    return None
    
def update_property_price(property_id: uuid.UUID, new_price: float) -> Optional[Property]:
    """Finds a property, updates its price, and returns the updated object."""
    prop = get_property_by_id(property_id)
    if prop:
        prop.price = new_price
        return prop
    return None

def save_scheduled_message(message: ScheduledMessage):
    """Saves a new scheduled message to the mock database."""
    mock_scheduled_messages_db.append(message)
    print(f"CRM: Saved scheduled message task '{message.content[:20]}...' for client {message.client_id} on {message.scheduled_at.strftime('%Y-%m-%d')}")

def get_scheduled_messages_for_client(client_id: uuid.UUID) -> List[ScheduledMessage]:
    """Retrieves all scheduled messages for a specific client."""
    return [msg for msg in mock_scheduled_messages_db if msg.client_id == client_id]

def update_scheduled_message(message_id: uuid.UUID, update_data: dict) -> Optional[ScheduledMessage]:
    """Finds and updates a specific scheduled message."""
    for msg in mock_scheduled_messages_db:
        if msg.id == message_id:
            msg.content = update_data.get("content", msg.content)
            msg.scheduled_at = update_data.get("scheduled_at", msg.scheduled_at)
            print(f"CRM: Updated scheduled message task -> {msg.id}")
            return msg
    return None

def delete_scheduled_messages_for_client(client_id: uuid.UUID):
    """Deletes all scheduled messages for a client before re-planning."""
    initial_count = len(mock_scheduled_messages_db)
    # Create a new list excluding messages for the specified client
    globals()['mock_scheduled_messages_db'] = [
        msg for msg in mock_scheduled_messages_db if msg.client_id != client_id
    ]
    deleted_count = initial_count - len(mock_scheduled_messages_db)
    print(f"CRM: Deleted {deleted_count} scheduled messages for client {client_id}")