import jwt
from datetime import datetime, timezone, timedelta
from typing import Dict, Any
from uuid import UUID
from common.config import get_settings

settings = get_settings()

def create_portal_token(client_id: UUID, user_id: UUID) -> str:
    """Create a JWT token for client portal access."""
    payload = {
        "sub": str(client_id),
        "user_id": str(user_id),
        "exp": datetime.now(timezone.utc) + timedelta(days=30),
        "iat": datetime.now(timezone.utc),
        "scope": "portal_access"
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

def decode_portal_token(token: str) -> Dict[str, Any]:
    """Decode and validate a portal JWT token."""
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=["HS256"], 
            options={"require": ["exp", "sub", "scope"]}
        )
        if payload.get("scope") != "portal_access":
            raise ValueError("Invalid token scope")
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError("Portal link has expired")
    except jwt.InvalidTokenError:
        raise ValueError("Invalid portal link")
