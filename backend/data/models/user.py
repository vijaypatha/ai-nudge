# ---
# File Path: backend/data/models/user.py
# --- FINAL, CONSOLIDATED VERSION ---
# This version merges all original fields with all the new fields 
# required for multi-tenancy and the settings page. Nothing has been removed.
# ---

from enum import Enum
from typing import List, Optional, TYPE_CHECKING, Dict, Any
from uuid import UUID, uuid4
from sqlmodel import SQLModel, Field, Relationship, Column, JSON

if TYPE_CHECKING:
    from .campaign import CampaignBriefing
    from .faq import Faq

# Defines the allowed user types for type safety.
class UserType(str, Enum):
    REALTOR = "realtor"
    THERAPIST = "therapist"
    LOAN_OFFICER = "loan_officer"

class User(SQLModel, table=True):
    """(Data Model) Represents a user of the application."""
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    
    # --- Base User Information ---
    user_type: UserType
    full_name: str
    email: Optional[str] = Field(default=None, index=True) # Optional as requested
    phone_number: str = Field(index=True, unique=True) # Primary identifier
    
    # --- Original Fields (Restored) ---
    market_focus: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    ai_style_guide: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    strategy: Dict[str, Any] = Field(default_factory=lambda: {"nudge_format": "ready-to-send"}, sa_column=Column(JSON))

    # --- New Settings Fields ---
    # Realtor-specific
    mls_username: Optional[str] = Field(default=None)
    mls_password: Optional[str] = Field(default=None)
    
    # Therapist-specific
    license_number: Optional[str] = Field(default=None)
    specialties: Optional[List[str]] = Field(default_factory=list, sa_column=Column(JSON))
    
    # AI Automation Fields
    faq_auto_responder_enabled: bool = Field(default=True)
    
    # --- Relationships (All included) ---
    campaigns: List["CampaignBriefing"] = Relationship(back_populates="user")
    faqs: List["Faq"] = Relationship(back_populates="user")

class UserUpdate(SQLModel):
    """Defines all updatable fields for the user settings page."""
    full_name: Optional[str] = None
    email: Optional[str] = None
    
    # Original Fields
    market_focus: Optional[List[str]] = None
    ai_style_guide: Optional[Dict[str, Any]] = None
    strategy: Optional[Dict[str, Any]] = None

    # New Settings Fields
    mls_username: Optional[str] = None
    mls_password: Optional[str] = None
    license_number: Optional[str] = None
    specialties: Optional[List[str]] = None
    faq_auto_responder_enabled: Optional[bool] = None