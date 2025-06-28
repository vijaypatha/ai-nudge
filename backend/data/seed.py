# File Path: backend/data/seed.py
# Purpose: Seeds the database on startup.
# CORRECTED VERSION: Fixed UniqueViolation by ensuring clean session state

import uuid
from datetime import datetime, timezone, timedelta
from sqlmodel import Session
from .database import engine
from .models.campaign import CampaignBriefing
from .models.client import Client
from .models.message import ScheduledMessage
from .models.property import Property
from .models.user import User

# --- Deterministic UUIDs ---
USER_ID_JANE = uuid.UUID("a8c6f1d7-8f7a-4b6e-8b0f-9e5a7d6c5b4a")
PROP_ID_MAPLE = uuid.UUID("b9f8e1a2-7d6c-4b3a-9e8f-1a2b3c4d5e6f")
CLIENT_ID_ALEX = uuid.UUID("c1e2d3f4-5b6a-7c8d-9e0f-1a2b3c4d5e6f")
CLIENT_ID_SAM = uuid.UUID("d2f3e4a5-6b7a-8c9d-0e1f-2a3b4c5d6e7f")
CLIENT_ID_BEN = uuid.UUID("e3f4a5b6-7a8b-9c0d-1e2f-3a4b5c6d7e8f")
CAMPAIGN_ID_PRICE_DROP = uuid.UUID("f4a5b6c7-8d9e-4f1a-b2c3-4d5e6f7a8b9c")
MSG_ID_BDAY = uuid.UUID("1a2b3c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6d")
MSG_ID_CHECKIN = uuid.UUID("2b3c4d5e-6f7a-8b9c-0d1e-2f3a4b5c6d7e")

def seed_database():
    """
    Populates the database with demo data.
    CORRECTED: Fixed UniqueViolation by using merge() instead of add().
    """
    print("SEEDER: Preparing to seed the database...")
    
    with Session(engine) as session:
        # Clear any existing session state
        session.expunge_all()
        
        # --- 1. Create and merge User ---
        realtor_user = User(
            id=USER_ID_JANE,
            full_name="Jane Doe",
            email="jane.doe@realty.com",
            phone_number="+15558675309",
            market_focus=["Sunnyvale", "Mountain View"]
        )
        session.merge(realtor_user)
        
        # --- 2. Create and merge Property ---
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
        session.merge(prop_maple)
        
        # --- 3. Create and merge Clients individually ---
        client1 = Client(
            id=CLIENT_ID_ALEX,
            full_name="Alex Chen (Demo)",
            email="alex.chen@example.com",
            phone="+14155551234",
            tags=["Investor", "Past Client"],
            preferences={
                "notes": ["Prefers properties with high ROI."],
                "source": "demo",
                "locations": ["Sunnyvale"],
                "budget_max": 2000000,
                "min_bedrooms": 3
            }
        )
        session.merge(client1)
        
        client2 = Client(
            id=CLIENT_ID_SAM,
            full_name="Samantha Miller (Demo)",
            email="samantha.miller@example.com",
            phone="+16505555678",
            tags=["First-Time Buyer"],
            preferences={
                "notes": ["Really wants a large yard for her dog."],
                "source": "demo",
                "min_bedrooms": 3
            }
        )
        session.merge(client2)
        
        client3 = Client(
            id=CLIENT_ID_BEN,
            full_name="Ben Carter (Demo)",
            email="ben.carter@example.com",
            phone=None,
            tags=["Renter", "Future Buyer"],
            preferences={
                "notes": ["Wants to buy in the next 12 months."],
                "source": "demo"
            }
        )
        session.merge(client3)
        
        # Commit base objects
        session.commit()
        
        # --- 4. Create Campaign Briefing ---
        price_drop_campaign = CampaignBriefing(
            id=CAMPAIGN_ID_PRICE_DROP,
            user_id=USER_ID_JANE,
            campaign_type="price_drop",
            headline="Price Drop: 123 Maple St, Sunnyvale, CA",
            key_intel={
                "address": "123 Maple St, Sunnyvale, CA",
                "price": "1,100,000",
                "price_change": "150,000"
            },
            original_draft="Hi {client_name}, great news!",
            matched_audience=[{
                "client_id": str(CLIENT_ID_ALEX),
                "client_name": "Alex Chen (Demo)",
                "match_score": 95,
                "match_reason": "Location Match, Under Budget"
            }],
            triggering_event_id=PROP_ID_MAPLE,
            status="new"
        )
        session.merge(price_drop_campaign)
        
        # --- 5. Create Scheduled Messages ---
        now = datetime.now(timezone.utc)
        bday_message = ScheduledMessage(
            id=MSG_ID_BDAY,
            client_id=CLIENT_ID_SAM,
            content="Happy Birthday, Samantha!",
            scheduled_at=now + timedelta(days=30)
        )
        session.merge(bday_message)
        
        checkin_message = ScheduledMessage(
            id=MSG_ID_CHECKIN,
            client_id=CLIENT_ID_SAM,
            content="Hi Samantha, just checking in!",
            scheduled_at=now + timedelta(days=90)
        )
        session.merge(checkin_message)
        
        # Final commit
        session.commit()
        
        print("SEEDER: Seeding complete. All data committed to the database.")
