# FILE: backend/data/models/feedback.py
# --- NEW FILE ---

from typing import List, Optional, TYPE_CHECKING
from uuid import UUID, uuid4
from datetime import datetime, timezone
from sqlalchemy import Column, JSON
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .client import Client

class NegativePreference(SQLModel, table=True):
    """
    Represents a user's explicit negative feedback. When a user dismisses a
    nudge for a client, we store the embedding of the dismissed opportunity here.
    This allows the AI to learn and avoid similar irrelevant suggestions in the future.
    """
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    client_id: UUID = Field(foreign_key="client.id", index=True)

    # The vector embedding of the opportunity/resource that was dismissed.
    dismissed_embedding: List[float] = Field(sa_column=Column(JSON))
    
    # The ID of the campaign/nudge that was dismissed.
    source_campaign_id: Optional[UUID] = Field(default=None, index=True)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Define the many-to-one relationship back to the Client
    client: "Client" = Relationship(back_populates="negative_preferences")