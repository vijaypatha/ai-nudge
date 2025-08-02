# File Path: backend/api/security.py

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlmodel import Session
from common.config import get_settings
from data.database import engine
from data.models.user import User

# Use centralized settings
settings = get_settings()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_current_user_from_token(token: str = Depends(oauth2_scheme)) -> User:
    """
    Decodes the JWT token to find the current user.
    This is the dependency that will protect all our endpoints.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    with Session(engine) as session:
        user = session.get(User, user_id)
        if user is None:
            raise credentials_exception
        return user

def is_super_user(user: User) -> bool:
    """
    Check if a user has super user privileges.
    (This function can be kept for potential future admin roles).
    """
    return user.super_user is True

def get_user_accessible_verticals(user: User) -> list[str]:
    """
    Get the list of verticals a user can access.
    - If user.vertical is None, they get access to all verticals.
    - Otherwise, they are restricted to their assigned vertical.
    """
    if user.vertical is None:
        # This user has an "All-Access" account.
        try:
            from agent_core.brain.verticals import VERTICAL_CONFIGS
            return list(VERTICAL_CONFIGS.keys())  # Automatically gets all configured verticals
        except ImportError:
            # Fallback to hardcoded list if registry not available
            return ["real_estate", "therapy", "loan_officer"]
    else:
        # This is a standard user restricted to their single assigned vertical.
        return [user.vertical]