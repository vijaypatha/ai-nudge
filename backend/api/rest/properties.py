# File Path: backend/api/rest/properties.py
# CORRECTED VERSION: Updated to use database functions instead of mock data

from fastapi import APIRouter, HTTPException
from typing import List
import uuid
from pydantic import BaseModel
from data import crm as crm_service
from data.models.property import Property

router = APIRouter()

class PriceDropRequest(BaseModel):
    new_price: float

@router.get("/", response_model=List[Property])
async def get_all_properties():
    """Get all properties from the database."""
    try:
        return crm_service.get_all_properties()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch properties: {str(e)}")

@router.post("/{property_id}/simulate-price-drop")
async def simulate_property_price_drop(property_id: str, request: PriceDropRequest):
    """
    Simulate a price drop for a property and trigger campaign generation.
    CORRECTED: Use database functions instead of mock data.
    """
    try:
        # Convert string to UUID
        prop_uuid = uuid.UUID(property_id)
        
        # Get the property from database
        property_obj = crm_service.get_property_by_id(prop_uuid)
        if not property_obj:
            raise HTTPException(status_code=404, detail="Property not found")
        
        # Get the first user from database (assuming single user for demo)
        all_users = crm_service.get_all_users()
        if not all_users:
            raise HTTPException(status_code=500, detail="No users found in database")
        
        realtor_user = all_users[0]  # Use first user from database
        
        print(f"TRIGGER: Price drop detected for property {property_id}. Notifying Nudge Engine.")
        
        # Update the property price in database
        updated_property = crm_service.update_property_price(prop_uuid, request.new_price)
        if not updated_property:
            raise HTTPException(status_code=500, detail="Failed to update property price")
        
        # Here you would typically trigger the nudge engine
        # For now, just return success
        return {
            "message": "Price drop simulated successfully",
            "property_id": property_id,
            "old_price": property_obj.price,
            "new_price": request.new_price,
            "user_id": str(realtor_user.id)
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid property ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to simulate price drop: {str(e)}")
