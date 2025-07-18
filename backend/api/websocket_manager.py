# backend/api/websocket_manager.py
# --- NEW FILE ---

import logging
from collections import defaultdict
from fastapi import WebSocket
from typing import List, Dict

class ConnectionManager:
    """
    Manages active WebSocket connections, organized by a client_id.
    This allows for broadcasting messages to all users viewing a specific client's conversation.
    """
    def __init__(self):
        # Use a defaultdict to automatically create a list for new client_ids
        self.active_connections: Dict[str, List[WebSocket]] = defaultdict(list)
        logging.info("WebSocket ConnectionManager initialized.")

    async def connect(self, websocket: WebSocket, client_id: str):
        """Accepts and stores a new WebSocket connection."""
        await websocket.accept()
        self.active_connections[client_id].append(websocket)
        logging.info(f"WS CONNECT: New connection for client_id: {client_id}. Total connections for client: {len(self.active_connections[client_id])}")

    def disconnect(self, websocket: WebSocket, client_id: str):
        """Removes a WebSocket connection."""
        if websocket in self.active_connections[client_id]:
            self.active_connections[client_id].remove(websocket)
        logging.info(f"WS DISCONNECT: Connection closed for client_id: {client_id}. Total connections for client: {len(self.active_connections[client_id])}")

    async def broadcast_to_client(self, client_id: str, message: str):
        """Broadcasts a message to all connected clients for a specific client_id."""
        connections = self.active_connections.get(client_id, [])
        if not connections:
            logging.info(f"WS BROADCAST: No active connections for client_id: {client_id}. Message not sent.")
            return

        logging.info(f"WS BROADCAST: Sending message to {len(connections)} connection(s) for client_id: {client_id}")
        for connection in connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logging.error(f"WS BROADCAST ERROR: Could not send message to a client for client_id {client_id}. Error: {e}")

# Create a single, globally accessible instance of the manager.
manager = ConnectionManager()