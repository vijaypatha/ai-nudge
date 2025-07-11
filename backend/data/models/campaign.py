# File Path: backend/data/models/campaign.py
# Purpose: Defines the data model for campaign briefings.
# This is the FINAL CORRECTED version to fix all JSON serialization errors.

from typing import List, Dict, Any, Optional, TYPE_CHECKING
from uuid import UUID, uuid4
from datetime import datetime, timezone
from pydantic import BaseModel
from sqlmodel import SQLModel, Field, Relationship, Column, JSON

if TYPE_CHECKING:
    from .user import User
    from .client import Client # Import Client model for type hinting

# This remains a Pydantic model for validating API data structures.
class MatchedClient(BaseModel):
    client_id: UUID
    client_name: str
    match_score: int
    match_reason: str

class CampaignBriefing(SQLModel, table=True):
    """
    (Database Table Model) The core "campaign-in-a-box".
    """
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id")
    client_id: Optional[UUID] = Field(default=None, foreign_key="client.id", index=True) # ADDED: Link to client
    campaign_type: str = Field(index=True)
    headline: str
    key_intel: Dict[str, Any] = Field(sa_column=Column(JSON))
    listing_url: Optional[str] = Field(default=None)
    original_draft: str
    edited_draft: Optional[str] = Field(default=None)
    # CORRECTED: The database model now uses a simple List of Dictionaries.
    # This is a native JSON type and solves the serialization error.
    matched_audience: List[Dict[str, Any]] = Field(sa_column=Column(JSON))
    sent_messages: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    triggering_event_id: UUID
    status: str = Field(default="new", index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    user: Optional["User"] = Relationship(back_populates="campaigns")
    client: Optional["Client"] = Relationship(back_populates="campaign_briefings") # ADDED: Relationship to client

class CampaignUpdate(SQLModel):
    """Model for updating campaign briefings."""
    campaign_type: Optional[str] = None
    headline: Optional[str] = None
    key_intel: Optional[Dict[str, Any]] = None
    original_draft: Optional[str] = None
    matched_audience: Optional[List[Dict[str, Any]]] = None
    status: Optional[str] = None