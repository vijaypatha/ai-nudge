# FILE: backend/data/seed.py
# --- MODIFIED: This version corrects the data clearing logic to prevent foreign key violations.

import logging
import sys
import os

from sqlalchemy.orm import Session
import asyncio
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from .database import engine
# --- FIXED: Defer model imports to prevent table redefinition ---
# from .models.user import User, UserType
# from .models.client import Client
# from .models.message import Message, ScheduledMessage
# from .models.resource import Resource, ContentResource
# from .models.campaign import CampaignBriefing
# from .models.faq import Faq
# from .models.event import MarketEvent, PipelineRun
from common.config import get_settings
from . import crm as crm_service
settings = get_settings()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def seed_database():
    """
    Main function to seed both Realtor and Therapist data with diverse clients,
    resources, and sample Nudges for UI testing.
    """
    logger.info("--- Starting database seeding process ---")
    
    with Session(engine) as session:
        # --- MODIFIED: Corrected deletion order to respect foreign key constraints ---
        logger.info("Clearing existing data...")
        
        # --- FIXED: Import models only when needed ---
        from .models.user import User, UserType
        from .models.client import Client
        from .models.message import Message, ScheduledMessage
        from .models.resource import Resource, ContentResource
        from .models.campaign import CampaignBriefing
        from .models.faq import Faq
        from .models.event import MarketEvent, PipelineRun
        
        # Clear tables that depend on users or other primary tables first.
        # The order here is critical to avoid integrity errors.
        session.query(ScheduledMessage).delete()
        session.query(CampaignBriefing).delete()
        session.query(Message).delete()
        session.query(Faq).delete()
        session.query(Client).delete()
        # Clear events before resources and users
        session.query(MarketEvent).delete()
        session.query(PipelineRun).delete()
        # Resources must be deleted before Users.
        session.query(Resource).delete()
        session.query(ContentResource).delete()
        # Finally, delete the Users, as all dependent records are now gone.
        session.query(User).delete()
        session.commit()
        
        logger.info("Previous data cleared. Seeding new data...")

        # --- Step 1: Create Users for Each Vertical ---
        realtor_user = User(
            id="75411688-5705-4dd8-9b47-5355a34d15ec",
            user_type=UserType.REALTOR,
            full_name="Jane Doe",
            email="jane.doe@realty.com",
            phone_number="+15558675309",
            twilio_phone_number="+143527219870",
            market_focus=["St. George", "Washington", "Hurricane", "Santa Clara"],
            tool_provider=settings.MLS_PROVIDER,
            vertical="real_estate",
            specialties=[],
            onboarding_complete=True
        )
        session.add(realtor_user)
        
        therapist_user = User(
            id="98d7acdc-362d-4682-b2e7-8a42e0c05a9f",
            user_type=UserType.THERAPIST,
            full_name="Dr. Sarah Chen",
            email="sarah.chen@therapypractice.com",
            phone_number="+15558675310",
            twilio_phone_number="+14352721987",
            specialties=["anxiety", "parenting", "mindfulness", "grief"],
            tool_provider=None,
            vertical="therapy"
        )
        session.add(therapist_user)
        
        session.commit()
        session.refresh(realtor_user)
        session.refresh(therapist_user)

        # --- Step 2: Create Resources for Each Vertical ---
        
        # Realtor's property resource (as Resource object)
        session.add(Resource(
            user_id=realtor_user.id,
            id="a1b2c3d4-e5f6-7890-1234-567890abcdef", # Fixed ID for predictability
            resource_type="property",
            entity_id="202401011234567890", # Example MLS Number
            status="active",
            attributes={
                "UnparsedAddress": "123 Investment Lane, St. George, UT",
                "ListPrice": 750000.0,
                "BedroomsTotal": 4,
                "BathroomsTotalInteger": 2,
                "LivingArea": 2200,
                "MlsStatus": "Active",
                "PublicRemarks": "Excellent duplex opportunity in a high-demand rental area. Great cash flow potential. Each unit is 2 bed, 1 bath. Close to downtown and university.",
                "listing_url": "https://example.com/listing/123",
                "Media": [{"Order": 0, "MediaURL": "https://placehold.co/600x400/1A1D24/FFFFFF?text=123+Investment+Ln"}]
            }
        ))

        # *** FIXED: Therapist's content is created as a Resource to work with foreign key constraints ***
        session.add(Resource(
            user_id=therapist_user.id,
            id="c1d2e3f4-a5b6-7890-1234-567890fedcba", # Fixed ID for predictability
            resource_type="web_content",
            entity_id="https://example.com/anxiety-meditation",
            status="active",
            attributes={
                "title": "Anxiety Meditation Guide",
                "description": "A 5-minute guided mindful breathing exercise for reducing acute anxiety and promoting calmness.",
                "url": "https://example.com/anxiety-meditation",
                "content_type": "video",
                "categories": ["anxiety", "meditation", "mindfulness"],
                "thumbnail_url": "https://placehold.co/600x400/5B21B6/FFFFFF?text=Mindful+Meditation"
            }
        ))
        
        # --- Step 3: Create A DIVERSE set of Clients ---
        buyer_client = Client(
            user_id=realtor_user.id, 
            full_name="Alex Chen (Buyer)",
            user_tags=["buyer", "first-time"],
            preferences={
                "budget_max": 800000,
                "locations": ["St. George", "Washington", "Hurricane", "Santa Clara"],
                "min_bedrooms": 3,
                "min_bathrooms": 2,
                "keywords": ["family", "move-in ready", "good schools", "single family"]
            }
        )
        seller_client = Client(
            user_id=realtor_user.id, 
            full_name="Brenda Miller (Seller)", 
            phone="+13856268825",
            user_tags=["prospective-seller"],
            preferences={
                "locations": ["St. George", "Hurricane", "Washington"],
                "keywords": ["market analysis", "comparable sales", "property value"]
            }
        )
        investor_client = Client(
            user_id=realtor_user.id, 
            full_name="Carlos Rodriguez (Investor)",
            user_tags=["investor"],
            preferences={
                "budget_max": 1000000,
                "locations": ["St. George", "Washington", "Hurricane", "Santa Clara"],
                "keywords": ["duplex", "multi-family", "cash flow", "investment", "rental", "income property"]
            }
        )
        luxury_client = Client(
            user_id=realtor_user.id, 
            full_name="Diana Prince (Luxury Client)",
            user_tags=["buyer", "luxury"],
            preferences={
                "budget_max": 1500000,
                "locations": ["Snow Canyon", "The Cliffs", "Entrada", "St. George"],
                "min_bedrooms": 4,
                "min_bathrooms": 3,
                "keywords": ["luxury", "golf", "mountain view", "high-end", "country club", "premium"]
            }
        )
        
        standard_therapy_client = Client(
            user_id=therapist_user.id, full_name="Jennifer Martinez",
            phone="+13856268825",
            notes="Experiencing generalized anxiety and looking for coping mechanisms.",
            last_interaction=datetime.now(timezone.utc).isoformat(),
            user_tags=["anxiety"]
        )
        
        realty_clients = [buyer_client, seller_client, investor_client, luxury_client]
        therapy_clients = [standard_therapy_client]
        
        session.add_all(realty_clients)
        session.add_all(therapy_clients)
        session.commit()

        for client in realty_clients + therapy_clients:
            session.refresh(client)
        
        # --- Step 4: Create FAQs ---
        session.add(Faq(user_id=realtor_user.id, question="What's the market like?", answer="Competitive."))
        session.add(Faq(user_id=therapist_user.id, question="How often are sessions?", answer="Weekly is typical."))

        # --- Step 5: Create Sample CampaignBriefings (Nudges) for UI Testing ---
        logger.info("Creating sample CampaignBriefings for UI testing...")
        
        # Nudge for Realtor
        investor_client_id = investor_client.id
        realtor_nudge = CampaignBriefing(
            user_id=realtor_user.id,
            triggering_resource_id="a1b2c3d4-e5f6-7890-1234-567890abcdef",
            campaign_type="new_listing",
            status="draft", headline="New Investment Property Opportunity",
            original_draft="Hi Carlos, a new duplex just hit the market...",
            matched_audience=[{"client_id": str(investor_client_id), "client_name": "Carlos Rodriguez (Investor)", "match_score": 92, "match_reasons": ["🔥 Seeking multi-family investment"] }],
            key_intel={ "strategic_context": "A rare multi-family property was just listed...", "content_preview": { "content_type": "property", "url": "https://example.com/listing/123", "image_url": "https://placehold.co/600x400/1A1D24/FFFFFF?text=123+Investment+Ln", "title": "123 Investment Lane, St. George, UT", "description": "Excellent duplex opportunity...", "details": { "price": 750000.0, "bedrooms": 4, "bathrooms": 2 } } }
        )
        session.add(realtor_nudge)

        # Nudge for Therapist (Content Recommendation)
        therapy_client_id = standard_therapy_client.id
        therapist_nudge = CampaignBriefing(
            user_id=therapist_user.id,
            triggering_resource_id="c1d2e3f4-a5b6-7890-1234-567890fedcba",
            campaign_type="content_suggestion",
            status="draft", headline="Share Anxiety Resource with Jennifer",
            original_draft="Hi Jennifer, thinking of you. I came across this short meditation that some of my other clients have found helpful for managing moments of anxiety. Thought you might appreciate it.",
            matched_audience=[{"client_id": str(therapy_client_id), "client_name": "Jennifer Martinez", "match_score": 95, "match_reasons": ["✅ Expressed anxiety", "✅ Open to resources"] }],
            key_intel={ "strategic_context": "Sharing a relevant, timely resource can reinforce coping strategies discussed in your sessions.", "timing_rationale": "Proactive support between sessions strengthens the therapeutic alliance.", "trigger_source": "Content Library", "style_match_score": 90, "tone_indicators": ["Empathetic", "Supportive"], "content_preview": { "content_type": "video", "url": "https://example.com/anxiety-meditation", "image_url": "https://placehold.co/600x400/5B21B6/FFFFFF?text=Mindful+Meditation", "title": "Anxiety Meditation Guide", "description": "A 5-minute guided mindful breathing exercise for reducing acute anxiety and promoting calmness." } }
        )
        session.add(therapist_nudge)

        # --- Step 6: Regenerate embeddings for all new clients ---
        logger.info("Generating initial embeddings for all seeded clients...")
        for client in realty_clients + therapy_clients:
            try:
                await crm_service.regenerate_embedding_for_client(client, session=session)
            except Exception as e:
                logger.warning(f"CRM (SEED): Skipping embedding for client {client.id} - {e}")
        logger.info("Embeddings generated.")

        session.commit()
        logger.info("Database seeding completed successfully.")
        print("✅✅✅ Database seeding completed successfully! ✅✅✅")


if __name__ == "__main__":
    asyncio.run(seed_database())