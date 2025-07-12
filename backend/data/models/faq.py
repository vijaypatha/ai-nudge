# backend/data/models/faq.py
from typing import Optional, TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .user import User

class Faq(SQLModel, table=True):
    """Simple FAQ storage without embeddings"""
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id")
    
    # Core content only
    question: str
    answer: str
    is_enabled: bool = Field(default=True)
    
    # Relationship back to User
    user: Optional["User"] = Relationship(back_populates="faqs")
