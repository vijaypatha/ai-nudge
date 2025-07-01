#property - Stores property listings with status/address indexes

from typing import Optional, List
from uuid import UUID, uuid4
from datetime import datetime, timezone # Import datetime and timezone
from sqlmodel import SQLModel, Field, Column, JSON

# --- Table Model ---
class Property(SQLModel, table=True):
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    address: str = Field(index=True)
    price: float
    bedrooms: Optional[int] = Field(default=None)
    bathrooms: Optional[float] = Field(default=None)
    square_footage: Optional[int] = Field(default=None)
    year_built: Optional[int] = Field(default=None)
    property_type: Optional[str] = Field(default=None)
    listing_url: Optional[str] = Field(default=None)
    image_urls: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    status: str = Field(default="active", index=True)
    
    # --- FIX: Add a default_factory to prevent NotNullViolation ---
    # This ensures the 'last_updated' field always has a value when a new
    # property is created, making the model more robust.
    last_updated: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

# --- API Schemas ---
class PropertyCreate(SQLModel):
    """Data required to create a new property listing."""
    address: str
    price: float
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    square_footage: Optional[int] = None
    year_built: Optional[int] = None
    property_type: Optional[str] = None
    listing_url: Optional[str] = None
    image_urls: List[str] = []

class PriceUpdate(SQLModel):
    """Model for updating the price of a property."""
    new_price: float
