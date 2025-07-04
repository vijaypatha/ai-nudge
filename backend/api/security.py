# File Path: backend/api/security.py
# Purpose: Central utility for API authentication and user session management.

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlmodel import Session
from pydantic import BaseModel

# Assuming settings are managed in a central config.
# In a real app, these would come from your config file/environment variables.
class Settings(BaseModel):
    SECRET_KEY: str = "your-super-secret-key-that-is-long-and-random"
    ALGORITHM: str = "HS256"

settings = Settings()


from data.database import engine
from data.models.user import User

# This scheme expects a "Bearer <token>" in the Authorization header.
# tokenUrl is a dummy path; the frontend will acquire the token from our /auth/otp/verify endpoint.
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
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
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