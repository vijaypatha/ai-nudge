
# campaignbriefing - Stores campaign data with foreign key to user


from typing import List, Dict, Any, Optional, TYPE_CHECKING
from uuid import UUID, uuid4
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Relationship, Column, JSON

if TYPE_CHECKING:
    from .user import User

class MatchedClient(SQLModel):
    client_id: UUID
    client_name: str
    match_score: int
    match_reason: str

class CampaignBriefing(SQLModel, table=True):
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id")
    campaign_type: str = Field(index=True)
    headline: str
    key_intel: Dict[str, Any] = Field(sa_column=Column(JSON))
    listing_url: Optional[str] = Field(default=None)
    original_draft: str
    edited_draft: Optional[str] = Field(default=None)
    matched_audience: List[MatchedClient] = Field(sa_column=Column(JSON))
    sent_messages: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    triggering_event_id: UUID
    status: str = Field(default="new", index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    user: Optional["User"] = Relationship(back_populates="campaigns")

class CampaignUpdate(SQLModel):
    """
    Defines the schema for updating a campaign. Uses SQLModel for consistency
    with the rest of our data models.
    """
    edited_draft: Optional[str] = None
    status: Optional[str] = None