# ---
# File Path: backend/data/models/user.py
# Purpose: Stores realtor user data.
# This version is CORRECTED to fix a JSON serialization error by replacing the
# UserStrategy object with a standard Dict. It also adds a phone_number field.
# ---
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
    # NEW: Added a phone_number field for the user, essential for an SMS-first app.
    phone_number: Optional[str] = Field(default=None, index=True)
    market_focus: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    
    # CORRECTED: Replaced the complex UserStrategy object with a simple dictionary.
    # This solves the "not JSON serializable" error during database commits.
    strategy: Dict[str, Any] = Field(default_factory=lambda: {"nudge_format": "ready-to-send"}, sa_column=Column(JSON))
    
    # Define the one-to-many relationship to campaigns
    campaigns: List["CampaignBriefing"] = Relationship(back_populates="user")