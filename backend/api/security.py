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
