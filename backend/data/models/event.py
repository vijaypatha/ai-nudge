# File Path: backend/data/models/event.py
# --- CORRECTED: Updated the foreign key to point to the new 'resource' table.

from typing import Dict, Any, Optional, TYPE_CHECKING
from uuid import UUID, uuid4
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Column, JSON, Relationship

# --- MODIFIED: Import Resource for the new relationship ---
if TYPE_CHECKING:
    from .resource import Resource

class MarketEvent(SQLModel, table=True):
    """Represents a persistent event from an external data source (e.g., MLS)."""
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    event_type: str = Field(index=True)
    market_area: str
    entity_type: str
    
    # --- MODIFIED: Foreign key now points to the generic 'resource.id' ---
    # This resolves the NoReferencedTableError by linking events to our new,
    # flexible Resource model instead of the deleted Property model.
    entity_id: UUID = Field(foreign_key="resource.id")
    
    payload: Dict[str, Any] = Field(sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)

    # --- ADDED: Defines the relationship for ORM capabilities ---
    resource: Optional["Resource"] = Relationship()