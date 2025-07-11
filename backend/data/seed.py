# ---
# File Path: backend/data/seed.py
# Purpose: Seeds the database with initial data for development and testing.
# ---
# MODIFIED: Now creates a wide variety of nudges on startup to populate the UI.
# ---

import uuid
import asyncio
from datetime import datetime, timezone, timedelta
from sqlmodel import Session

from .database import engine
from .models.client import Client
from .models.message import Message, ScheduledMessage
from .models.property import Property
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

def clear_demo_data():
    """Deletes all data from tables in the correct order to respect foreign keys."""
    print("SEEDER: Clearing all existing demo data...")
    with Session(engine) as session:
        # Correct order to avoid foreign key violations
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
        # Step 1: Create base data
        realtor_user = User(
            id=USER_ID_JANE,
            user_type=UserType.REALTOR,
            full_name="Jane Doe",
            email="jane.doe@realty.com",
            phone_number="+15558675309",
            twilio_phone_number="+14352721987",
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
            Client(id=CLIENT_ID_ALEX, user_id=USER_ID_JANE, full_name="Alex Chen (Demo)", email="alex.chen@example.com", phone="+14155551234", user_tags=["investor"], ai_tags=["past_client"], last_interaction=(datetime.now(timezone.utc) - timedelta(days=10)).isoformat(), preferences={"notes": ["Prefers properties with high ROI."], "source": "demo", "locations": ["Sunnyvale"], "budget_max": 2000000, "min_bedrooms": 3}),
            Client(id=CLIENT_ID_SAM, user_id=USER_ID_JANE, full_name="Samantha Miller (Demo)", email="samantha.miller@example.com", phone="+16505555678", user_tags=["first_time_buyer"], ai_tags=[], last_interaction=(datetime.now(timezone.utc) - timedelta(days=45)).isoformat(), preferences={"notes": ["Really wants a large yard for her dog. Loves Yoga", "birthday October 30"], "source": "demo", "min_bedrooms": 3}),
            Client(id=CLIENT_ID_BEN, user_id=USER_ID_JANE, full_name="Ben Carter (Demo)", email="ben.carter@example.com", phone="+13856268825", user_tags=[], ai_tags=[], last_interaction=None, preferences={"notes": ["Wants to buy in the next 12 months."], "source": "demo"})
        ]

        session.add(realtor_user)
        session.add(prop_maple)
        session.add_all(clients_data)
        
        session.commit()
        print("SEEDER: Base data for users, clients, and properties committed.")

        session.refresh(realtor_user)
        session.refresh(prop_maple)

        # --- MODIFIED: Create a variety of market events to generate nudges ---
        print("SEEDER: Simulating multiple market events to generate a rich set of nudges...")
        
        market_area_city = prop_maple.address.split(',')[1].strip()
        
        # A list of event types to simulate
        event_types_to_simulate = [
            "price_drop", "new_listing", "sold_listing", "back_on_market",
            "expired_listing", "coming_soon", "withdrawn_listing"
        ]
        
        event_creation_tasks = []

        for event_type in event_types_to_simulate:
            # Create a unique event for each type
            event = MarketEvent(
                id=uuid.uuid4(),
                event_type=event_type,
                market_area=market_area_city,
                entity_type="PROPERTY",
                entity_id=PROP_ID_MAPLE,
                payload={"old_price": 1250000.0, "new_price": 1100000.0} if event_type == "price_drop" else {}
            )
            session.add(event)
            session.commit() # Commit each event so it has an ID before processing
            
            # Add the processing of this event to our list of tasks
            event_creation_tasks.append(
                nudge_engine.process_market_event(event=event, realtor=realtor_user)
            )
            
        # Also generate the relationship-based "recency" nudge
        event_creation_tasks.append(
            nudge_engine.generate_recency_nudges(realtor=realtor_user)
        )

        # Run all nudge generation tasks concurrently
        await asyncio.gather(*event_creation_tasks)
        
        session.commit()
        print("SEEDER: Seeding complete.")