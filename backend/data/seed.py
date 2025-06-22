# ---
# File Path: backend/data/seed.py
# Purpose: Populates the application with mock data for development.
# ---
from datetime import datetime, timezone
from . import crm as crm_service
from .models.user import User
from .models.client import Client
from .models.property import Property

def seed_database():
    """
    Clears and populates the mock database with a realistic dataset for a Realtor.
    This function is called once on application startup.
    """
    print("SEEDING DATABASE: Clearing existing mock data...")
    crm_service.clear_all_data()

    # --- 1. Create the Realtor (the User) ---
    realtor_user = User(
        full_name="Jane Doe",
        email="jane.doe@realty.com",
        market_focus=["Sunnyvale", "Mountain View"],
        strategy={"nudge_format": "ready-to-send"}
    )
    crm_service.save_user(realtor_user)
    print(f"SEEDING DATABASE: Created User -> {realtor_user.full_name}")

    # --- 2. Create Properties in the Realtor's market ---
    # NOTE: Client data is no longer seeded here. It will be added by the user.
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
    crm_service.save_property(prop_maple)
    print(f"SEEDING DATABASE: Created Property -> {prop_maple.address}")

    print("SEEDING DATABASE: Complete. Ready for client import.")