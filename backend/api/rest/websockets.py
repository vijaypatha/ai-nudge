import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from api.websocket_manager import manager
from api.security import get_current_user_from_token # <-- Import the authenticator
from data.models.user import User

router = APIRouter()

@router.websocket("/ws/{client_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    client_id: str,
    token: str = Query(...), # <-- Require a token as a query parameter
):
    """
    Handles the WebSocket connection, now with authentication.
    """
    try:
        # --- FIX: Authenticate the user before connecting ---
        user: User = await get_current_user_from_token(token)
        if not user:
            await websocket.close(code=403)
            return
    except Exception:
        await websocket.close(code=403)
        return

    await manager.connect(websocket, client_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, client_id)
    except Exception as e:
        logging.error(f"WS ERROR: An unexpected error occurred with client_id {client_id}. Error: {e}")
        if websocket in manager.active_connections.get(client_id, []):
             manager.disconnect(websocket, client_id)