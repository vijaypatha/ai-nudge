# marketevent - Stores market events with foreign key to property

    
from typing import Dict, Any, Optional, TYPE_CHECKING
from uuid import UUID, uuid4
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Column, JSON, Relationship

if TYPE_CHECKING:
    from .property import Property

class MarketEvent(SQLModel, table=True):
    """Represents a persistent event from an external data source (e.g., MLS)."""
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    event_type: str = Field(index=True)
    market_area: str
    entity_type: str
    
    # --- Foreign Key for Relationship ---
    entity_id: UUID = Field(foreign_key="property.id")
    
    payload: Dict[str, Any] = Field(sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)
