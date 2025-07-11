# File Path: backend/data/models/message.py
# Purpose: Defines data models for all messages.
# --- UPDATED with a fix for Pydantic schema generation ---

from typing import Optional, TYPE_CHECKING, List
from uuid import UUID, uuid4
from datetime import datetime, timezone
from enum import Enum
from sqlmodel import SQLModel, Field, Relationship
# --- ADDED: Import Pydantic's BaseModel for a clean API model ---
from pydantic import BaseModel

# Forward references for database relationships
if TYPE_CHECKING:
    from .client import Client
    from .user import User
    from .campaign import CampaignBriefing

class MessageStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RECEIVED = "received"

class MessageDirection(str, Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"

# This is the pure DATABASE model.
class Message(SQLModel, table=True):
    """
    (Database Table) A log of every single message sent or received.
    """
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id", index=True)
    client_id: UUID = Field(foreign_key="client.id", index=True)
    content: str
    direction: MessageDirection = Field(index=True)
    status: MessageStatus
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)
    
    # SQLAlchemy relationships for internal ORM use. Pydantic struggles with these.
    client: Optional["Client"] = Relationship(back_populates="messages")
    user: Optional["User"] = Relationship(back_populates="messages")
    ai_draft: Optional["CampaignBriefing"] = Relationship(back_populates="parent_message", sa_relationship_kwargs={'uselist': False})


# This is the pure DATABASE model.
class ScheduledMessage(SQLModel, table=True):
    """
    (Database Table) Stores messages scheduled to be sent in the future.
    """
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id", index=True)
    client_id: UUID = Field(foreign_key="client.id")
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


# --- API Schemas ---
# Import CampaignBriefing here for the Pydantic model to use.
from .campaign import CampaignBriefing

# --- MODIFIED: Redefined MessageWithDraft as a pure Pydantic model ---
# This fixes the error by creating a separate, clean model for the API response.
# It does NOT inherit from the Message SQLModel, preventing the relationship error.
class MessageWithDraft(BaseModel):
    """API model for a Message that includes its optional AI draft."""
    id: UUID
    user_id: UUID
    client_id: UUID
    content: str
    direction: MessageDirection
    status: MessageStatus
    created_at: datetime
    ai_draft: Optional[CampaignBriefing] = None

    # This allows the Pydantic model to be created from the ORM/database model
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