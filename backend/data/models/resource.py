# File Path: backend/data/models/resource.py
# --- NEW FILE: Defines the generic Resource model for our vertical-agnostic architecture.

from typing import Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Column, JSON

class Resource(SQLModel, table=True):
    """
    (Database Table) A generic, flexible model to represent any type of entity
    a user might work with, from a real estate property to a vehicle or a rental venue.
    This model is the key to making our platform vertical-agnostic.
    """
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id", index=True)
    entity_id: Optional[str] = Field(default=None, index=True)

    
    # The type of resource, e.g., "property", "vehicle", "venue".
    resource_type: str = Field(index=True)
    
    # The current status of the resource, e.g., "active", "sold", "draft".
    status: str = Field(index=True)
    
    # A flexible JSON field to store all vertical-specific data.
    # For a "property": {"address": "...", "price": 100000, "amenities": ["pool"]}
    # For a "vehicle": {"make": "Toyota", "model": "Camry", "year": 2023, "price": 25000}
    attributes: Dict[str, Any] = Field(sa_column=Column(JSON))
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column_kwargs={"onupdate": lambda: datetime.now(timezone.utc)}
    )

class ResourceCreate(SQLModel):
    """Pydantic model for creating a new resource via the API."""
    resource_type: str
    status: str
    attributes: Dict[str, Any]

class ResourceUpdate(SQLModel):
    """Pydantic model for updating an existing resource via the API."""
    status: Optional[str] = None
    attributes: Optional[Dict[str, Any]] = None