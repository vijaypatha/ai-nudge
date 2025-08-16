# File Path: backend/data/models/client.py
# --- MODIFIED: Added notes_embedding field to store the semantic vector.

from typing import List, Dict, Any, Optional, TYPE_CHECKING
from uuid import UUID, uuid4
from sqlalchemy import Column, Text
from sqlmodel import SQLModel, Field, Relationship, JSON
from .portal import PortalComment

if TYPE_CHECKING:
    from .message import ScheduledMessage, Message
    from .user import User
    from .campaign import CampaignBriefing
    from .feedback import NegativePreference

class Client(SQLModel, table=True):
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id", index=True)
    full_name: str
    
    email: Optional[str] = Field(default=None, unique=True, index=True)
    phone: Optional[str] = Field(default=None, index=True)
    
    notes: Optional[str] = Field(default=None, sa_column=Column(Text))
    
    # --- NEW: Field to store the vector embedding of the client's notes. ---
    # This vector represents the "concept profile" for semantic matching.
    # Stored as JSON in the database.
    notes_embedding: Optional[List[float]] = Field(default=None, sa_column=Column(JSON))
    
    ai_tags: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    user_tags: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    
    preferences: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    last_interaction: Optional[str] = Field(default=None)
    timezone: Optional[str] = Field(default=None)
    
    # --- NEW: Survey completion tracking ---
    intake_survey_completed: bool = Field(default=False, index=True)
    intake_survey_sent_at: Optional[str] = Field(default=None)
    
    user: "User" = Relationship(back_populates="clients")
    
    scheduled_messages: List["ScheduledMessage"] = Relationship(back_populates="client")
    messages: List["Message"] = Relationship(back_populates="client")
    campaign_briefings: List["CampaignBriefing"] = Relationship(back_populates="client")
    negative_preferences: List["NegativePreference"] = Relationship(back_populates="client")
    intake_surveys: List["ClientIntakeSurvey"] = Relationship(back_populates="client")
    portal_comments: List["PortalComment"] = Relationship(back_populates="client")


class ClientIntakeSurvey(SQLModel, table=True):
    """
    Stores client responses to intake questionnaires to gather initial preferences.
    This addresses the cold start problem by providing structured data for AI personalization.
    """
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    client_id: UUID = Field(foreign_key="client.id", index=True)
    user_id: UUID = Field(foreign_key="user.id", index=True)
    
    # Survey metadata
    survey_type: str = Field(index=True)  # "real_estate_buyer", "real_estate_seller", "therapy", etc.
    survey_version: str = Field(default="1.0")
    completed_at: Optional[str] = Field(default=None)
    
    # Survey responses stored as structured JSON
    responses: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    
    # Processing status
    processed: bool = Field(default=False, index=True)
    preferences_extracted: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    tags_generated: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    
    # Relationships
    client: "Client" = Relationship(back_populates="intake_surveys")
    user: "User" = Relationship(back_populates="client_surveys")


class ClientCreate(SQLModel):
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    notes: Optional[str] = None
    ai_tags: List[str] = []
    user_tags: List[str] = []
    preferences: Dict[str, Any] = {}
    intake_survey_completed: bool = False

class ClientUpdate(SQLModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    notes: Optional[str] = None
    user_tags: Optional[List[str]] = None
    preferences: Optional[Dict[str, Any]] = None
    timezone: Optional[str] = None
    intake_survey_completed: Optional[bool] = None
    intake_survey_sent_at: Optional[str] = None

class ClientTagUpdate(SQLModel):
    user_tags: List[str]