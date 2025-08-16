# FILE: backend/data/seed.py
import logging
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.orm import Session
import asyncio
from datetime import datetime, timezone

from .database import engine
from common.config import get_settings

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
        
        # --- THIS IS THE FIX ---
        # The deletion order is now corrected to respect all database foreign key constraints.
        # Dependent records are deleted before their parent records.
        
        # 1. Delete records that depend on CampaignBriefing, Client, User, or Resource
        session.query(ScheduledMessage).delete()
        session.query(Message).delete()

        # 2. Now it's safe to delete CampaignBriefing
        session.query(CampaignBriefing).delete()

        # 3. Delete other records that depend on Client and User
        session.query(ClientIntakeSurvey).delete()
        session.query(Faq).delete()
        
        # 4. Safely attempt to delete survey questions
        try:
            # Use TRUNCATE for PostgreSQL to reset identity columns, or DELETE for others.
            # This is a general approach; for production, you might use dialect-specific code.
            if session.bind.dialect.name == 'postgresql':
                session.execute(text("TRUNCATE TABLE surveyquestion RESTART IDENTITY CASCADE"))
            else:
                # This will fail if the table doesn't exist, hence the try/except
                session.query_class.delete() # A placeholder for a potential SurveyQuestion model
            logger.info("Cleared surveyquestion table.")
        except Exception:
            logger.warning("Could not clear surveyquestion table (it may not exist yet). Continuing...")
            session.rollback()
            
        # 5. Now it's safe to delete Clients
        session.query(Client).delete()

        # 6. Delete records that depend on User
        session.query(MarketEvent).delete()
        session.query(PipelineRun).delete()
        session.query(Resource).delete()
        session.query(ContentResource).delete()

        # 7. Finally, it's safe to delete the Users
        session.query(User).delete()
        
        session.commit()
        # --- END FIX ---
        
        logger.info("Previous data cleared. Seeding new data...")

        # --- Seeding logic remains the same ---
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

        investor_client = Client(id="9afb4bd1-9f26-4ae8-8a63-af71537dd932", user_id=realtor_user.id, full_name="Carlos Rodriguez (Investor)", user_tags=["investor"], preferences={"keywords": ["duplex", "investment"]})
        therapy_client = Client(id="54d5b199-0cf2-43e1-bd52-c6d7ba90699b", user_id=therapist_user.id, full_name="Jennifer Martinez", user_tags=["anxiety"], notes="Experiencing generalized anxiety.")
        session.add_all([investor_client, therapy_client])
        session.commit()

        logger.info("Database seeding completed successfully.")


if __name__ == "__main__":
    asyncio.run(seed_database())