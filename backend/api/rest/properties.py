# File Path: backend/api/rest/properties.py
from fastapi import APIRouter, HTTPException
from typing import List
import uuid
from pydantic import BaseModel
from data import crm as crm_service
from data.models.property import Property

# FIXED: Add prefix to router definition
router = APIRouter(prefix="/properties")

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
    """Simulate a price drop for a property and trigger campaign generation."""
    try:
        prop_uuid = uuid.UUID(property_id)
        property_obj = crm_service.get_property_by_id(prop_uuid)
        if not property_obj:
            raise HTTPException(status_code=404, detail="Property not found")
        
        all_users = crm_service.get_all_users()
        if not all_users:
            raise HTTPException(status_code=500, detail="No users found in database")
        
        realtor_user = all_users[0]
        print(f"TRIGGER: Price drop detected for property {property_id}. Notifying Nudge Engine.")
        
        updated_property = crm_service.update_property_price(prop_uuid, request.new_price)
        if not updated_property:
            raise HTTPException(status_code=500, detail="Failed to update property price")
        
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
