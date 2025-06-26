
# scheduledmessage - Stores scheduled messages with foreign key to client
from typing import Optional, TYPE_CHECKING
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

class ScheduledMessage(SQLModel, table=True):
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    client_id: UUID = Field(foreign_key="client.id")
    content: str
    scheduled_at: datetime = Field(index=True)
    status: MessageStatus = Field(default=MessageStatus.PENDING, index=True)
    sent_at: Optional[datetime] = Field(default=None)
    error_message: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
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
