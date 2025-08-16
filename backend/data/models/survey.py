# File Path: backend/data/models/survey.py

from typing import List, Optional, TYPE_CHECKING
from uuid import UUID, uuid4
from sqlmodel import SQLModel, Field, Relationship, JSON, Column
from agent_core.survey_config import QuestionType

if TYPE_CHECKING:
    from .user import User

class SurveyQuestion(SQLModel, table=True):
    """(Data Model) Represents a user-defined question for a client intake survey."""
    # --- THIS IS THE FIX ---
    # Explicitly defining the table name resolves the naming conflict.
    __tablename__ = "surveyquestion"

    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id", index=True)
    
    # Defines which survey this question belongs to (e.g., "real_estate_buyer")
    survey_type: str = Field(index=True)
    
    # The actual question content and configuration
    question_text: str
    question_type: QuestionType = Field(default=QuestionType.TEXT)
    options: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))
    is_required: bool = Field(default=False)
    placeholder: Optional[str] = Field(default=None)
    help_text: Optional[str] = Field(default=None)
    preference_key: Optional[str] = Field(default=None)
    
    # To maintain user-defined order
    display_order: int = Field(default=0)
    
    # Relationship back to the user
    user: "User" = Relationship(back_populates="custom_survey_questions")


class SurveyQuestionCreate(SQLModel):
    survey_type: str
    question_text: str
    question_type: QuestionType
    options: Optional[List[str]] = None
    is_required: bool = False
    placeholder: Optional[str] = None
    help_text: Optional[str] = None
    preference_key: Optional[str] = None
    display_order: int = 0

class SurveyQuestionUpdate(SQLModel):
    question_text: Optional[str] = None
    question_type: Optional[QuestionType] = None
    options: Optional[List[str]] = None
    is_required: Optional[bool] = None
    placeholder: Optional[str] = None
    help_text: Optional[str] = None
    preference_key: Optional[str] = None
    display_order: Optional[int] = None