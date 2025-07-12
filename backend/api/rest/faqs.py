# backend/api/rest/faqs.py
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session, select

from api.security import get_current_user_from_token
from data.database import engine
from data.models.faq import Faq
from data.models.user import User

router = APIRouter(prefix="/faqs", tags=["FAQs"])

# Pydantic schemas
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

@router.get("/", response_model=List[FaqRead])
async def list_faqs(current_user: User = Depends(get_current_user_from_token)):
    """Return all FAQs for the authenticated user"""
    with Session(engine) as session:
        return session.exec(
            select(Faq).where(Faq.user_id == current_user.id)
        ).all()

@router.post("/", response_model=FaqRead, status_code=status.HTTP_201_CREATED)
async def create_faq(
    faq_create: FaqCreate,
    current_user: User = Depends(get_current_user_from_token),
):
    """Create a new FAQ"""
    new_faq = Faq.model_validate(
        faq_create,
        update={"user_id": current_user.id}
    )
    
    with Session(engine) as session:
        session.add(new_faq)
        session.commit()
        session.refresh(new_faq)
        return new_faq

@router.put("/{faq_id}", response_model=FaqRead)
async def update_faq(
    faq_id: UUID,
    faq_update: FaqUpdate,
    current_user: User = Depends(get_current_user_from_token),
):
    """Update an existing FAQ"""
    with Session(engine) as session:
        db_faq: Faq | None = session.get(Faq, faq_id)
        if not db_faq or db_faq.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="FAQ not found")
        
        data = faq_update.model_dump(exclude_unset=True)
        for key, value in data.items():
            setattr(db_faq, key, value)
        
        session.add(db_faq)
        session.commit()
        session.refresh(db_faq)
        return db_faq

@router.delete("/{faq_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_faq(
    faq_id: UUID,
    current_user: User = Depends(get_current_user_from_token),
):
    """Delete an FAQ"""
    with Session(engine) as session:
        db_faq: Faq | None = session.get(Faq, faq_id)
        if not db_faq or db_faq.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="FAQ not found")
        session.delete(db_faq)
        session.commit()
