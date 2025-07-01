# ---
# File Path: backend/data/seed.py
# Purpose: Seeds the database with initial data for development and testing.
# --- CORRECTED to prevent foreign key constraint violations on startup ---

import uuid
from datetime import datetime, timezone
from sqlmodel import Session

from .database import engine
# --- FIX: Import all necessary models for clearing data ---
from .models.client import Client
from .models.message import Message, ScheduledMessage
from .models.property import Property
from .models.user import User
from .models.event import MarketEvent
from .models.campaign import CampaignBriefing

from agent_core.brain import nudge_engine

# --- Deterministic UUIDs (Preserved from your original file) ---
USER_ID_JANE = uuid.UUID("a8c6f1d7-8f7a-4b6e-8b0f-9e5a7d6c5b4a")
PROP_ID_MAPLE = uuid.UUID("b9f8e1a2-7d6c-4b3a-9e8f-1a2b3c4d5e6f")
CLIENT_ID_ALEX = uuid.UUID("c1e2d3f4-5b6a-7c8d-9e0f-1a2b3c4d5e6f")
CLIENT_ID_SAM = uuid.UUID("d2f3e4a5-6b7a-8c9d-0e1f-2a3b4c5d6e7f")
CLIENT_ID_BEN = uuid.UUID("e3f4a5b6-7a8b-9c0d-1e2f-3a4b5c6d7e8f")
EVENT_ID_PRICE_DROP = uuid.UUID("9e5a7d6c-5b4a-4b6e-8b0f-a8c6f1d78f7a")

def clear_demo_data():
    """
    Deletes all data from the tables in the correct order to respect foreign key constraints.
    """
    print("SEEDER: Clearing all existing demo data...")
    with Session(engine) as session:
        # --- FIX: Delete from child tables BEFORE parent tables ---
        session.query(Message).delete()
        session.query(ScheduledMessage).delete()
        session.query(CampaignBriefing).delete()
        session.query(MarketEvent).delete()
        
        # Now it's safe to delete the parent records
        session.query(Client).delete()
        session.query(Property).delete()
        session.query(User).delete()
        
        session.commit()
    print("SEEDER: Demo data cleared successfully.")

async def seed_database():
    """
    Populates the database by creating base records and then simulating a
    market event to trigger the AI nudge generation process.
    """
    print("SEEDER: Preparing to seed the database...")
    clear_demo_data()

    with Session(engine) as session:
        # --- Step 1: Create all data objects (Preserved from your original file) ---
        realtor_user = User(
            id=USER_ID_JANE,
            full_name="Jane Doe",
            email="jane.doe@realty.com",
            phone_number="+15558675309",
            market_focus=["Sunnyvale", "Mountain View"]
        )

        # The 'last_updated' field is now correctly handled by the model's default_factory
        # or should be explicitly set if the model requires it without a default.
        prop_maple = Property(
            id=PROP_ID_MAPLE,
            address="123 Maple St, Sunnyvale, CA",
            price=1100000.0,
            property_type="Single Family",
            bedrooms=4,
            bathrooms=3,
            square_footage=2200,
            last_updated=datetime.now(timezone.utc).isoformat()
        )

        clients_data = [
            Client(id=CLIENT_ID_ALEX, full_name="Alex Chen (Demo)", email="alex.chen@example.com", phone="+14155551234", tags=["Investor", "Past Client"], preferences={"notes": ["Prefers properties with high ROI."], "source": "demo", "locations": ["Sunnyvale"], "budget_max": 2000000, "min_bedrooms": 3}),
            Client(id=CLIENT_ID_SAM, full_name="Samantha Miller (Demo)", email="samantha.miller@example.com", phone="+16505555678", tags=["First-Time Buyer"], preferences={"notes": ["Really wants a large yard for her dog. Loves Yoga"], "source": "demo", "min_bedrooms": 3}),
            Client(id=CLIENT_ID_BEN, full_name="Ben Carter (Demo)", email="ben.carter@example.com", phone=None, tags=["Renter", "Future Buyer"], preferences={"notes": ["Wants to buy in the next 12 months."], "source": "demo"})
        ]

        session.add(realtor_user)
        session.add(prop_maple)
        session.add_all(clients_data)
        
        session.commit()
        print("SEEDER: Base data for users, clients, and properties committed.")

        session.refresh(realtor_user)
        session.refresh(prop_maple)

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
        await nudge_engine.process_market_event(event=price_drop_event, realtor=realtor_user)
        
        session.commit()
        print("SEEDER: Seeding complete.")
