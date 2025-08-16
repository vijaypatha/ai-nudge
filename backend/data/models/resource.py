# File Path: backend/data/models/resource.py
# --- NEW FILE: Defines the generic Resource model for our vertical-agnostic architecture.

from enum import Enum
from typing import List, Optional, TYPE_CHECKING, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Relationship, Column, JSON
from .portal import PortalComment

if TYPE_CHECKING:
    from .user import User
    from .campaign import CampaignBriefing

class ResourceType(str, Enum):
    PROPERTY = "property"
    WEB_CONTENT = "web_content"
    CONTENT_RESOURCE = "content_resource"  # NEW: For manual content resources

class ResourceStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"

class Resource(SQLModel, table=True):
    """(Data Model) Represents a resource in the system."""
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id", index=True)
    resource_type: ResourceType = Field(index=True)
    status: ResourceStatus = Field(default=ResourceStatus.ACTIVE, index=True)
    entity_id: Optional[str] = Field(default=None, index=True)  # External ID (e.g., listing key, URL)
    attributes: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)

    # --- Relationships ---
    user: Optional["User"] = Relationship(back_populates="resources")
    campaigns: List["CampaignBriefing"] = Relationship(back_populates="triggering_resource")
    portal_comments: List["PortalComment"] = Relationship(back_populates="resource")
    

class ResourceCreate(SQLModel):
    """Defines the structure for creating a new resource."""
    user_id: UUID
    resource_type: ResourceType
    status: ResourceStatus = ResourceStatus.ACTIVE
    entity_id: Optional[str] = None
    attributes: Dict[str, Any] = Field(default_factory=dict)

# --- NEW: Content Resource Models ---

class ContentResource(SQLModel, table=True):
    """(Data Model) Represents a manually added content resource."""
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id", index=True)
    title: str = Field(index=True)
    url: str = Field(index=True)
    description: Optional[str] = Field(default=None)
    categories: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    content_type: str = Field(default="article")  # article, video, document, etc.
    status: ResourceStatus = Field(default=ResourceStatus.ACTIVE, index=True)
    usage_count: int = Field(default=0, index=True)  # Track how often it's used
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)

    # --- Relationships ---
    user: Optional["User"] = Relationship(back_populates="content_resources")

class ContentResourceCreate(SQLModel):
    """Defines the structure for creating a new content resource."""
    title: str
    url: str
    description: Optional[str] = None
    categories: List[str] = Field(default_factory=list)
    content_type: str = "article"

class ContentResourceUpdate(SQLModel):
    """Defines updatable fields for content resources."""
    title: Optional[str] = None
    url: Optional[str] = None
    description: Optional[str] = None
    categories: Optional[List[str]] = None
    content_type: Optional[str] = None
    status: Optional[ResourceStatus] = None