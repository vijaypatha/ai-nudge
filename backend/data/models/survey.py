# File Path: backend/data/models/survey.py
# MODIFIED: Introduced SurveyTemplate and linked SurveyQuestion to it.

from typing import List, Optional, TYPE_CHECKING
from uuid import UUID, uuid4
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Relationship, JSON, Column, Enum
from agent_core.survey_config import QuestionType

if TYPE_CHECKING:
    from .user import User

# NEW: The SurveyTemplate model, which acts as the container for a survey.
class SurveyTemplate(SQLModel, table=True):
    __tablename__ = "surveytemplate"
    
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id", index=True)
    
    name: str = Field(index=True)
    description: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Relationships
    user: "User" = Relationship(back_populates="survey_templates")
    questions: List["SurveyQuestion"] = Relationship(back_populates="template")

class SurveyQuestion(SQLModel, table=True):
    __tablename__ = "surveyquestion"

    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id", index=True)
    
    # MODIFIED: Questions now belong to a template, not a generic "survey_type".
    template_id: UUID = Field(foreign_key="surveytemplate.id", index=True)
    
    question_text: str
    question_type: QuestionType = Field(sa_column=Column(Enum(QuestionType, native_enum=False)))
    options: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))
    is_required: bool = Field(default=False)
    placeholder: Optional[str] = Field(default=None)
    help_text: Optional[str] = Field(default=None)
    preference_key: Optional[str] = Field(default=None)
    display_order: int = Field(default=0)
    
    # Relationships
    user: "User" = Relationship() # A question is still owned by a user for permissioning
    template: "SurveyTemplate" = Relationship(back_populates="questions")

# --- Pydantic models for API interaction ---

# For Templates
class SurveyTemplateCreate(SQLModel):
    name: str
    description: Optional[str] = None

class SurveyTemplateUpdate(SQLModel):
    name: Optional[str] = None
    description: Optional[str] = None

# For Questions (Contextualized to a Template)
class SurveyQuestionCreate(SQLModel):
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