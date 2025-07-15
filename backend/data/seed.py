# File Path: backend/data/seed.py
# --- MODIFIED: Passed the main session into the nudge engine to unify the transaction.

import uuid
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from sqlmodel import Session

from .database import engine
from .models.client import Client
from .models.message import Message, ScheduledMessage
from .models.resource import Resource
from .models.user import User, UserType
from .models.event import MarketEvent
from .models.campaign import CampaignBriefing

from data import crm as crm_service
from agent_core.brain import nudge_engine

# Deterministic UUIDs
USER_ID_JANE = uuid.UUID("a8c6f1d7-8f7a-4b6e-8b0f-9e5a7d6c5b4a")
PROP_ID_MAPLE = uuid.UUID("b9f8e1a2-7d6c-4b3a-9e8f-1a2b3c4d5e6f")
CLIENT_ID_ALEX = uuid.UUID("c1e2d3f4-5b6a-7c8d-9e0f-1a2b3c4d5e6f")
CLIENT_ID_SAM = uuid.UUID("d2f3e4a5-6b7a-8c9d-0e1f-2a3b4c5d6e7f")
CLIENT_ID_BEN = uuid.UUID("e3f4a5b6-7a8b-9c0d-1e2f-3a4b5c6d7e8f")
CLIENT_ID_CARLA = uuid.UUID("f4a5b6c7-8b9c-0d1e-2f3a-4b5c6d7e8f90")

def clear_demo_data():
    """This function is obsolete and no longer called."""
    pass

async def seed_database():
    """Populates the database with initial data for development."""
    logging.info("SEEDER: Preparing to seed the database...")
    
    with Session(engine) as session:
        realtor_user = User(
            id=USER_ID_JANE,
            user_type=UserType.REALTOR,
            full_name="Jane Doe",
            email="jane.doe@realty.com",
            phone_number="+15558675309",
            twilio_phone_number="+14352721987",
            market_focus=["Sunnyvale", "Mountain View"]
        )
        session.add(realtor_user)
        session.commit()
        logging.info("SEEDER: Base user committed successfully.")

        property_attributes = {
            "address": "123 Maple St, Sunnyvale, CA", "price": 1100000.0, "property_type": "Single Family",
            "bedrooms": 4, "bathrooms": 3, "square_footage": 2200,
            "PublicRemarks": "An entertainer's dream! This spacious, light-filled home features an open floor plan ideal for gatherings. Flooded with sunlight, this home features a serene loft perfect for a studio or office. The quiet backyard is a private oasis. Recent updates include a new roof and HVAC system."
        }
        resource_maple = Resource(id=PROP_ID_MAPLE, user_id=USER_ID_JANE, resource_type="property", status="active", attributes=property_attributes)

        clients_to_create = [
            Client(id=CLIENT_ID_ALEX, user_id=USER_ID_JANE, full_name="Alex Chen (Demo)", email="alex.chen@example.com", phone="+14155551234", user_tags=["investor"], notes="Looking for a high ROI property.", preferences={"locations": ["Sunnyvale"], "budget_max": 2000000, "min_bedrooms": 5}),
            Client(id=CLIENT_ID_SAM, user_id=USER_ID_JANE, full_name="Samantha Miller (Demo)", email="samantha.miller@example.com", phone="+16505555678", user_tags=["first_time_buyer"], notes="Really wants a large yard for her dog, Buddy. Loves to do Yoga outside.", preferences={"min_bedrooms": 3}),
            Client(id=CLIENT_ID_BEN, user_id=USER_ID_JANE, full_name="Ben Carter (Demo)", email="ben.carter@example.com", phone="+13856268825", user_tags=[], last_interaction=None, notes="Wants to buy in the next 12 months.", preferences={}),
            Client(id=CLIENT_ID_CARLA, user_id=USER_ID_JANE, full_name="Conceptual Carla (Demo)", email="carla.conceptual@example.com", phone="+14085559876", user_tags=["artist"], notes="She's an artist and wants a home with great natural light and a quiet, inspiring space to paint. A serene environment is a must-have.", preferences={"budget_max": 1500000, "locations": ["Sunnyvale"]})
        ]
        
        session.add(resource_maple)
        session.add_all(clients_to_create)
        session.commit()
        logging.info("SEEDER: Dependent resources and clients committed.")
        
        logging.info("SEEDER: Generating embeddings for all seeded clients...")
        embedding_tasks = []
        for client_data in clients_to_create:
            client_in_db = session.get(Client, client_data.id)
            if client_in_db:
                task = crm_service.regenerate_embedding_for_client(client_in_db, session)
                embedding_tasks.append(task)
        
        await asyncio.gather(*embedding_tasks)
        session.commit()
        logging.info("SEEDER: Embeddings generated and saved successfully.")
        
        logging.info("SEEDER: Simulating a 'New Listing' event to test the core matching logic...")
        listing_payload = {
            "ListingKey": str(uuid.uuid4()), "UnparsedAddress": property_attributes["address"], "ListPrice": property_attributes["price"],
            "BedroomsTotal": property_attributes["bedrooms"], "BathroomsTotalInteger": property_attributes["bathrooms"],
            "PublicRemarks": property_attributes["PublicRemarks"], "SubdivisionName": "Sunnyvale",
            "Media": [{"MediaURL": "https://images.unsplash.com/photo-1580587771525-78b9dba3b914", "Order": 0}]
        }
        event = MarketEvent(id=uuid.uuid4(), event_type="new_listing", market_area="Sunnyvale", entity_type="RESOURCE", entity_id=PROP_ID_MAPLE, payload=listing_payload)
        session.add(event)
        session.commit()
        
        realtor_user = session.get(User, USER_ID_JANE)
        
        # --- THE FIX: Pass the main 'session' object into the nudge engine. ---
        await nudge_engine.process_market_event(event=event, realtor=realtor_user, db_session=session)
        
        await nudge_engine.generate_recency_nudges(realtor=realtor_user)
        
        session.commit()
        logging.info("SEEDER: Seeding complete.")