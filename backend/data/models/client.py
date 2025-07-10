# File Path: backend/data/models/client.py
# --- DEFINITIVE FIX V4 ---
# 1. Made the 'email' field optional (nullable) to allow importing contacts
#    that only have a phone number, preventing database errors.

from typing import List, Dict, Any, Optional, TYPE_CHECKING
from uuid import UUID, uuid4
from sqlmodel import SQLModel, Field, Relationship, Column, JSON

if TYPE_CHECKING:
    from .message import ScheduledMessage, Message
    from .user import User

class Client(SQLModel, table=True):
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id", index=True)
    full_name: str
    
    # --- MODIFIED: email is now optional ---
    # The unique constraint only applies to non-NULL values, which is correct.
    email: Optional[str] = Field(default=None, unique=True, index=True)
    phone: Optional[str] = Field(default=None, index=True)
    
    ai_tags: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    user_tags: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    
    preferences: Dict[str, Any] = Field(sa_column=Column(JSON))
    last_interaction: Optional[str] = Field(default=None)
    
    user: "User" = Relationship(back_populates="clients")
    
    scheduled_messages: List["ScheduledMessage"] = Relationship(back_populates="client")
    messages: List["Message"] = Relationship(back_populates="client")


class ClientCreate(SQLModel):
    """
    This is the model used for creating new clients, including during import.
    """
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    ai_tags: List[str] = []
    user_tags: List[str] = []
    preferences: Dict[str, Any] = {}

class ClientUpdate(SQLModel):
    preferences: Dict[str, Any]

class ClientTagUpdate(SQLModel):
    """
    The key is 'user_tags' to match the frontend request.
    """
    user_tags: List[str]