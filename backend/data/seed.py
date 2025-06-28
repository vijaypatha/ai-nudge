# File Path: backend/data/seed.py
# Purpose: This script seeds the database on startup with a complete set of mock data including a user, a property, multiple clients, and scheduled messages to ensure all features are testable.

import uuid
from datetime import datetime, timezone, timedelta
from . import crm as crm_service
from .models.campaign import CampaignBriefing
from .models.client import Client
from .models.event import MarketEvent
from .models.message import ScheduledMessage
from .models.property import Property
from .models.user import User

def seed_database():
    """
    (Core Seeder) Wipes and populates the in-memory database with a complete set of demo data.
    """
    print("SEEDER: Preparing to seed the database...")
    crm_service.clear_all_data()
    print("SEEDER: All mock data cleared.")

    # --- 1. Create and Save the Default User ---
    realtor_user = User(
        id=uuid.uuid4(),
        full_name="Jane Doe",
        email="jane.doe@realty.com",
        market_focus=["Sunnyvale", "Mountain View"],
        strategy={"nudge_format": "ready-to-send"}
    )
    crm_service.save_user(realtor_user)
    print(f"SEEDER: Staged User -> {realtor_user.full_name}")

    # --- 2. Create and Save the Demo Property ---
    now_iso = datetime.now(timezone.utc).isoformat()
    prop_maple = Property(
        id=uuid.uuid4(),
        address="123 Maple St, Sunnyvale, CA",
        price=1250000.0,
        property_type="Single Family",
        bedrooms=4,
        bathrooms=3,
        square_footage=2200,
        listing_url="https://example.com/listing/123-maple-st",
        image_urls=[],
        last_updated=now_iso,
        status="active"
    )
    crm_service.save_property(prop_maple)
    print(f"SEEDER: Staged Property -> {prop_maple.address}")

    # --- 3. Create and Save Demo Clients ---
    client1 = Client(
        id=uuid.uuid4(),
        full_name="Alex Chen (Demo)",
        email="alex.chen@example.com",
        phone="+14155551234",
        tags=["Investor", "Past Client"],
        preferences={
            "notes": ["Prefers properties with high ROI."], 
            "source": "demo",
            #"locations": ["Sunnyvale"],
            #"budget_max": 2000000,
            "min_bedrooms": 3
        }
    )
    client2 = Client(
        id=uuid.uuid4(),
        full_name="Samantha Miller (Demo)",
        email="samantha.miller@example.com",
        phone="+16505555678",
        tags=["First-Time Buyer"],
        preferences={
            "notes": ["Prefers properties with high ROI."], 
            "source": "demo",
            #"locations": ["Sunnyvale"],
            #"budget_max": 2000000,
            "min_bedrooms": 3
        }
    )
    client3 = Client(
        id=uuid.uuid4(),
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

    # --- 4. Create and Save Demo Scheduled Messages ---
    now = datetime.now(timezone.utc)
    bday_message = ScheduledMessage(
        id=uuid.uuid4(),
        client_id=client2.id,
        content="Happy Birthday, Samantha! Hope you have a wonderful day.",
        scheduled_at=now + timedelta(days=30)
    )
    checkin_message = ScheduledMessage(
        id=uuid.uuid4(),
        client_id=client2.id,
        content="Hi Samantha, just checking in to see how the home search is going. Let me know if you'd like to see some new listings!",
        scheduled_at=now + timedelta(days=90)
    )
    crm_service.save_scheduled_message(bday_message)
    crm_service.save_scheduled_message(checkin_message)
    print(f"SEEDER: Staged 2 scheduled messages for client -> {client2.full_name}")

    print("SEEDER: Seeding complete.")