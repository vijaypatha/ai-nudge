# File Path: backend/data/models/portal.py
# Purpose: Defines the database models for the interactive client portal.

from typing import Optional, TYPE_CHECKING
from uuid import UUID, uuid4
from datetime import datetime, timezone
from enum import Enum
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, Text

if TYPE_CHECKING:
    from .user import User
    from .client import Client
    from .resource import Resource

class CommenterType(str, Enum):
    AGENT = "agent"
    CLIENT = "client"

class PortalComment(SQLModel, table=True):
    """(Data Model) Represents a comment made within the client portal on a resource."""
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id", index=True)
    client_id: UUID = Field(foreign_key="client.id", index=True)
    resource_id: UUID = Field(foreign_key="resource.id", index=True)
    
    commenter_type: CommenterType
    comment_text: str
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Relationships
    user: "User" = Relationship()
    client: "Client" = Relationship(back_populates="portal_comments")
    resource: "Resource" = Relationship(back_populates="portal_comments")

class PortalLink(SQLModel, table=True):
    """
    (Data Model) Stores a mapping between a short, user-friendly ID and a long, secure JWT.
    This creates clean, shareable URLs for the client portal.
    """
    id: str = Field(primary_key=True)  # A short, random, URL-safe ID
    token: str = Field(sa_column=Column(Text))  # The full, long JWT
    
    # Foreign keys for tracking and potential future features
    campaign_id: UUID = Field(foreign_key="campaignbriefing.id", index=True)
    client_id: UUID = Field(foreign_key="client.id", index=True)
    user_id: UUID = Field(foreign_key="user.id", index=True)

    # Timestamps for management and security
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime
    
    is_active: bool = Field(default=True, index=True)