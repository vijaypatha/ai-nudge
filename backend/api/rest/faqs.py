# ---
# File Path: backend/api/rest/faqs.py
# Purpose: CORRECTED to separate API data models from the database model.
# ---
from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional
from uuid import UUID
from sqlmodel import Session, SQLModel
from pydantic import BaseModel

from data.database import engine
from data.models.faq import Faq
from data.models.user import User
from api.rest.users import get_current_user_from_token # Reuse the user dependency

router = APIRouter(prefix="/faqs", tags=["FAQs"])

# --- NEW: API-specific models that DO NOT include database relationships ---

class FaqBase(BaseModel):
    """Defines the core fields for an FAQ that are sent over the API."""
    question: str
    answer: str
    is_enabled: bool = True

class FaqCreate(FaqBase):
    """Model for creating a new FAQ."""
    pass

class FaqUpdate(BaseModel):
    """Model for updating an FAQ. All fields are optional."""
    question: Optional[str] = None
    answer: Optional[str] = None
    is_enabled: Optional[bool] = None

class FaqRead(FaqBase):
    """Model for reading an FAQ, includes the ID."""
    id: UUID

# --- Endpoints are now updated to use these new, simpler models ---

@router.get("/", response_model=List[FaqRead])
def get_faqs_for_user(current_user: User = Depends(get_current_user_from_token)):
    """Get all FAQs for the currently authenticated user."""
    with Session(engine) as session:
        faqs = session.query(Faq).filter(Faq.user_id == current_user.id).all()
        return faqs

@router.post("/", response_model=FaqRead, status_code=status.HTTP_201_CREATED)
def create_faq(faq_create: FaqCreate, current_user: User = Depends(get_current_user_from_token)):
    """Create a new FAQ for the user."""
    with Session(engine) as session:
        # Create the full database model from the simple API model
        new_faq = Faq.model_validate(faq_create)
        new_faq.user_id = current_user.id
        
        session.add(new_faq)
        session.commit()
        session.refresh(new_faq)
        return new_faq

@router.put("/{faq_id}", response_model=FaqRead)
def update_faq(faq_id: UUID, faq_update: FaqUpdate, current_user: User = Depends(get_current_user_from_token)):
    """Update an existing FAQ."""
    with Session(engine) as session:
        db_faq = session.get(Faq, faq_id)
        if not db_faq or db_faq.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="FAQ not found")
        
        # Get update data, excluding fields that were not set
        faq_data = faq_update.model_dump(exclude_unset=True)
        for key, value in faq_data.items():
            setattr(db_faq, key, value)
            
        session.add(db_faq)
        session.commit()
        session.refresh(db_faq)
        return db_faq

@router.delete("/{faq_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_faq(faq_id: UUID, current_user: User = Depends(get_current_user_from_token)):
    """Delete an FAQ."""
    with Session(engine) as session:
        db_faq = session.get(Faq, faq_id)
        if not db_faq or db_faq.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="FAQ not found")
        session.delete(db_faq)
        session.commit()
        return