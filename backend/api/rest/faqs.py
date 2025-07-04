# File Path: backend/api/rest/faqs.py
from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional
from uuid import UUID
from sqlmodel import Session
from pydantic import BaseModel

from data.database import engine
from data.models.faq import Faq
from data.models.user import User
# --- MODIFIED: Use the new central security dependency ---
from api.security import get_current_user_from_token

router = APIRouter(prefix="/faqs", tags=["FAQs"])

class FaqBase(BaseModel):
    question: str
    answer: str
    is_enabled: bool = True

class FaqCreate(FaqBase):
    pass

class FaqUpdate(BaseModel):
    question: Optional[str] = None
    answer: Optional[str] = None
    is_enabled: Optional[bool] = None

class FaqRead(FaqBase):
    id: UUID

# All endpoints below were already correctly using the dependency pattern.
# No changes to the logic were needed, only the import path above was updated.

@router.get("/", response_model=List[FaqRead])
def get_faqs_for_user(current_user: User = Depends(get_current_user_from_token)):
    with Session(engine) as session:
        faqs = session.query(Faq).filter(Faq.user_id == current_user.id).all()
        return faqs

@router.post("/", response_model=FaqRead, status_code=status.HTTP_201_CREATED)
def create_faq(faq_create: FaqCreate, current_user: User = Depends(get_current_user_from_token)):
    with Session(engine) as session:
        new_faq = Faq.model_validate(faq_create)
        new_faq.user_id = current_user.id
        
        session.add(new_faq)
        session.commit()
        session.refresh(new_faq)
        return new_faq

@router.put("/{faq_id}", response_model=FaqRead)
def update_faq(faq_id: UUID, faq_update: FaqUpdate, current_user: User = Depends(get_current_user_from_token)):
    with Session(engine) as session:
        db_faq = session.get(Faq, faq_id)
        if not db_faq or db_faq.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="FAQ not found")
        
        faq_data = faq_update.model_dump(exclude_unset=True)
        for key, value in faq_data.items():
            setattr(db_faq, key, value)
            
        session.add(db_faq)
        session.commit()
        session.refresh(db_faq)
        return db_faq

@router.delete("/{faq_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_faq(faq_id: UUID, current_user: User = Depends(get_current_user_from_token)):
    with Session(engine) as session:
        db_faq = session.get(Faq, faq_id)
        if not db_faq or db_faq.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="FAQ not found")
        session.delete(db_faq)
        session.commit()
        return