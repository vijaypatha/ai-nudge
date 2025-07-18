# backend/api/rest/websockets.py
# --- NEW FILE ---

import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from api.websocket_manager import manager # Import the global manager instance

router = APIRouter()

@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """
    Handles the WebSocket connection for a specific client conversation.
    """
    await manager.connect(websocket, client_id)
    try:
        # This loop keeps the connection alive to listen for the client closing it.
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, client_id)
    except Exception as e:
        logging.error(f"WS ERROR: An unexpected error occurred with client_id {client_id}. Error: {e}")
        if websocket in manager.active_connections.get(client_id, []):
             manager.disconnect(websocket, client_id)