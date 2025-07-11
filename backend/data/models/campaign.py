# File Path: backend/data/models/campaign.py
# --- MODIFIED: Evolved CampaignBriefing to serve as the "Recommendation Slate" model.

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
    (Database Table Model) The core "campaign-in-a-box".
    ---
    MODIFIED to also function as the "Recommendation Slate" for the AI co-pilot.
    It holds a set of recommendations generated in response to an event, like an incoming message.
    """
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id")
    client_id: Optional[UUID] = Field(default=None, foreign_key="client.id", index=True)
    parent_message_id: Optional[UUID] = Field(default=None, foreign_key="message.id", index=True)

    campaign_type: str = Field(index=True) # e.g., "inbound_response_recommendation"
    headline: str
    
    # This field now stores the structured list of recommendation objects.
    key_intel: Dict[str, Any] = Field(sa_column=Column(JSON))
    
    listing_url: Optional[str] = Field(default=None)
    original_draft: str # This can hold the primary text draft from the recommendations.
    edited_draft: Optional[str] = Field(default=None)
    matched_audience: List[Dict[str, Any]] = Field(sa_column=Column(JSON))
    sent_messages: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    triggering_event_id: UUID
    
    # The status now reflects the lifecycle of the recommendation slate.
    # active: The current, actionable slate for the UI.
    # completed: The user acted on a recommendation from this slate.
    # stale: A new event occurred, making this slate outdated.
    # new: A market-event campaign that has not been reviewed.
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