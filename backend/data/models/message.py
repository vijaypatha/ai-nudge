# File Path: backend/data/models/message.py
# --- MODIFIED ---

from typing import Optional, TYPE_CHECKING, List
from uuid import UUID, uuid4
from datetime import datetime, timezone
from enum import Enum
from sqlmodel import SQLModel, Field, Relationship
from pydantic import BaseModel

if TYPE_CHECKING:
    from .client import Client
    from .user import User
    from .campaign import CampaignBriefing, RecommendationSlateResponse

class MessageStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RECEIVED = "received"

class MessageDirection(str, Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"

class Message(SQLModel, table=True):
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id", index=True)
    client_id: UUID = Field(foreign_key="client.id", index=True)
    content: str
    direction: MessageDirection = Field(index=True)
    status: MessageStatus
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)
    client: Optional["Client"] = Relationship(back_populates="messages")
    user: Optional["User"] = Relationship(back_populates="messages")
    # --- MODIFIED: ai_draft now relates to CampaignBriefing instead of RecommendationSlateResponse ---
    ai_draft: Optional["CampaignBriefing"] = Relationship(back_populates="parent_message", sa_relationship_kwargs={'uselist': False})

class ScheduledMessage(SQLModel, table=True):
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id", index=True)
    client_id: UUID = Field(foreign_key="client.id")

    # --- ADDED: Foreign key to link this scheduled message to an overarching plan. ---
    parent_plan_id: Optional[UUID] = Field(default=None, foreign_key="campaignbriefing.id", index=True)

    content: str
    scheduled_at: datetime = Field(index=True)
    status: MessageStatus = Field(default=MessageStatus.PENDING, index=True)
    sent_at: Optional[datetime] = Field(default=None)
    error_message: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    playbook_touchpoint_id: Optional[str] = Field(default=None, index=True)
    is_recurring: bool = Field(default=False, index=True)

    client: Optional["Client"] = Relationship(back_populates="scheduled_messages")
    user: Optional["User"] = Relationship(back_populates="scheduled_messages")

    # --- ADDED: Relationship to the parent CampaignBriefing (the plan). ---
    parent_plan: Optional["CampaignBriefing"] = Relationship(back_populates="scheduled_messages")


# --- MODIFIED: MessageWithDraft now expects ai_draft to be a RecommendationSlateResponse ---
class MessageWithDraft(BaseModel):
    """API model for a Message that includes its optional AI draft."""
    id: UUID
    user_id: UUID
    client_id: UUID
    content: str
    direction: MessageDirection
    status: MessageStatus
    created_at: datetime
    ai_draft: Optional["RecommendationSlateResponse"] = None

    class Config:
        from_attributes = True


class ScheduledMessageCreate(SQLModel):
    client_id: UUID
    content: str
    scheduled_at: datetime

class SendMessageImmediate(SQLModel):
    client_id: UUID
    content: str

class IncomingMessage(SQLModel):
    client_id: UUID
    content: str

class ScheduledMessageUpdate(SQLModel):
    content: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    status: Optional[MessageStatus] = None
