# File Path: backend/data/models/campaign.py
# --- CORRECTED: Added a dedicated Pydantic model for the API response to fix serialization errors.

from typing import List, Dict, Any, Optional, TYPE_CHECKING
from uuid import UUID, uuid4
from datetime import datetime, timezone
from pydantic import BaseModel
from sqlmodel import SQLModel, Field, Relationship, Column, JSON

if TYPE_CHECKING:
    from .user import User
    from .client import Client
    from .message import Message

class MatchedClient(BaseModel):
    client_id: UUID
    client_name: str
    match_score: int
    match_reason: str

class CampaignBriefing(SQLModel, table=True):
    """
    (Database Table Model) The core "campaign-in-a-box" and "Recommendation Slate".
    """
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id")
    client_id: Optional[UUID] = Field(default=None, foreign_key="client.id", index=True)
    parent_message_id: Optional[UUID] = Field(default=None, foreign_key="message.id", index=True)
    campaign_type: str = Field(index=True)
    headline: str
    key_intel: Dict[str, Any] = Field(sa_column=Column(JSON))
    listing_url: Optional[str] = Field(default=None)
    original_draft: str
    edited_draft: Optional[str] = Field(default=None)
    matched_audience: List[Dict[str, Any]] = Field(sa_column=Column(JSON))
    sent_messages: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    triggering_event_id: UUID
    status: str = Field(default="active", index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    user: Optional["User"] = Relationship(back_populates="campaigns")
    client: Optional["Client"] = Relationship(back_populates="campaign_briefings")
    parent_message: Optional["Message"] = Relationship(back_populates="ai_draft")


class CampaignUpdate(SQLModel):
    """Model for updating campaign briefings."""
    campaign_type: Optional[str] = None
    headline: Optional[str] = None
    key_intel: Optional[Dict[str, Any]] = None
    original_draft: Optional[str] = None
    matched_audience: Optional[List[Dict[str, Any]]] = None
    status: Optional[str] = None

# --- NEW: API Response Model for Recommendation Slates ---
# This is a pure Pydantic model, NOT an SQLModel. It defines a clean, safe
# structure for API responses, preventing serialization errors from database relationships.
class RecommendationSlateResponse(BaseModel):
    id: UUID
    user_id: UUID
    client_id: Optional[UUID]
    parent_message_id: Optional[UUID]
    campaign_type: str
    headline: str
    key_intel: Dict[str, Any] # This holds the list of recommendation objects
    status: str
    created_at: datetime

    class Config:
        # This allows the Pydantic model to be created from the CampaignBriefing ORM object.
        from_attributes = True