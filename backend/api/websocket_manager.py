# backend/api/websocket_manager.py
# --- PATCHED: Enforces a single connection per user ---

import logging
from collections import defaultdict
from fastapi import WebSocket
from typing import List, Dict, Set
import json
import asyncio

class ConnectionManager:
    """
    Manages active WebSocket connections with a "last-one-in-wins" policy for users.
    - `client_connections`: For client-specific rooms (e.g., a conversation page).
    - `user_connections`: For user-specific notifications.
    """
    def __init__(self):
        self.client_connections: Dict[str, List[WebSocket]] = defaultdict(list)
        self.user_connections: Dict[str, Set[WebSocket]] = defaultdict(set)
        logging.info("WebSocket ConnectionManager initialized with client and user scopes.")

    # --- Client-specific methods (unchanged) ---
    async def connect_client(self, websocket: WebSocket, client_id: str):
        # This endpoint is for specific client views and can still allow multiple connections
        # if a user opens the same client conversation in multiple tabs.
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

    # --- User-specific methods (MODIFIED) ---
    async def connect_user(self, websocket: WebSocket, user_id: str):
        """
        Accepts a new user connection and enforces a single-connection policy.
        It closes any existing connections for the user before accepting the new one.
        """
        # --- BEGIN FIX: "Last one in wins" logic ---
        if user_id in self.user_connections and self.user_connections[user_id]:
            existing_connections = list(self.user_connections[user_id])
            logging.warning(f"WS RECONCILE: User {user_id} already has {len(existing_connections)} connection(s). Closing them.")
            
            # Close all old connections for this user
            for conn in existing_connections:
                try:
                    # Send a specific code indicating the reason for closure.
                    # 1012: Service Restart (a suitable code for a new session taking over)
                    await conn.close(code=1012, reason="A new connection was established.")
                except RuntimeError:
                    # This can happen if the connection is already dead.
                    logging.info(f"WS RECONCILE: Could not close an already dead connection for user {user_id}.")
                    pass
            self.user_connections[user_id].clear()
        # --- END FIX ---
        
        # Accept the new connection now that old ones are closed.
        await websocket.accept()
        self.user_connections[user_id].add(websocket)
        logging.info(f"WS CONNECT (USER): New, single connection for user_id: {user_id} accepted.")


    def disconnect_user(self, websocket: WebSocket, user_id: str):
        """Removes a user's WebSocket connection."""
        self.user_connections[user_id].discard(websocket)
        logging.info(f"WS DISCONNECT (USER): Connection closed for user_id: {user_id}. {len(self.user_connections[user_id])} connection(s) remain.")

    async def broadcast_to_user(self, user_id: str, data: dict):
        """Broadcasts a JSON payload to all connections for a specific user_id."""
        connections = self.user_connections.get(user_id)
        if not connections:
            logging.info(f"WS BROADCAST (USER): No active connections for user_id: {user_id}. Message not sent.")
            return

        message_to_send = json.dumps(data)
        logging.info(f"WS BROADCAST (USER): Sending to {len(connections)} connection(s) for user_id: {user_id}: {message_to_send}")
        
        tasks = [connection.send_text(message_to_send) for connection in connections]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, Exception):
                logging.error(f"WS BROADCAST ERROR (USER): Could not send message to a user. Error: {result}")


# Create a single, globally accessible instance of the manager.
manager = ConnectionManager()