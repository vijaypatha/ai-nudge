# ---
# File Path: backend/api/rest/users.py
# ---
# CORRECTED: Removed the duplicate definition of the User model and now correctly
# imports the existing User and UserUpdate models from data/models/user.py
# ---
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List
from uuid import UUID

from data.database import engine
# CORRECTLY import the models, don't redefine them
from data.models.user import User, UserUpdate 

# This placeholder function would be replaced by a real authentication dependency
def get_current_user_from_token() -> User:
    """A placeholder to simulate getting the logged-in user from an auth token."""
    with Session(engine) as session:
        # For demo purposes, we'll always return our one hardcoded user.
        user = session.get(User, UUID("a8c6f1d7-8f7a-4b6e-8b0f-9e5a7d6c5b4a"))
        if not user:
            raise HTTPException(status_code=404, detail="Demo user not found")
        return user

# Create the router
router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

# --- NEW: Endpoints for the User Settings Page ---
@router.get("/me", response_model=User)
def get_current_user_profile(current_user: User = Depends(get_current_user_from_token)):
    """Get the profile of the currently authenticated user."""
    return current_user

@router.put("/me", response_model=User)
def update_current_user_profile(user_update: UserUpdate, current_user: User = Depends(get_current_user_from_token)):
    """Update the profile of the currently authenticated user."""
    with Session(engine) as session:
        user_to_update = session.get(User, current_user.id)
        if not user_to_update:
            raise HTTPException(status_code=404, detail="User not found")
            
        update_data = user_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(user_to_update, key, value)
            
        session.add(user_to_update)
        session.commit()
        session.refresh(user_to_update)
        return user_to_update

# --- Existing Admin-level Endpoint ---
@router.get("/", response_model=List[User])
def get_all_users():
    """Get all users from the database (for admin purposes)."""
    with Session(engine) as session:
        statement = select(User)
        users = session.exec(statement).all()
        return users