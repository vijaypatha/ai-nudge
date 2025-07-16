# FILE: backend/data/seed.py
# --- MODIFIED: Adds a "Prospective Seller" client ---

import logging
from sqlalchemy.orm import Session
import asyncio

from .database import engine
from .models.user import User, UserType
from .models.client import Client
from .models.resource import Resource
from .models.faq import Faq
from common.config import get_settings
from . import crm as crm_service
settings = get_settings()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def seed_database():
    """
    Main function to seed both Realtor and Therapist data.
    """
    logger.info("--- Starting database seeding process ---")
    
    with Session(engine) as session:
        if session.query(User).first():
            logger.info("Database already contains data. Skipping seed process.")
            return

        # --- Step 1: Create Users for Each Vertical ---
        realtor_user = User(
            user_type=UserType.REALTOR,
            full_name="Jane Doe",
            email="jane.doe@realty.com",
            phone_number="+15558675309",
            twilio_phone_number="+14352721987",
            market_focus=["Sunnyvale", "Mountain View", "Santa Clara"],
            tool_provider=settings.MLS_PROVIDER,
            vertical="real_estate"
        )
        session.add(realtor_user)
        
        therapist_user = User(
            user_type=UserType.THERAPIST,
            full_name="Dr. Sarah Chen",
            email="sarah.chen@therapypractice.com",
            phone_number="+15558675310",
            twilio_phone_number="+14352721988",
            business_name="Mindful Therapy Practice",
            bio="Licensed clinical psychologist specializing in anxiety and trauma.",
            tool_provider=None,
            vertical="therapy"
        )
        session.add(therapist_user)
        
        session.commit()
        session.refresh(realtor_user)
        session.refresh(therapist_user)

        # --- Step 2: Create Vertical-Specific Resources ---
        session.add(Resource(
            user_id=realtor_user.id,
            resource_type="property",
            status="active",
            attributes={
                "address": "123 Maple St, Sunnyvale, CA", "price": 1100000.0,
                "property_type": "Single Family", "bedrooms": 4, "bathrooms": 3,
                "PublicRemarks": "An entertainer's dream! This spacious home features an open floor plan."
            }
        ))
        session.add(Resource(
            user_id=therapist_user.id,
            resource_type="session",
            status="active",
            attributes={
                "title": "Cognitive Behavioral Therapy for Anxiety",
                "description": "Individual CBT session focused on anxiety management.",
                "duration": 60, "specialty": "Anxiety Treatment"
            }
        ))
        
        # --- Step 3: Create Clients for Each User ---
        buyer_client = Client(
            user_id=realtor_user.id, 
            full_name="Alex Chen (Buyer Client)",
            email="alex.chen@example.com", 
            phone="+14155551234",
            notes="Looking for a high ROI property. Interested in Sunnyvale starter homes, maybe a fixer-upper. Wants something with good bones and a large yard for a dog.",
            preferences={
                "budget_max": 2500000,
                "min_bedrooms": 3,
                "locations": ["Sunnyvale", "Santa Clara", "Mountain View"]
            }
        )
        session.add(buyer_client)

        # --- NEW: Add a Seller Client to see different nudge types ---
        seller_client = Client(
            user_id=realtor_user.id,
            full_name="Brenda Miller (Prospective Seller)",
            email="brenda.miller@example.com",
            phone="+14155551236",
            notes="Homeowner in Santa Clara, considering selling in the next 6-12 months. Curious about what her home is worth and recent sales activity in her neighborhood.",
            user_tags=["homeowner", "prospective-seller"],
            preferences={
                "locations": ["Santa Clara"] # Used to find nearby "Just Sold" events
            }
        )
        session.add(seller_client)
        # --- END OF NEW CODE ---

        therapy_client = Client(
            user_id=therapist_user.id, 
            full_name="Jennifer Martinez (Therapy Client)",
            email="jennifer.martinez@example.com", 
            phone="+14155551235",
            notes="Experiencing generalized anxiety and looking for coping mechanisms.",
            preferences={}
        )
        session.add(therapy_client)
        
        session.commit()
        session.refresh(buyer_client)
        session.refresh(seller_client)
        session.refresh(therapy_client)

        # --- Step 4: Create FAQs for Each Vertical ---
        session.add(Faq(
            user_id=realtor_user.id,
            question="What's the current market like in Sunnyvale?",
            answer="The current market is competitive with low inventory and high demand."
        ))
        session.add(Faq(
            user_id=therapist_user.id,
            question="How often should I have therapy sessions?",
            answer="For most clients, weekly sessions are recommended initially."
        ))

        # --- Step 5: Regenerate embeddings for all seeded clients ---
        logger.info("Generating initial embeddings for seeded clients...")
        await crm_service.regenerate_embedding_for_client(buyer_client, session=session)
        await crm_service.regenerate_embedding_for_client(seller_client, session=session) # Added seller client
        await crm_service.regenerate_embedding_for_client(therapy_client, session=session)
        logger.info("Embeddings generated.")

        session.commit()
        logger.info("Database seeding completed successfully.")
        print("✅✅✅ Database seeding completed successfully! ✅✅✅")


if __name__ == "__main__":
    asyncio.run(seed_database())