# File Path: backend/data/models/message.py
# Purpose: Defines data models for all messages.
# --- UPDATED to include a universal 'Message' log table ---

from typing import Optional, TYPE_CHECKING, List
from uuid import UUID, uuid4
from datetime import datetime, timezone
from enum import Enum
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .client import Client

class MessageStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RECEIVED = "received" # For inbound messages

# --- NEW: Added to distinguish message direction ---
class MessageDirection(str, Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"

# --- NEW: Universal Message Log Table ---
class Message(SQLModel, table=True):
    """
    (Database Table) A log of every single message sent or received.
    This provides a complete history for any conversation.
    """
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    client_id: UUID = Field(foreign_key="client.id", index=True)
    content: str
    direction: MessageDirection = Field(index=True)
    status: MessageStatus
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)
    
    # Defines the many-to-one relationship with the Client table
    client: Optional["Client"] = Relationship(back_populates="messages")


class ScheduledMessage(SQLModel, table=True):
    """
    (Database Table) Stores messages scheduled to be sent in the future.
    """
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
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

# --- API Schemas ---
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
