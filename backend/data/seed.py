# FILE: backend/data/seed.py
import logging
from sqlalchemy import text
from sqlalchemy.orm import Session
import asyncio
from datetime import datetime, timezone

from .database import engine
from common.config import get_settings
# ✅ Import the function to create default surveys
from agent_core.survey_processor import create_default_surveys_for_user

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
        logger.info("Clearing existing data...")
        
        from .models.user import User, UserType
        from .models.client import Client, ClientIntakeSurvey
        from .models.message import Message, ScheduledMessage
        from .models.resource import Resource, ContentResource
        from .models.campaign import CampaignBriefing
        from .models.faq import Faq
        from .models.event import MarketEvent, PipelineRun
        from .models.survey import SurveyQuestion, SurveyTemplate

        # The deletion order is corrected to respect all database foreign key constraints.
        session.query(ScheduledMessage).delete()
        session.query(Message).delete()
        session.query(CampaignBriefing).delete()
        session.query(ClientIntakeSurvey).delete()
        session.query(Faq).delete()
        
        # Safely attempt to delete survey questions and templates
        try:
            if session.bind.dialect.name == 'postgresql':
                # Use TRUNCATE CASCADE to handle foreign keys and reset sequences
                session.execute(text("TRUNCATE TABLE surveyquestion RESTART IDENTITY CASCADE"))
                session.execute(text("TRUNCATE TABLE surveytemplate RESTART IDENTITY CASCADE"))
            else:
                session.query(SurveyQuestion).delete()
                session.query(SurveyTemplate).delete()
            logger.info("Cleared surveyquestion and surveytemplate tables.")
        except Exception:
            logger.warning("Could not clear survey tables (they may not exist yet). Continuing...")
            session.rollback()
            
        session.query(Client).delete()
        session.query(MarketEvent).delete()
        session.query(PipelineRun).delete()
        session.query(Resource).delete()
        session.query(ContentResource).delete()
        session.query(User).delete()
        
        session.commit()
        
        logger.info("Previous data cleared. Seeding new data...")

        realtor_user = User(
            id="75411688-5705-4dd8-9b47-5355a34d15ec", user_type=UserType.REALTOR, full_name="Jane Doe",
            email="jane.doe@realty.com", phone_number="+15558675309", twilio_phone_number="+143527219870",
            market_focus=["St. George", "Washington"], tool_provider=settings.MLS_PROVIDER, vertical="real_estate",
            onboarding_complete=True
        )
        therapist_user = User(
            id="98d7acdc-362d-4682-b2e7-8a42e0c05a9f", user_type=UserType.THERAPIST, full_name="Dr. Sarah Chen",
            email="sarah.chen@therapypractice.com", phone_number="+15558675310", twilio_phone_number="+14352721987",
            specialties=["anxiety", "parenting"], vertical="therapy", onboarding_complete=True
        )
        session.add_all([realtor_user, therapist_user])
        session.commit()
        session.refresh(realtor_user)
        session.refresh(therapist_user)

        # ✅ NEW: Explicitly create default surveys for the seed users
        logger.info("Creating default surveys for seed users...")
        create_default_surveys_for_user(user=realtor_user, session=session)
        create_default_surveys_for_user(user=therapist_user, session=session)
        logger.info("Default surveys for seed users created.")

        investor_client = Client(id="9afb4bd1-9f26-4ae8-8a63-af71537dd932", user_id=realtor_user.id, full_name="Carlos Rodriguez (Investor)", user_tags=["investor"], preferences={"keywords": ["duplex", "investment"]})
        therapy_client = Client(id="54d5b199-0cf2-43e1-bd52-c6d7ba90699b", user_id=therapist_user.id, full_name="Jennifer Martinez", user_tags=["anxiety"], notes="Experiencing generalized anxiety.")
        session.add_all([investor_client, therapy_client])
        session.commit()

        logger.info("Database seeding completed successfully.")


if __name__ == "__main__":
    asyncio.run(seed_database())