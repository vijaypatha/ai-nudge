# File Path: backend/data/models/client.py
# --- DEFINITIVE FIX V3 for Dynamic Tagging ---
# 1. Removed the 'alias' from 'ai_tags' that was causing JSON serialization conflicts.
# 2. Standardized the 'ClientTagUpdate' model to use 'user_tags' for clarity and consistency.

from typing import List, Dict, Any, Optional, TYPE_CHECKING
from uuid import UUID, uuid4
from sqlmodel import SQLModel, Field, Relationship, Column, JSON

if TYPE_CHECKING:
    from .message import ScheduledMessage, Message

class Client(SQLModel, table=True):
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    full_name: str
    email: str = Field(unique=True, index=True)
    phone: Optional[str] = Field(default=None, index=True)
    
    # --- DYNAMIC TAGGING FIX ---
    # REMOVED: `alias="tags"` which caused the serialization error.
    # The frontend will now correctly receive both `ai_tags` and `user_tags`.
    ai_tags: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    user_tags: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    
    preferences: Dict[str, Any] = Field(sa_column=Column(JSON))
    last_interaction: Optional[str] = Field(default=None)
    
    scheduled_messages: List["ScheduledMessage"] = Relationship(back_populates="client")
    messages: List["Message"] = Relationship(back_populates="client")


class ClientCreate(SQLModel):
    full_name: str
    email: str
    phone: Optional[str] = None
    ai_tags: List[str] = []
    user_tags: List[str] = []
    preferences: Dict[str, Any] = {}

class ClientUpdate(SQLModel):
    preferences: Dict[str, Any]

class ClientTagUpdate(SQLModel):
    """
    (CORRECTED) The key is now 'user_tags' to match the frontend request.
    """
    user_tags: List[str]