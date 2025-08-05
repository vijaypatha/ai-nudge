# File: backend/api/rest/websockets.py

import logging
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException
from api.websocket_manager import manager
from data.models.user import User
from jose import JWTError, jwt
from sqlmodel import Session
from data.database import engine
from common.config import get_settings

settings = get_settings()
router = APIRouter()

async def get_user_from_token(token: str) -> User | None:
    """Helper function to authenticate a user from a JWT token."""
    try:
        # --- FIX: Add detailed logging to diagnose the 403 error ---
        logging.info(f"WS_AUTH: Attempting to decode token...")
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id: str | None = payload.get("sub")
        if not user_id:
            logging.warning("WS_AUTH: Token is valid but missing 'sub' (user_id).")
            return None

        logging.info(f"WS_AUTH: Token decoded successfully. User ID: {user_id}")
        with Session(engine) as session:
            user = session.get(User, user_id)
            if not user:
                logging.warning(f"WS_AUTH: User with ID {user_id} not found in database.")
                return None
            logging.info(f"WS_AUTH: User {user_id} found in database. Authentication successful.")
            return user
    except JWTError as e:
        logging.error(f"WS_AUTH: JWTError during token decoding. SECRET_KEY may be wrong. Error: {e}", exc_info=True)
        return None
    except Exception as e:
        logging.error(f"WS_AUTH: An unexpected error occurred during token validation. Error: {e}", exc_info=True)
        return None

@router.websocket("/ws/user")
async def user_websocket_endpoint(websocket: WebSocket, token: str = Query(...)):
    """
    Establishes a persistent WebSocket connection for a user to receive
    account-level notifications, such as nudge updates.
    """
    user = await get_user_from_token(token)
    if not user:
        await websocket.close(code=1008)
        return
    
    await websocket.accept()
    await manager.connect_user(websocket, str(user.id))
    try:
        while True:
            # Keep the connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect_user(websocket, str(user.id))

@router.websocket("/ws/{client_id}")
async def client_websocket_endpoint(websocket: WebSocket, client_id: str, token: str = Query(...)):
    """
    Establishes a WebSocket connection for a specific client conversation view.
    It now ALSO registers the user for general notifications.
    """
    user = await get_user_from_token(token)
    if not user:
        await websocket.close(code=1008)
        return

    # Connect to both client and user channels
    await manager.connect_client(websocket, client_id)
    await manager.connect_user(websocket, str(user.id))

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        # Disconnect from both channels on close
        manager.disconnect_client(websocket, client_id)
        manager.disconnect_user(websocket, str(user.id))