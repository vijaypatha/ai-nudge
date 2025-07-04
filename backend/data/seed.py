# ---
# File Path: backend/data/seed.py
# Purpose: Seeds the database with initial data for development and testing.
# ---
# CORRECTED:
# 1. Assigns a `user_type` to the demo user to prevent NotNullViolation.
# 2. Uses the correct `user_tags` and `ai_tags` fields for clients.
# 3. (NEW) Assigns a user_id to each client to satisfy the foreign key constraint.
# ---

import uuid
from datetime import datetime, timezone
from sqlmodel import Session

from .database import engine
from .models.client import Client
from .models.message import Message, ScheduledMessage
from .models.property import Property
# Import UserType along with User
from .models.user import User, UserType
from .models.event import MarketEvent
from .models.campaign import CampaignBriefing

from agent_core.brain import nudge_engine

# Deterministic UUIDs
USER_ID_JANE = uuid.UUID("a8c6f1d7-8f7a-4b6e-8b0f-9e5a7d6c5b4a")
PROP_ID_MAPLE = uuid.UUID("b9f8e1a2-7d6c-4b3a-9e8f-1a2b3c4d5e6f")
CLIENT_ID_ALEX = uuid.UUID("c1e2d3f4-5b6a-7c8d-9e0f-1a2b3c4d5e6f")
CLIENT_ID_SAM = uuid.UUID("d2f3e4a5-6b7a-8c9d-0e1f-2a3b4c5d6e7f")
CLIENT_ID_BEN = uuid.UUID("e3f4a5b6-7a8b-9c0d-1e2f-3a4b5c6d7e8f")
EVENT_ID_PRICE_DROP = uuid.UUID("9e5a7d6c-5b4a-4b6e-8b0f-a8c6f1d78f7a")

def clear_demo_data():
    """Deletes all data from tables in the correct order to respect foreign keys."""
    print("SEEDER: Clearing all existing demo data...")
    with Session(engine) as session:
        session.query(Message).delete()
        session.query(ScheduledMessage).delete()
        session.query(CampaignBriefing).delete()
        session.query(MarketEvent).delete()
        session.query(Client).delete()
        session.query(Property).delete()
        session.query(User).delete()
        session.commit()
    print("SEEDER: Demo data cleared successfully.")

async def seed_database():
    """Populates the database with initial data for development."""
    print("SEEDER: Preparing to seed the database...")
    clear_demo_data()

    with Session(engine) as session:
        # Step 1: Create all data objects
        realtor_user = User(
            id=USER_ID_JANE,
            user_type=UserType.REALTOR,
            full_name="Jane Doe",
            email="jane.doe@realty.com",
            phone_number="+15558675309",
            market_focus=["Sunnyvale", "Mountain View"]
        )

        prop_maple = Property(
            id=PROP_ID_MAPLE,
            address="123 Maple St, Sunnyvale, CA",
            price=1100000.0,
            property_type="Single Family",
            bedrooms=4,
            bathrooms=3,
            square_footage=2200,
        )

        clients_data = [
            # --- MODIFIED: Added user_id to each Client ---
            Client(id=CLIENT_ID_ALEX, user_id=USER_ID_JANE, full_name="Alex Chen (Demo)", email="alex.chen@example.com", phone="+14155551234", user_tags=["investor"], ai_tags=["past_client"], preferences={"notes": ["Prefers properties with high ROI."], "source": "demo", "locations": ["Sunnyvale"], "budget_max": 2000000, "min_bedrooms": 3}),
            Client(id=CLIENT_ID_SAM, user_id=USER_ID_JANE, full_name="Samantha Miller (Demo)", email="samantha.miller@example.com", phone="+16505555678", user_tags=["first_time_buyer"], ai_tags=[], preferences={"notes": ["Really wants a large yard for her dog. Loves Yoga", "birthday October 30"], "source": "demo", "min_bedrooms": 3}),
            Client(id=CLIENT_ID_BEN, user_id=USER_ID_JANE, full_name="Ben Carter (Demo)", email="ben.carter@example.com", phone=None, user_tags=[], ai_tags=[], preferences={"notes": ["Wants to buy in the next 12 months."], "source": "demo"})
        ]

        session.add(realtor_user)
        session.add(prop_maple)
        session.add_all(clients_data)
        
        session.commit()
        print("SEEDER: Base data for users, clients, and properties committed.")

        # Refresh objects to ensure relationships are loaded for the next step
        session.refresh(realtor_user)
        session.refresh(prop_maple)

        # Step 2: Simulate a market event to trigger the Nudge Engine
        print("SEEDER: Simulating 'price_drop' market event to trigger Nudge Engine...")
        market_area_city = prop_maple.address.split(',')[1].strip()
        price_drop_event = MarketEvent(
            id=EVENT_ID_PRICE_DROP,
            event_type="price_drop",
            market_area=market_area_city,
            entity_type="PROPERTY",
            entity_id=PROP_ID_MAPLE,
            payload={"old_price": 1250000.0, "new_price": 1100000.0}
        )
        # Manually add the event to the session so it has a valid ID before being used
        session.add(price_drop_event)
        session.commit()
        
        await nudge_engine.process_market_event(event=price_drop_event, realtor=realtor_user)
        
        session.commit()
        print("SEEDER: Seeding complete.")