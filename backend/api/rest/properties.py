# backend/api/rest/properties.py

from fastapi import APIRouter, HTTPException, status # Import necessary FastAPI components
from typing import List                            # For type hinting lists
from uuid import UUID                              # For validating UUID (Universally Unique Identifier)

# Import the Pydantic models for Property, PropertyCreate, and the new PriceUpdate
# These models define the structure of data for properties coming in and out of the API.
from backend.data.models.property import Property, PropertyCreate, PriceUpdate
# Import the mock MLS integration service.
# This service acts as a stand-in for an actual MLS database connection.
from backend.integrations import mls as mls_service

# Initialize an API router specifically for property-related endpoints.
# - prefix="/properties": All routes defined in this router will start with /properties.
# - tags=["Properties"]: Organizes these routes under a "Properties" section in the API documentation (e.g., Swagger UI).
router = APIRouter(
    prefix="/properties",
    tags=["Properties"]
)

@router.post("/", response_model=Property, status_code=status.HTTP_201_CREATED)
async def create_property(property_data: PropertyCreate):
    """
    Endpoint to create a new property listing.

    This function receives data for a new property and adds it to our
    simulated MLS system.
    How it works for the robot: This is like the robot writing down details
    of a brand new house it just heard about in its "House Listing Database."

    - **property_data**: The data needed to create the property, validated by PropertyCreate model.
    - **response_model=Property**: Specifies that the response will follow the Property model structure.
    - **status_code=status.HTTP_201_CREATED**: Indicates that a new resource was successfully created.
    """
    # Use the mock MLS service to add the new listing.
    new_prop = mls_service.add_new_listing(property_data)
    # Return the newly created property object.
    return new_prop

@router.get("/", response_model=List[Property])
async def get_all_properties():
    """
    Endpoint to retrieve all active property listings.

    This function fetches all available properties from our simulated MLS data.
    How it works for the robot: This is like the robot opening its "House Listing Database"
    and reading out loud all the houses it knows about right now.

    - **response_model=List[Property]**: Specifies that the response will be a list of Property objects.
    """
    # Use the mock MLS service to get all active listings.
    return mls_service.get_all_listings()

@router.get("/{property_id}", response_model=Property)
async def get_property_by_id(property_id: UUID):
    """
    Endpoint to retrieve a single property by its unique ID.

    This function looks up a specific property using its unique identifier.
    How it works for the robot: This is like asking the robot, "Tell me about THIS specific house!"
    (pointing to it by its unique ID).

    - **property_id**: The unique identifier (UUID) of the property to retrieve.
    - **response_model=Property**: Specifies that the response will be a single Property object.
    - **raises HTTPException**: If the property is not found, a 404 Not Found error is returned.
    """
    # Use the mock MLS service to find the property by its ID.
    prop = mls_service.get_listing_by_id(property_id)
    # If the property is found, return it.
    if prop:
        return prop
    # If not found, raise an HTTP 404 error with a detail message.
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")

@router.post("/{property_id}/simulate-price-drop", response_model=Property)
async def simulate_property_price_drop(property_id: UUID, price_update: PriceUpdate):
    """
    Endpoint to simulate a price drop for a specific property.

    This endpoint is primarily for testing the price drop detection feature.
    It updates the price of an existing property in the simulated data.
    How it works for the robot: This is like telling the robot, "Hey, for THIS house, its new price is THIS much!"
    The robot then updates its records. This update is what would later trigger an automatic "nudge."

    - **property_id**: The unique identifier (UUID) of the property to update.
    - **price_update**: A PriceUpdate model containing the new_price. This ensures the price
      is correctly read from the request body.
    - **response_model=Property**: Specifies that the response will be the updated Property object.
    - **raises HTTPException**: If the property is not found or the price does not actually drop,
      a 400 Bad Request error is returned.
    """
    # Use the mock MLS service to simulate the price change.
    # We access the 'new_price' from the 'price_update' Pydantic object.
    updated_prop = mls_service.simulate_price_drop(property_id, price_update.new_price)
    # If the property was updated successfully (price actually dropped), return it.
    if updated_prop:
        return updated_prop
    # If the update failed (e.g., property not found, or new_price was not lower), raise an error.
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not simulate price drop or property not found.")