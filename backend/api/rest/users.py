# backend/api/rest/users.py
from fastapi import APIRouter
from sqlmodel import Session, select
from typing import List
from data.models.user import User
from data.database import engine

# Create the router
router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

@router.get("", response_model=List[User])
@router.get("/", response_model=List[User])
def get_all_users():
    """Get all users from the database"""
    with Session(engine) as session:
        statement = select(User)
        users = session.exec(statement).all()
        return users
