# ---
# File Path: backend/data/crm.py
# Purpose: Centralized in-memory mock database service.
# ---

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
    """Clears all mock data, called by the seed script on startup."""
    mock_users_db.clear()
    mock_clients_db.clear()
    mock_properties_db.clear()
    mock_client_property_links.clear()
    mock_campaigns_db.clear()
    mock_scheduled_messages_db.clear()

# ... (User, Client, Property, and Linking functions remain the same) ...
def save_user(user: User):
    mock_users_db.append(user)
def get_user_by_id(user_id: uuid.UUID) -> Optional[User]:
    for user in mock_users_db:
        if user.id == user_id: return user
    return None

## Client Functions 
def save_client(client: Client):
    mock_clients_db.append(client)

def get_client_by_id_mock(client_id: uuid.UUID) -> Optional[Client]:
    for client in mock_clients_db:
        if client.id == client_id: return client
    return None

def get_all_clients_mock() -> List[Client]:
    return mock_clients_db

def add_client_mock(client: Client):
    save_client(client)

def update_client_preferences(client_id: uuid.UUID, preferences: Dict[str, Any]) -> Optional[Client]:
    """Finds a client and updates their preferences dictionary."""
    client = get_client_by_id_mock(client_id)
    if client:
        client.preferences = preferences
        print(f"CRM: Updated preferences for client -> {client.full_name}")
        return client
    return None

## Properity Functions
def save_property(property_item: Property):
    mock_properties_db.append(property_item)
def get_property_by_id(property_id: uuid.UUID) -> Optional[Property]:
    for prop in mock_properties_db:
        if prop.id == property_id:
            return prop
    return None
def get_all_properties_mock() -> List[Property]:
    return mock_properties_db
def link_client_to_property(client_id: uuid.UUID, property_id: uuid.UUID):
    link = (client_id, property_id)
    if link not in mock_client_property_links:
        mock_client_property_links.append(link)
def get_clients_linked_to_property(property_id: uuid.UUID) -> List[uuid.UUID]:
    return [client_id for client_id, prop_id in mock_client_property_links if prop_id == property_id]

# --- Campaign Briefing Functions ---
def save_campaign_briefing(briefing: CampaignBriefing):
    """Saves a newly generated campaign briefing to the mock database."""
    mock_campaigns_db.append(briefing)
    print(f"NUDGE ENGINE: Saved new Campaign Briefing -> {briefing.headline}")

def get_new_campaign_briefings_for_user(user_id: uuid.UUID) -> List[CampaignBriefing]:
    """Retrieves all 'new' campaign briefings for a specific user."""
    return [briefing for briefing in mock_campaigns_db if briefing.user_id == user_id and briefing.status == "new"]

# --- Property Functions ---
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
    
# NEW: A dedicated function to handle updating a property's price.
def update_property_price(property_id: uuid.UUID, new_price: float) -> Optional[Property]:
    """Finds a property, updates its price, and returns the updated object."""
    prop = get_property_by_id(property_id)
    if prop:
        prop.price = new_price
        return prop
    return None

# --- Scheduled Message & Campaign Functions ---
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