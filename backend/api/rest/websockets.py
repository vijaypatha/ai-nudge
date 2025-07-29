# backend/api/rest/websockets.py
# --- MODIFIED: Added a user-level websocket endpoint ---

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
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id: str | None = payload.get("sub")
        if user_id:
            with Session(engine) as session:
                return session.get(User, user_id)
    except (JWTError, Exception):
        return None
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