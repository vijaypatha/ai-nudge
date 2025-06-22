# ---
# File Path: backend/data/models/event.py
# Purpose: Defines a generic data model for market events.
# ---
from pydantic import BaseModel, Field
from typing import Dict, Any, Literal
from uuid import UUID, uuid4
from datetime import datetime, timezone

EventType = Literal["price_drop", "new_listing", "status_change"]
EntityType = Literal["PROPERTY"]

class MarketEvent(BaseModel):
    """Represents an event from an external data source (e.g., MLS)."""
    id: UUID = Field(default_factory=uuid4)
    event_type: EventType
    market_area: str
    entity_type: EntityType
    entity_id: UUID
    payload: Dict[str, Any]
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Config:
        from_attributes = True