# File Path: backend/data/models/campaign.py
# --- MODIFIED ---

from typing import List, Dict, Any, Optional, TYPE_CHECKING
from uuid import UUID, uuid4
from datetime import datetime, timezone
from enum import Enum  # --- ADDED: For status enum
from pydantic import BaseModel
from sqlmodel import SQLModel, Field, Relationship, Column, JSON

if TYPE_CHECKING:
    from .user import User
    from .client import Client
    from .message import Message, ScheduledMessage # --- ADDED

# --- ADDED: A clear Enum for the status of a plan or campaign briefing. ---
class CampaignStatus(str, Enum):
    DRAFT = "draft"         # An AI-suggested plan, not yet approved by the user.
    ACTIVE = "active"       # A plan that is currently running with scheduled messages.
    PAUSED = "paused"       # An active plan that was interrupted by a client reply.
    COMPLETED = "completed"   # A plan that finished successfully or a slate that was actioned.
    CANCELLED = "cancelled"   # A plan or slate that was dismissed by the user.

class MatchedClient(BaseModel):
    client_id: UUID
    client_name: str
    match_score: int
    match_reason: str

class CampaignBriefing(SQLModel, table=True):
    """
    (Database Table) The core "campaign-in-a-box" and "Recommendation Slate".
    --- MODIFIED: Now also serves as the container for an "Adaptive Nudge Plan". ---
    """
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id")
    client_id: Optional[UUID] = Field(default=None, foreign_key="client.id", index=True)
    parent_message_id: Optional[UUID] = Field(default=None, foreign_key="message.id", index=True)

    # --- ADDED: Flag to distinguish between a single nudge and a multi-step plan. ---
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

    # --- MODIFIED: Uses the new CampaignStatus Enum for type safety and defaults to DRAFT. ---
    status: CampaignStatus = Field(default=CampaignStatus.DRAFT, index=True)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    user: Optional["User"] = Relationship(back_populates="campaigns")
    client: Optional["Client"] = Relationship(back_populates="campaign_briefings")
    parent_message: Optional["Message"] = Relationship(back_populates="ai_draft")

    # --- ADDED: A plan can have many scheduled messages. ---
    scheduled_messages: List["ScheduledMessage"] = Relationship(back_populates="parent_plan")

class CampaignUpdate(SQLModel):
    """Model for updating campaign briefings."""
    campaign_type: Optional[str] = None
    headline: Optional[str] = None
    key_intel: Optional[Dict[str, Any]] = None
    original_draft: Optional[str] = None
    matched_audience: Optional[List[Dict[str, Any]]] = None
    status: Optional[CampaignStatus] = None # --- MODIFIED: Uses the Enum.

class RecommendationSlateResponse(BaseModel):
    """
    --- MODIFIED: This model is now used for both single slates and multi-step plans. ---
    """
    id: UUID
    user_id: UUID
    client_id: Optional[UUID]
    parent_message_id: Optional[UUID]
    campaign_type: str
    headline: str
    key_intel: Dict[str, Any]
    status: CampaignStatus # --- MODIFIED: Uses the Enum.
    created_at: datetime
    is_plan: bool # --- ADDED

    class Config:
        from_attributes = True