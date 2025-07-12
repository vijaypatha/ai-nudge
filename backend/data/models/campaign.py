# File Path: backend/data/models/campaign.py
# --- MODIFIED: Added a Pydantic model for the new Co-Pilot actions. ---

from typing import List, Dict, Any, Optional, TYPE_CHECKING
from uuid import UUID, uuid4
from datetime import datetime, timezone
from enum import Enum
from pydantic import BaseModel
from sqlmodel import SQLModel, Field, Relationship, Column, JSON

if TYPE_CHECKING:
    from .user import User
    from .client import Client
    from .message import Message, ScheduledMessage

class CampaignStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

# --- NEW: Pydantic model for structured co-pilot actions. ---
class CoPilotAction(BaseModel):
    type: str # e.g., "UPDATE_PLAN", "END_PLAN", "RESUME_PLAN"
    label: str # e.g., "Update the Plan..."

class MatchedClient(BaseModel):
    client_id: UUID
    client_name: str
    match_score: int
    match_reason: str

class CampaignBriefing(SQLModel, table=True):
    """(Database Table) The core campaign and recommendation slate container."""
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id")
    client_id: Optional[UUID] = Field(default=None, foreign_key="client.id", index=True)
    parent_message_id: Optional[UUID] = Field(default=None, foreign_key="message.id", index=True)
    is_plan: bool = Field(default=False, index=True)
    campaign_type: str = Field(index=True)
    headline: str
    key_intel: Dict[str, Any] = Field(sa_column=Column(JSON))
    listing_url: Optional[str] = Field(default=None)
    original_draft: str
    edited_draft: Optional[str] = Field(default=None)
    matched_audience: List[Dict[str, Any]] = Field(sa_column=Column(JSON))
    sent_messages: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    triggering_event_id: UUID
    status: CampaignStatus = Field(default=CampaignStatus.DRAFT, index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    user: Optional["User"] = Relationship(back_populates="campaigns")
    client: Optional["Client"] = Relationship(back_populates="campaign_briefings")
    parent_message: Optional["Message"] = Relationship(back_populates="ai_draft")
    scheduled_messages: List["ScheduledMessage"] = Relationship(back_populates="parent_plan")

class CampaignUpdate(SQLModel):
    campaign_type: Optional[str] = None
    headline: Optional[str] = None
    key_intel: Optional[Dict[str, Any]] = None
    original_draft: Optional[str] = None
    matched_audience: Optional[List[Dict[str, Any]]] = None
    status: Optional[CampaignStatus] = None

class RecommendationSlateResponse(BaseModel):
    """Pydantic model for serializing a CampaignBriefing for API responses."""
    id: UUID
    user_id: UUID
    client_id: Optional[UUID]
    parent_message_id: Optional[UUID]
    campaign_type: str
    headline: str
    key_intel: Dict[str, Any]
    status: CampaignStatus
    created_at: datetime
    is_plan: bool

    class Config:
        from_attributes = True