from datetime import datetime, timezone
from sqlmodel import Session, SQLModel
from .database import engine

# Import ALL table models. This ensures they are known to SQLModel
# before we ask it to resolve the relationships.
from .models.user import User
from .models.property import Property
from .models.client import Client
from .models.message import ScheduledMessage
from .models.campaign import CampaignBriefing
from .models.event import MarketEvent

def seed_database():
    """
    Resolves model forward references, then clears and populates the database.
    """
    print("SEEDER: Preparing to seed the database...")
    
    print("SEEDER: Model relationships resolved automatically.")
    
    with Session(engine) as session:
        print("SEEDER: Dropping all tables...")
        SQLModel.metadata.drop_all(engine)
        
        print("SEEDER: Creating all tables...")
        SQLModel.metadata.create_all(engine)
        
        realtor_user = User(
            full_name="Jane Doe",
            email="jane.doe@realty.com",
            market_focus=["Sunnyvale", "Mountain View"],
            strategy={"nudge_format": "ready-to-send"}
        )
        
        session.add(realtor_user)
        print(f"SEEDER: Staged User -> {realtor_user.full_name}")
        
        now_iso = datetime.now(timezone.utc).isoformat()
        
        prop_maple = Property(
            address="123 Maple St, Sunnyvale, CA",
            price=1250000.0,
            property_type="Single Family",
            bedrooms=4,
            bathrooms=3,
            square_footage=2200,
            listing_url="https://example.com/listing/123-maple-st",
            image_urls=[],
            last_updated=now_iso
        )
        
        session.add(prop_maple)
        print(f"SEEDER: Staged Property -> {prop_maple.address}")
        
        print("SEEDER: Committing new data to the database...")
        session.commit()
        print("SEEDER: Seeding complete.")
