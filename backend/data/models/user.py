
#user - Stores realtor user data with email index

from typing import List, Optional, TYPE_CHECKING
from uuid import UUID, uuid4
from sqlmodel import SQLModel, Field, Relationship, Column, JSON

if TYPE_CHECKING:
    from .campaign import CampaignBriefing

class UserStrategy(SQLModel):
    nudge_format: str = "ready-to-send"

class User(SQLModel, table=True):
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    full_name: str
    email: str = Field(unique=True, index=True)
    market_focus: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    strategy: UserStrategy = Field(default_factory=UserStrategy, sa_column=Column(JSON))
    
    campaigns: List["CampaignBriefing"] = Relationship(back_populates="user")
