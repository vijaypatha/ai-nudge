# backend/api/endpoints/websockets.py

import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException
from api.websocket_manager import manager
from data.models.user import User
from jose import JWTError, jwt
from sqlmodel import Session
from data.database import engine
from common.config import get_settings

# CRITICAL: Use centralized settings, NOT hardcoded values
settings = get_settings()

router = APIRouter()

@router.websocket("/ws/{client_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    client_id: str,
    token: str = Query(...),
):
    """
    WebSocket endpoint with proper centralized authentication.
    """
    user: User | None = None
    
    try:
        # Use the SAME secret key as your REST API
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id: str | None = payload.get("sub")
        
        if user_id:
            with Session(engine) as session:
                user = session.get(User, user_id)
                
        if not user:
            raise ValueError("User not found")
            
    except (JWTError, ValueError, Exception) as e:
        logging.warning(f"WS REJECT: Authentication failed for client_id {client_id}. Token validation error: {e}")
        await websocket.close(code=1008)  # Policy violation
        return

    # Success - establish connection
    logging.info(f"WS SUCCESS: User {user.id} authenticated for client {client_id}")
    
    await manager.connect(websocket, client_id)
    
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, client_id)
        logging.info(f"WS DISCONNECT: User {user.id} disconnected from client {client_id}")
    except Exception as e:
        logging.error(f"WS ERROR: Unexpected error for client_id {client_id}: {e}")
        if manager.active_connections.get(client_id) and websocket in manager.active_connections[client_id]:
            manager.disconnect(websocket, client_id)
