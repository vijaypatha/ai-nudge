# File Path: backend/api/rest/users.py

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List
from uuid import UUID

# --- FIX: Import get_session for dependency injection ---
from data.database import get_session
from data.models.user import User, UserUpdate
from api.security import get_current_user_from_token

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

@router.get("/me", response_model=User)
def get_current_user_profile(current_user: User = Depends(get_current_user_from_token)):
    """Get the profile of the currently authenticated user."""
    return current_user

@router.put("/me", response_model=User)
def update_current_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user_from_token),
    # --- FIX: Use the dependency-injected session ---
    session: Session = Depends(get_session)
):
    """Update the profile of the currently authenticated user."""
    # The endpoint now correctly uses the session provided by the dependency,
    # which our test setup can override.
    user_to_update = session.get(User, current_user.id)
    if not user_to_update:
        # This case should ideally not be hit if the token is valid, but it's good practice.
        raise HTTPException(status_code=404, detail="User not found")
        
    update_data = user_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(user_to_update, key, value)
        
    session.add(user_to_update)
    session.commit()
    session.refresh(user_to_update)
    return user_to_update

@router.get("/", response_model=List[User], include_in_schema=False)
def get_all_users(session: Session = Depends(get_session)):
    """Get all users from the database (for admin purposes)."""
    # Also updated this endpoint to use the injected session for consistency.
    users = session.exec(select(User)).all()
    return users
