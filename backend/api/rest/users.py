# backend/api/rest/users.py
from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from typing import List
from data.models.user import User
from data.database import get_session

# Create the router with /users prefix
router = APIRouter(
    prefix="/users",
    tags=["Users"]
)  # ADD THIS CLOSING PARENTHESIS

@router.get("", response_model=List[User])
def get_all_users(session: Session = Depends(get_session)):
    """Get all users from the database"""
    statement = select(User)
    users = session.exec(statement).all()
    return users

@router.get("/{user_id}", response_model=User)
def get_user_by_id(user_id: str, session: Session = Depends(get_session)):
    """Get a specific user by ID"""
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
