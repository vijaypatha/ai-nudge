# ---
# File Path: backend/data/models/user.py
# Purpose: Defines the data model for a User, including their strategic preferences.
# ---
from pydantic import BaseModel, Field
from typing import List, Literal
from uuid import UUID, uuid4

class UserStrategy(BaseModel):
    """Defines the user's strategic preferences for how AI Nudge should operate."""
    nudge_format: Literal["ready-to-send", "data-points-only"] = "ready-to-send"

class User(BaseModel):
    """Represents a user of the AI Nudge application (e.g., a Realtor)."""
    id: UUID = Field(default_factory=uuid4)
    full_name: str
    email: str
    market_focus: List[str] = Field(
        default_factory=list,
        description="The primary markets or specializations the user focuses on."
    )
    strategy: UserStrategy = Field(default_factory=UserStrategy)

    class Config:
        from_attributes = True