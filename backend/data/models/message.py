# backend/data/models/message.py
# --- FINAL, CORRECTED VERSION ---

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

class MessageSource(str, Enum):
    MANUAL = "manual"
    SCHEDULED = "scheduled"
    FAQ_AUTO_RESPONSE = "faq_auto_response"
    INSTANT_NUDGE = "instant_nudge" # Added for Instant Nudge attribution

class MessageSenderType(str, Enum):
    USER = "user"
    AI = "ai" # Added for AI-generated messages
    SYSTEM = "system"

class Message(SQLModel, table=True):
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id", index=True)
    client_id: UUID = Field(foreign_key="client.id", index=True)
    content: str
    direction: MessageDirection = Field(index=True)
    status: MessageStatus
    source: MessageSource = Field(default=MessageSource.MANUAL, index=True)
    sender_type: MessageSenderType = Field(default=MessageSenderType.USER, index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)
    originally_scheduled_at: Optional[datetime] = Field(default=None, index=True)  # Store original scheduled time
    client: Optional["Client"] = Relationship(back_populates="messages")
    user: Optional["User"] = Relationship(back_populates="messages")
    ai_drafts: List["CampaignBriefing"] = Relationship(back_populates="parent_message")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() + 'Z' if v.tzinfo is None else v.isoformat()
        }

class ScheduledMessage(SQLModel, table=True):
    __tablename__ = "scheduledmessage"  # Explicitly define the table name

    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id", index=True)
    client_id: UUID = Field(foreign_key="client.id")
    parent_plan_id: Optional[UUID] = Field(default=None, foreign_key="campaignbriefing.id", index=True)
    content: str
    scheduled_at_utc: datetime = Field(index=True) # Renamed for clarity that this is always UTC
    timezone: str = Field(index=True) # Added to store the original scheduling timezone
    status: MessageStatus = Field(default=MessageStatus.PENDING, index=True)
    sent_at: Optional[datetime] = Field(default=None)
    error_message: Optional[str] = Field(default=None)
    celery_task_id: Optional[str] = Field(default=None, index=True) # Added to manage the Celery task
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    playbook_touchpoint_id: Optional[str] = Field(default=None, index=True)
    is_recurring: bool = Field(default=False, index=True)

    client: Optional["Client"] = Relationship(back_populates="scheduled_messages")
    user: Optional["User"] = Relationship(back_populates="scheduled_messages")
    parent_plan: Optional["CampaignBriefing"] = Relationship(back_populates="scheduled_messages")

# Replace with this updated Pydantic model
class MessageWithDraft(BaseModel):
    """API model for a Message that includes its optional AI suggestions."""
    id: UUID
    user_id: UUID
    client_id: UUID
    content: str
    direction: MessageDirection
    status: MessageStatus
    # --- NEW FIELDS START ---
    source: MessageSource
    sender_type: MessageSenderType
    # --- NEW FIELDS END ---
    created_at: datetime
    # --- DEFINITIVE FIX: Updated to reflect the one-to-many relationship ---
    ai_drafts: List["RecommendationSlateResponse"] = []

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() + 'Z' if v.tzinfo is None else v.isoformat()
        }

class ScheduledMessageCreate(SQLModel):
    client_id: UUID
    content: str
    scheduled_at_local: datetime # Frontend sends local time
    timezone: str # Frontend sends timezone string e.g., "America/New_York"

class SendMessageImmediate(SQLModel):
    client_id: UUID
    content: str

class IncomingMessage(SQLModel):
    client_id: UUID
    content: str

class ScheduledMessageUpdate(SQLModel):
    content: Optional[str] = None
    scheduled_at_local: Optional[datetime] = None # Frontend sends local time
    timezone: Optional[str] = None