# backend/data/models/property.py

from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List
import uuid

class Property(BaseModel):
    """
    Represents a real estate property listing.
    This model defines the structure of property data.
    """
    # Unique identifier for the property.
    id: uuid.UUID = Field(default_factory=uuid.uuid4, description="Unique ID for the property.")

    # Main address of the property.
    address: str = Field(min_length=5, description="Full address of the property.")

    # Current listing price.
    price: float = Field(gt=0, description="Current listing price of the property.")

    # Number of bedrooms.
    bedrooms: Optional[int] = Field(None, ge=0, description="Number of bedrooms in the property.")

    # Number of bathrooms. Can be float for half-baths.
    bathrooms: Optional[float] = Field(None, ge=0, description="Number of bathrooms in the property.")

    # Square footage of the property.
    square_footage: Optional[int] = Field(None, gt=0, description="Square footage of the property.")

    # Year the property was built.
    year_built: Optional[int] = Field(None, ge=1800, description="Year the property was built.")

    # Type of property (e.g., 'house', 'condo', 'townhouse').
    property_type: Optional[str] = Field(None, description="Type of property (e.g., 'house', 'condo').")

    # URL to the main listing on an external site (like MLS, Redfin, Zillow).
    listing_url: Optional[HttpUrl] = Field(None, description="URL to the original listing.")

    # List of image URLs for the property.
    image_urls: List[HttpUrl] = Field(default_factory=list, description="List of URLs to property images.")

    # Status of the listing (e.g., 'active', 'pending', 'sold', 'price_reduced').
    status: str = Field("active", description="Current status of the property listing.")

    # Timestamp for when the listing was last updated (e.g., for price changes).
    last_updated: str = Field(description="Timestamp of the last update to the listing data.")


class PropertyCreate(BaseModel):
    """
    Data required to create a new property listing.
    ID and default status/last_updated are handled by the 
    """
    address: str = Field(min_length=5, description="Full address of the property.")
    price: float = Field(gt=0, description="Current listing price of the property.")
    bedrooms: Optional[int] = Field(None, ge=0, description="Number of bedrooms in the property.")
    bathrooms: Optional[float] = Field(None, ge=0, description="Number of bathrooms in the property.")
    square_footage: Optional[int] = Field(None, gt=0, description="Square footage of the property.")
    year_built: Optional[int] = Field(None, ge=1800, description="Year the property was built.")
    property_type: Optional[str] = Field(None, description="Type of property (e.g., 'house', 'condo').")
    listing_url: Optional[HttpUrl] = Field(None, description="URL to the original listing.")
    image_urls: List[HttpUrl] = Field(default_factory=list, description="List of URLs to property images.")

class PriceUpdate(BaseModel):
    """
    Model for updating the price of a property via a POST request body.
    """
    new_price: float = Field(gt=0, description="The new price for the property.")
