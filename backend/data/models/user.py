# ---
# File Path: backend/data/models/user.py
# ---
# DEFINITIVE FIX: Adds `google_sync_complete` to track if a user has
# specifically imported contacts from Google.
# ---

from enum import Enum
from typing import List, Optional, TYPE_CHECKING, Dict, Any
from uuid import UUID, uuid4
from sqlmodel import SQLModel, Field, Relationship, Column, JSON

if TYPE_CHECKING:
    from .campaign import CampaignBriefing
    from .faq import Faq
    from .client import Client
    from .message import Message, ScheduledMessage

class UserType(str, Enum):
    REALTOR = "realtor"
    THERAPIST = "therapist"
    LOAN_OFFICER = "loan_officer"

class User(SQLModel, table=True):
    """(Data Model) Represents a user of the application."""
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)

    # --- Base User Information ---
    user_type: Optional[UserType] = Field(default=None) #
    full_name: str #
    email: Optional[str] = Field(default=None, index=True) #
    phone_number: str = Field(index=True, unique=True) #

    # --- Onboarding Tracking Fields ---
    onboarding_complete: bool = Field(default=False) #
    # MODIFIED: Added google_sync_complete
    onboarding_state: Dict[str, Any] = Field(
        default_factory=lambda: {
            "phone_verified": False,
            "work_style_set": False,
            "contacts_imported": False,
            "first_nudges_seen": False,
            "google_sync_complete": False
        },
        sa_column=Column(JSON)
    )

    # --- Existing Fields ---
    market_focus: List[str] = Field(default_factory=list, sa_column=Column(JSON)) #
    ai_style_guide: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON)) #
    strategy: Dict[str, Any] = Field(default_factory=lambda: {"nudge_format": "ready-to-send"}, sa_column=Column(JSON)) #
    mls_username: Optional[str] = Field(default=None) #
    mls_password: Optional[str] = Field(default=None) #
    license_number: Optional[str] = Field(default=None) #
    specialties: Optional[List[str]] = Field(default_factory=list, sa_column=Column(JSON)) #
    faq_auto_responder_enabled: bool = Field(default=True) #
    twilio_phone_number: Optional[str] = Field(default=None, index=True) #
    timezone: Optional[str] = Field(default=None, index=True) #



    # --- Relationships ---
    campaigns: List["CampaignBriefing"] = Relationship(back_populates="user") #
    faqs: List["Faq"] = Relationship(back_populates="user") #
    clients: List["Client"] = Relationship(back_populates="user") #
    messages: List["Message"] = Relationship(back_populates="user") #
    scheduled_messages: List["ScheduledMessage"] = Relationship(back_populates="user") #

class UserUpdate(SQLModel):
    """Defines all updatable fields for a user."""
    full_name: Optional[str] = None #
    email: Optional[str] = None #
    user_type: Optional[UserType] = None #
    
    onboarding_complete: Optional[bool] = None #
    onboarding_state: Optional[Dict[str, Any]] = None #

    # Existing Fields
    market_focus: Optional[List[str]] = None #
    ai_style_guide: Optional[Dict[str, Any]] = None #
    strategy: Optional[Dict[str, Any]] = None #
    mls_username: Optional[str] = None #
    mls_password: Optional[str] = None #
    license_number: Optional[str] = None #
    specialties: Optional[List[str]] = None #
    faq_auto_responder_enabled: Optional[bool] = None #
    twilio_phone_number: Optional[str] = None #
    timezone: Optional[str] = None #
