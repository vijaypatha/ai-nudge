# File Path: backend/data/models/client.py
# Purpose: Stores client information. This version adds a dedicated model for updating tags.
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
    tags: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    preferences: Dict[str, Any] = Field(sa_column=Column(JSON))
    last_interaction: Optional[str] = Field(default=None)
    
    scheduled_messages: List["ScheduledMessage"] = Relationship(back_populates="client")

    messages: List["Message"] = Relationship(back_populates="client")


class ClientCreate(SQLModel):
    full_name: str
    email: str
    phone: Optional[str] = None
    tags: List[str] = []
    preferences: Dict[str, Any] = {}

class ClientUpdate(SQLModel):
    preferences: Dict[str, Any]

class ClientTagUpdate(SQLModel):
    """
    (New Data Model) Defines the schema for updating only the tags for a client.
    """
    tags: List[str]