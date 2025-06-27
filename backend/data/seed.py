# File Path: backend/data/seed.py
# Purpose: This script now seeds the database on startup with a mock user and a rich set of demo clients and scheduled messages. This provides an illustrative "Day One" experience for the user.

from datetime import datetime, timezone, timedelta
from sqlmodel import Session, SQLModel
from .database import engine

# Import ALL table models to ensure they are known to SQLModel
from .models.user import User
from .models.property import Property
from .models.client import Client
from .models.message import ScheduledMessage
from .models.campaign import CampaignBriefing
from .models.event import MarketEvent

# Import the crm service to use its data-saving functions
from . import crm as crm_service

def seed_database():
    """
    (Core Seeder) Wipes and populates the in-memory database. Creates a default user and a set of demo clients, each marked with a 'source: demo' preference for later automatic cleanup.
    """
    print("SEEDER: Preparing to seed the database...")
    # Clear all data lists in the crm service to ensure a clean start
    crm_service.clear_all_data()
    print("SEEDER: All mock data cleared.")
    
    # Create the default realtor user
    realtor_user = User(
        full_name="Jane Doe",
        email="jane.doe@realty.com",
        market_focus=["Sunnyvale", "Mountain View"],
        strategy={"nudge_format": "ready-to-send"}
    )
    crm_service.save_user(realtor_user)
    print(f"SEEDER: Staged User -> {realtor_user.full_name}")
    
    # Create three mock clients and mark them as demo data
    client1 = Client(
        full_name="Alex Chen (Demo)",
        email="alex.chen@example.com",
        phone="+14155551234",
        tags=["Investor", "Past Client"],
        preferences={"notes": ["Prefers properties with high ROI.", "Communicates via text."], "source": "demo"}
    )
    client2 = Client(
        full_name="Samantha Miller (Demo)",
        email="samantha.miller@example.com",
        phone="+16505555678",
        tags=["First-Time Buyer"],
        preferences={"notes": ["Looking for a 2-bedroom condo near a park.", "Budget is $800k."], "source": "demo"}
    )
    client3 = Client(
        full_name="Ben Carter (Demo)",
        email="ben.carter@example.com",
        phone=None,
        tags=["Renter", "Future Buyer"],
        preferences={"notes": ["Wants to buy in the next 12 months."], "source": "demo"}
    )
    crm_service.save_client(client1)
    crm_service.save_client(client2)
    crm_service.save_client(client3)
    print("SEEDER: Staged 3 demo clients.")
    
    # Create a mock relationship plan for one of the demo clients
    now = datetime.now(timezone.utc)
    bday_message = ScheduledMessage(
        client_id=client2.id,
        content="Happy Birthday, Samantha! Hope you have a wonderful day.",
        scheduled_at=now + timedelta(days=30)
    )
    checkin_message = ScheduledMessage(
        client_id=client2.id,
        content="Hi Samantha, just checking in to see how the home search is going. Let me know if you'd like to see some new listings!",
        scheduled_at=now + timedelta(days=90)
    )
    crm_service.save_scheduled_message(bday_message)
    crm_service.save_scheduled_message(checkin_message)
    print(f"SEEDER: Staged 2 scheduled messages for client -> {client2.full_name}")
    
    print("SEEDER: Seeding complete.")