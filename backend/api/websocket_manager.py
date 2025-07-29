# backend/api/websocket_manager.py
# --- MODIFIED: Added user-level connection management ---

import logging
from collections import defaultdict
from fastapi import WebSocket
from typing import List, Dict, Set
import json
import asyncio

class ConnectionManager:
    """
    Manages active WebSocket connections.
    - `client_connections`: For client-specific rooms (e.g., a conversation page).
    - `user_connections`: For user-specific notifications (e.g., 'your nudges have been updated').
    """
    def __init__(self):
        self.client_connections: Dict[str, List[WebSocket]] = defaultdict(list)
        self.user_connections: Dict[str, Set[WebSocket]] = defaultdict(set) # Use a set for users to avoid duplicates
        logging.info("WebSocket ConnectionManager initialized with client and user scopes.")

    # --- Client-specific methods (unchanged) ---
    async def connect_client(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.client_connections[client_id].append(websocket)
        logging.info(f"WS CONNECT (CLIENT): New connection for client_id: {client_id}.")

    def disconnect_client(self, websocket: WebSocket, client_id: str):
        if websocket in self.client_connections[client_id]:
            self.client_connections[client_id].remove(websocket)
        logging.info(f"WS DISCONNECT (CLIENT): Connection closed for client_id: {client_id}.")

    async def broadcast_json_to_client(self, client_id: str, data: dict):
        connections = self.client_connections.get(client_id, [])
        if not connections:
            return
        message_to_send = json.dumps(data)
        logging.info(f"WS BROADCAST (CLIENT): Sending to {len(connections)} connection(s) for client_id: {client_id}: {message_to_send}")
        for connection in connections:
            await connection.send_text(message_to_send)

    # --- NEW: User-specific methods ---
    async def connect_user(self, websocket: WebSocket, user_id: str):
        """Accepts and stores a new WebSocket connection for a user."""
        # Note: The websocket might already be accepted by another endpoint
        try:
            await websocket.accept()
        except RuntimeError: # Handles cases where websocket is already active
            pass
        self.user_connections[user_id].add(websocket)
        logging.info(f"WS CONNECT (USER): New connection for user_id: {user_id}. Total connections for user: {len(self.user_connections[user_id])}")

    def disconnect_user(self, websocket: WebSocket, user_id: str):
        """Removes a user's WebSocket connection."""
        self.user_connections[user_id].discard(websocket)
        logging.info(f"WS DISCONNECT (USER): Connection closed for user_id: {user_id}. Total connections for user: {len(self.user_connections[user_id])}")

    async def broadcast_to_user(self, user_id: str, data: dict):
        """Broadcasts a JSON payload to all connections for a specific user_id."""
        connections = self.user_connections.get(user_id)
        if not connections:
            logging.info(f"WS BROADCAST (USER): No active connections for user_id: {user_id}. Message not sent.")
            return

        message_to_send = json.dumps(data)
        logging.info(f"WS BROADCAST (USER): Sending to {len(connections)} connection(s) for user_id: {user_id}: {message_to_send}")
        
        # Create a list of tasks to send messages concurrently
        tasks = [connection.send_text(message_to_send) for connection in connections]
        # Gather results, which also handles exceptions
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, Exception):
                logging.error(f"WS BROADCAST ERROR (USER): Could not send message to a user. Error: {result}")


# Create a single, globally accessible instance of the manager.
manager = ConnectionManager()