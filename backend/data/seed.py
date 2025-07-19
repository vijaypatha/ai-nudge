# FILE: backend/data/seed.py
# --- VERSION 3.0 ---
# This version enriches client data with more context, keywords, and specific
# phone numbers to enable real-world testing and more nuanced AI matching.

import logging
from sqlalchemy.orm import Session
import asyncio
from datetime import datetime, timedelta, timezone

from .database import engine
from .models.user import User, UserType
from .models.client import Client
from .models.resource import Resource
from .models.campaign import CampaignBriefing
from .models.faq import Faq
from common.config import get_settings
from . import crm as crm_service
settings = get_settings()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def seed_database():
    """
    Main function to seed both Realtor and Therapist data with diverse clients.
    """
    logger.info("--- Starting database seeding process ---")
    
    with Session(engine) as session:
        # Clear existing data for a clean seed
        logger.info("Clearing existing data...")
        session.query(CampaignBriefing).delete()
        session.query(Faq).delete()
        session.query(Client).delete()
        session.query(Resource).delete()
        session.query(User).delete()
        session.commit()
        
        logger.info("Previous data cleared. Seeding new data...")

        # --- Step 1: Create Users for Each Vertical ---
        realtor_user = User(
            id="75411688-5705-4dd8-9b47-5355a34d15ec",  # Fixed ID to match existing user
            user_type=UserType.REALTOR,
            full_name="Jane Doe",
            email="jane.doe@realty.com",
            phone_number="+15558675309",
            twilio_phone_number="+143527219870", # As requested
            market_focus=["St. George", "Washington", "Hurricane", "Santa Clara"],
            tool_provider=settings.MLS_PROVIDER,
            vertical="real_estate",
            specialties=[] # Ensure specialties is an empty list if not provided
        )
        session.add(realtor_user)
        
        therapist_user = User(
            id="98d7acdc-362d-4682-b2e7-8a42e0c05a9f",  # Fixed ID to match current user
            user_type=UserType.THERAPIST,
            full_name="Dr. Sarah Chen",
            email="sarah.chen@therapypractice.com",
            phone_number="+15558675310",
            twilio_phone_number="+14352721987", # As requested
            specialties=["anxiety", "parenting", "mindfulness", "grief"],
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
            user_id=realtor_user.id, resource_type="property", status="active",
            attributes={"address": "456 Oak Ave, St. George, UT", "price": 550000.0}
        ))
        
        # --- Step 3: Create A DIVERSE set of Clients ---
        
        # -- REAL ESTATE CLIENTS --
        buyer_client = Client(
            user_id=realtor_user.id, full_name="Alex Chen (Buyer)",
            notes="Looking for a starter home, maybe a fixer-upper. Wants a large yard for a dog. Mentioned needing good schools and a quiet street. Prefers single-story homes.",
            preferences={"budget_max": 1200000, "min_bedrooms": 3, "locations": ["St. George", "Washington"], "keywords": ["yard", "fixer", "single-story", "quiet street"]}
        )
        seller_client = Client(
            user_id=realtor_user.id, full_name="Brenda Miller (Seller)",
            phone="+13856268825", # As requested for testing
            notes="Homeowner in the 'Tonaquint' area of St. George. Thinking about downsizing in the next 6-12 months. Very interested in what homes like hers are selling for.",
            user_tags=["prospective-seller", "homeowner", "downsizing"],
            preferences={"locations": ["Tonaquint", "St. George", "Hurricane"]}
        )
        investor_client = Client(
            user_id=realtor_user.id, full_name="Carlos Rodriguez (Investor)",
            notes="Real estate investor looking for multi-family properties or homes with rental potential (e.g., casitas or basement apartments). Focused on cash flow and ROI, not primary residence features.",
            user_tags=["investor", "1031-exchange"],
            preferences={"locations": ["St. George", "Hurricane"], "keywords": ["duplex", "triplex", "investment", "cash flow", "tenant", "rental", "investor"]}
        )
        luxury_client = Client(
            user_id=realtor_user.id, full_name="Diana Prince (Luxury Client)",
            notes="Looking to sell her luxury condo in 'Entrada' and purchase a larger estate with a view, possibly in 'The Ledges' or 'Stone Cliff'. High-end finishes and privacy are key.",
            user_tags=["luxury-client", "prospective-seller", "buyer"],
            preferences={"budget_max": 7000000, "min_bedrooms": 4, "locations": ["The Ledges", "Stone Cliff", "Entrada"], "keywords": ["view", "luxury", "gated", "privacy", "custom", "pool"]}
        )

        # -- THERAPY CLIENTS --
        standard_therapy_client = Client(
            user_id=therapist_user.id, full_name="Jennifer Martinez",
            phone="+13856268825",
            notes="Experiencing generalized anxiety and looking for coping mechanisms.",
            last_interaction=datetime.now(timezone.utc).isoformat(),
            user_tags=["anxiety"]
        )

        parenting_client = Client(
            user_id=therapist_user.id, full_name="Michael Carter",
            notes="Struggling with work-life balance after the birth of his second child. Needs strategies for managing stress and being a more present parent.",
            user_tags=["parenting", "stress"]
        )
        grief_client = Client(
            user_id=therapist_user.id, full_name="Emily Rodriguez",
            notes="Recently lost a parent and is navigating the grieving process. Looking for resources on coping with loss.",
            user_tags=["grief", "loss"]
        )
        mindfulness_client = Client(
            user_id=therapist_user.id, full_name="David Lee",
            notes="Wants to learn about mindfulness and meditation to improve focus and reduce daily stress.",
            user_tags=["mindfulness", "stress"]
        )

        therapy_clients = [standard_therapy_client, parenting_client, grief_client, mindfulness_client]
        realty_clients = [buyer_client, seller_client, investor_client, luxury_client]
        
        session.add_all(realty_clients)
        session.add_all(therapy_clients)
        session.commit()

        for client in realty_clients + therapy_clients:
            session.refresh(client)
        
        # --- Step 4: Create FAQs ---
        session.add(Faq(user_id=realtor_user.id, question="What's the market like?", answer="Competitive."))
        session.add(Faq(user_id=therapist_user.id, question="How often are sessions?", answer="Weekly is typical."))

        # --- Step 5: Regenerate embeddings for all new clients ---
        logger.info("Generating initial embeddings for all seeded clients...")
        for client in realty_clients + therapy_clients:
            await crm_service.regenerate_embedding_for_client(client, session=session)
        logger.info("Embeddings generated.")

        session.commit()
        logger.info("Database seeding completed successfully.")
        print("✅✅✅ Database seeding completed successfully! ✅✅✅")


if __name__ == "__main__":
    asyncio.run(seed_database())