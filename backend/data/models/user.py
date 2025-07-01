# ---
# File Path: backend/data/models/user.py
# Purpose: Stores realtor user data.
# --- UPDATED to include a UserUpdate model for consistency ---

from typing import List, Optional, TYPE_CHECKING, Dict, Any
from uuid import UUID, uuid4
from sqlmodel import SQLModel, Field, Relationship, Column, JSON

if TYPE_CHECKING:
    from .campaign import CampaignBriefing

class User(SQLModel, table=True):
    """
    (Data Model) Represents a realtor user of the application.
    """
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    full_name: str
    email: str = Field(unique=True, index=True)
    phone_number: Optional[str] = Field(default=None, index=True)
    market_focus: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    ai_style_guide: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    
    strategy: Dict[str, Any] = Field(default_factory=lambda: {"nudge_format": "ready-to-send"}, sa_column=Column(JSON))
    
    # Defines the one-to-many relationship to campaigns
    campaigns: List["CampaignBriefing"] = Relationship(back_populates="user")

# --- NEW: Added UserUpdate model for handling partial updates ---
class UserUpdate(SQLModel):
    """
    Defines the schema for updating a user's record.
    """
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    market_focus: Optional[List[str]] = None
    ai_style_guide: Optional[Dict[str, Any]] = None
    strategy: Optional[Dict[str, Any]] = None

