# FILE: backend/api/rest/settings.py (NEW FILE)

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from pydantic import BaseModel
from typing import List

from backend.api.security import get_current_user_from_token
from data.database import get_session
from data.models.user import User

# --- Configuration for default roles per vertical ---
DEFAULT_ROLES = {
    "real_estate": ["Buyer", "Seller", "Renter", "Investor"],
    "therapy": ["Client", "Patient", "Couple", "Family"],
    "default": ["Client", "Customer", "Lead", "Contact"],
}

router = APIRouter(prefix="/settings", tags=["User Settings"])


class RolesUpdatePayload(BaseModel):
    roles: List[str]


@router.get("/roles", response_model=List[str])
async def get_user_client_roles(current_user: User = Depends(get_current_user_from_token)):
    """
    Fetches the user's custom client roles.
    If none are set, returns the system default for their vertical.
    """
    if current_user.client_roles:
        return current_user.client_roles

    return DEFAULT_ROLES.get(current_user.vertical, DEFAULT_ROLES["default"])


@router.put("/roles", response_model=List[str])
async def update_user_client_roles(
    payload: RolesUpdatePayload,
    current_user: User = Depends(get_current_user_from_token),
    session: Session = Depends(get_session)
):
    """
    Updates the user's custom list of client roles.
    """
    if not payload.roles:
        raise HTTPException(status_code=400, detail="Roles list cannot be empty.")

    user_to_update = session.get(User, current_user.id)
    user_to_update.client_roles = payload.roles
    session.add(user_to_update)
    session.commit()
    session.refresh(user_to_update)

    return user_to_update.client_roles