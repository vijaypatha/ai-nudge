# File Path: backend/data/models/faq.py
# Purpose   : Defines the FAQ table with a persistent vector field used for similarity search.

from typing import Optional, List, TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, JSON

if TYPE_CHECKING:                      # Prevent circular-import issues in type-checking
    from .user import User             # Local import for the back-reference

class Faq(SQLModel, table=True):
    """Stores per-user FAQs and the pre-computed embedding of each question."""
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id")

    # Core content
    question: str
    answer:   str

    # Control flags
    is_enabled: bool = Field(default=True, description="When False, FAQ is ignored in matching.")

    # Vector used for semantic search (Google text-embedding-004 → 768 dims)
    faq_embedding: List[float] = Field(
        default_factory=list,
        sa_column=Column(JSON),         # Stored as JSON for portability
        description="768-D embedding of the FAQ question"
    )

    # Relationship back to User (1-to-many)
    user: Optional["User"] = Relationship(back_populates="faqs")
