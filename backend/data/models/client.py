# File Path: backend/data/models/client.py
# --- MODIFIED: Added an optional 'notes' field to store AI-generated intel.

from typing import List, Dict, Any, Optional, TYPE_CHECKING
from uuid import UUID, uuid4
# --- MODIFIED: Import Text for longer form notes ---
from sqlalchemy import Column, Text
from sqlmodel import SQLModel, Field, Relationship, JSON

if TYPE_CHECKING:
    from .message import ScheduledMessage, Message
    from .user import User
    from .campaign import CampaignBriefing

class Client(SQLModel, table=True):
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id", index=True)
    full_name: str
    
    email: Optional[str] = Field(default=None, unique=True, index=True)
    phone: Optional[str] = Field(default=None, index=True)
    
    # --- NEW: Field to store notes and insights about the client ---
    notes: Optional[str] = Field(default=None, sa_column=Column(Text))
    
    ai_tags: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    user_tags: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    
    preferences: Dict[str, Any] = Field(sa_column=Column(JSON))
    last_interaction: Optional[str] = Field(default=None)
    timezone: Optional[str] = Field(default=None)

    
    user: "User" = Relationship(back_populates="clients")
    
    scheduled_messages: List["ScheduledMessage"] = Relationship(back_populates="client")
    messages: List["Message"] = Relationship(back_populates="client")
    campaign_briefings: List["CampaignBriefing"] = Relationship(back_populates="client")


class ClientCreate(SQLModel):
    """
    This is the model used for creating new clients, including during import.
    """
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    # --- MODIFIED: Added notes field ---
    notes: Optional[str] = None
    ai_tags: List[str] = []
    user_tags: List[str] = []
    preferences: Dict[str, Any] = {}

class ClientUpdate(SQLModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    notes: Optional[str] = None
    user_tags: Optional[List[str]] = None
    preferences: Optional[Dict[str, Any]] = None
    timezone: Optional[str] = None

class ClientTagUpdate(SQLModel):
    """
    The key is 'user_tags' to match the frontend request.
    """
    user_tags: List[str]