# backend/data/models/campaign.py
# --- MODIFIED: Added 'matched_audience' to CampaignBriefing and enhanced MatchedClient.

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

class CoPilotAction(BaseModel):
    type: str
    label: str

# --- MODIFIED: Enhanced with match_score and match_reasons ---
class MatchedClient(BaseModel):
    """
    A Pydantic model representing a client matched to an opportunity.
    This is not a database table; it's used for data validation and structure.
    """
    client_id: UUID
    client_name: str
    match_score: int          # <-- NEW: The calculated score for the match.
    match_reasons: List[str]  # <-- NEW: Human-readable reasons for the score.

class CampaignBriefing(SQLModel, table=True):
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id", index=True)
    client_id: Optional[UUID] = Field(default=None, foreign_key="client.id", index=True)
    parent_message_id: Optional[UUID] = Field(default=None, foreign_key="message.id", index=True)
    is_plan: bool = Field(default=False, index=True)
    campaign_type: str = Field(index=True)
    headline: str
    key_intel: Dict[str, Any] = Field(sa_column=Column(JSON))
    
    # --- NEW: Added field to store the list of matched clients as JSON. ---
    # This aligns the model with the data being passed by nudge_engine.py.
    matched_audience: List[Dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON))
    
    original_draft: str
    status: CampaignStatus = Field(default=CampaignStatus.DRAFT, index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    parent_message: Optional["Message"] = Relationship(back_populates="ai_drafts")
    user: Optional["User"] = Relationship(back_populates="campaigns")
    client: Optional["Client"] = Relationship(back_populates="campaign_briefings")
    scheduled_messages: List["ScheduledMessage"] = Relationship(back_populates="parent_plan")

class CampaignUpdate(SQLModel):
    """Model for updating campaign briefings."""
    campaign_type: Optional[str] = None
    headline: Optional[str] = None
    key_intel: Optional[Dict[str, Any]] = None
    original_draft: Optional[str] = None
    status: Optional[CampaignStatus] = None

class RecommendationSlateResponse(BaseModel):
    id: UUID
    is_plan: bool
    campaign_type: str
    headline: str
    key_intel: Dict[str, Any]
    original_draft: str
    status: CampaignStatus

    class Config:
        from_attributes = True