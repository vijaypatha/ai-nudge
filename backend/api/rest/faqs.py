# File Path: backend/api/rest/faqs.py
# Purpose   : CRUD endpoints for FAQs with per-user scoping, text-normalisation
#             before embedding, and fully async I/O to avoid event-loop clashes.

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session, select

from api.security import get_current_user_from_token
from common.text_utils import normalize_text              # ADD
from data.database import engine
from data.models.faq import Faq
from data.models.user import User
from integrations.gemini import get_text_embedding        # async helper

router = APIRouter(prefix="/faqs", tags=["FAQs"])

# --------------------------------------------------------------------------- #
# ⬇︎ Pydantic I/O Schemas                                                     #
# --------------------------------------------------------------------------- #
class FaqBase(BaseModel):
    question: str
    answer:   str
    is_enabled: bool = True


class FaqCreate(FaqBase):
    pass


class FaqUpdate(BaseModel):
    question: Optional[str] = None
    answer:   Optional[str] = None
    is_enabled: Optional[bool] = None


class FaqRead(FaqBase):
    id: UUID


# --------------------------------------------------------------------------- #
# ⬇︎ Routes                                                                   #
# --------------------------------------------------------------------------- #
@router.get("/", response_model=List[FaqRead])
async def list_faqs(current_user: User = Depends(get_current_user_from_token)):
    """Return all FAQs that belong to the authenticated user."""
    with Session(engine) as session:
        return session.exec(
            select(Faq).where(Faq.user_id == current_user.id)
        ).all()


@router.post("/", response_model=FaqRead, status_code=status.HTTP_201_CREATED)
async def create_faq(
    faq_create: FaqCreate,
    current_user: User = Depends(get_current_user_from_token),
):
    """
    Persist a new FAQ and its embedding.  
    The question text is normalised before embedding to maximise
    cosine-similarity with incoming SMS.
    """
    clean_q    = normalize_text(faq_create.question)          # CHANGE
    faq_vector = await get_text_embedding(clean_q)            # CHANGE

    new_faq = Faq.model_validate(
        faq_create,
        update={
            "user_id": current_user.id,
            "faq_embedding": faq_vector,
        },
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
    """
    Update an existing FAQ.  
    If the question text changes, re-embed with the same normalisation rules.
    """
    with Session(engine) as session:
        db_faq: Faq | None = session.get(Faq, faq_id)
        if not db_faq or db_faq.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="FAQ not found")

        data = faq_update.model_dump(exclude_unset=True)

        if "question" in data:                                   # ADD
            clean_q               = normalize_text(data["question"])   # ADD
            data["faq_embedding"] = await get_text_embedding(clean_q)  # CHANGE

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
    """Hard-delete an FAQ owned by the current user."""
    with Session(engine) as session:
        db_faq: Faq | None = session.get(Faq, faq_id)
        if not db_faq or db_faq.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="FAQ not found")
        session.delete(db_faq)
        session.commit()
