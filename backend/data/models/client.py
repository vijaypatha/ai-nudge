# ---
# File Path: backend/data/models/client.py
# Purpose: Defines the data structure for a Client.
# ---
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from uuid import UUID, uuid4

class Client(BaseModel):
    """Represents a client of the business owner."""
    id: UUID = Field(default_factory=uuid4)
    full_name: str
    email: str
    phone: str | None = None
    tags: List[str] = Field(default_factory=list)
    
    # This field holds the unstructured intel for our AI.
    preferences: Dict[str, Any] = Field(
        default_factory=dict,
        description="Client-specific preferences and intel for AI matchmaking."
    )
    
    last_interaction: str | None = None

    class Config:
        from_attributes = True

class ClientCreate(BaseModel):
    """Defines the data required to create a new client via the API."""
    full_name: str
    email: str
    phone: str | None = None
    tags: List[str] = []
    preferences: Dict[str, Any] = {}

class ClientUpdate(BaseModel):
    """Defines the fields that can be updated on a client."""
    preferences: Dict[str, Any]