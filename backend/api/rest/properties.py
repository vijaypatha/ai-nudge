# ---
# File Path: backend/api/rest/properties.py
# Purpose: Defines API endpoints for properties and triggers the Nudge Engine on events.
# ---

from fastapi import APIRouter, HTTPException, status
from typing import List
from uuid import UUID

from data.models.property import Property, PropertyCreate, PriceUpdate
# NEW: Import the event model and the nudge engine
from data.models.event import MarketEvent
from agent_core.brain import nudge_engine
from data import crm as crm_service

# This service acts as a stand-in for an actual MLS database connection.
# I am assuming you have this file and it contains the 'simulate_price_drop' function.
from integrations import mls as mls_service

router = APIRouter(
    prefix="/properties",
    tags=["Properties"]
)

@router.post("/", response_model=Property, status_code=status.HTTP_201_CREATED)
async def create_property(property_data: PropertyCreate):
    """Creates a new property listing."""
    # NOTE: The existing mls_service is assumed to handle the property creation.
    # In a real system, we would need to provide the full implementation.
    new_prop = mls_service.add_new_listing(property_data)
    return new_prop

@router.get("/", response_model=List[Property])
async def get_all_properties():
    """Retrieves all active property listings."""
    return crm_service.get_all_properties_mock() # Using our CRM mock for consistency

@router.get("/{property_id}", response_model=Property)
async def get_property_by_id(property_id: UUID):
    """Retrieves a single property by its unique ID."""
    prop = crm_service.get_property_by_id(property_id)
    if prop:
        return prop
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")

@router.post("/{property_id}/simulate-price-drop", response_model=Property)
async def simulate_property_price_drop(property_id: UUID, price_update: PriceUpdate):
    """Simulates a price drop and triggers the Nudge Engine."""
    property_to_update = crm_service.get_property_by_id(property_id)
    if not property_to_update:
        raise HTTPException(status_code=404, detail="Property not found")
    old_price = property_to_update.price
    updated_prop = crm_service.update_property_price(property_id, price_update.new_price)

    if updated_prop:
        print(f"TRIGGER: Price drop detected for property {property_id}. Notifying Nudge Engine.")
        realtor_user = crm_service.get_user_by_id(crm_service.mock_users_db[0].id)
        market_area_city = updated_prop.address.split(',')[1].strip()

        # CORRECTED: Use lowercase event_type
        price_drop_event = MarketEvent(
            event_type="price_drop",
            market_area=market_area_city,
            entity_type="PROPERTY",
            entity_id=property_id,
            payload={"old_price": old_price, "new_price": updated_prop.price}
        )
        if realtor_user:
            await nudge_engine.process_market_event(event=price_drop_event, realtor=realtor_user)
        return updated_prop
    raise HTTPException(status_code=400, detail="Could not simulate price drop.")

@router.post("/simulate-new-listing", response_model=Property, status_code=status.HTTP_201_CREATED)
async def simulate_new_listing(property_data: PropertyCreate):
    """Creates a new property and triggers the Nudge Engine for a NEW_LISTING event."""
    from datetime import datetime, timezone
    new_property_data = property_data.model_dump()
    new_property_data["last_updated"] = datetime.now(timezone.utc).isoformat()
    new_prop = Property(**new_property_data)
    crm_service.save_property(new_prop)
    print(f"TRIGGER: New listing detected for property {new_prop.address}. Notifying Nudge Engine.")

    realtor_user = crm_service.get_user_by_id(crm_service.mock_users_db[0].id)
    market_area_city = new_prop.address.split(',')[1].strip()

    # CORRECTED: Use lowercase event_type
    new_listing_event = MarketEvent(
        event_type="new_listing",
        market_area=market_area_city,
        entity_type="PROPERTY",
        entity_id=new_prop.id,
        payload=new_prop.model_dump()
    )
    if realtor_user:
        await nudge_engine.process_market_event(event=new_listing_event, realtor=realtor_user)
    return new_prop