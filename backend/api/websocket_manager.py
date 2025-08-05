# backend/api/websocket_manager.py
# --- FINAL VERSION: Manages process-local connections for a Redis Pub/Sub architecture ---

import logging
from collections import defaultdict
from fastapi import WebSocket
from typing import List, Dict, Set
import json
import asyncio

class ConnectionManager:
    """
    Manages active WebSocket connections FOR A SINGLE PROCESS.
    This instance's state is not shared with other web or worker processes.
    It is controlled by the Redis listener in `main.py`.
    """
    def __init__(self):
        # These dictionaries are local to each process (web server or worker)
        self.client_connections: Dict[str, List[WebSocket]] = defaultdict(list)
        # This dictionary holds user-specific connections *only for the process it runs in*.
        self.user_connections: Dict[str, Set[WebSocket]] = defaultdict(set)
        logging.info("WebSocket ConnectionManager initialized for this process.")

    # --- Client-specific methods (for chat rooms, unchanged) ---
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

    # --- User-specific methods (Now much simpler) ---
    async def connect_user(self, websocket: WebSocket, user_id: str):
        """
        Accepts a new user connection and adds it to this process's local connection pool.
        The "last-one-in-wins" logic is still included to handle browser tab refreshes gracefully.
        """
        # This check prevents having multiple connections for the same user in the *same process*.
        if user_id in self.user_connections and self.user_connections[user_id]:
            existing_connections = list(self.user_connections[user_id])
            logging.warning(f"WS RECONCILE: User {user_id} has old connections in this process. Closing them.")
            for conn in existing_connections:
                try:
                    # Await the close operation to ensure it completes.
                    await conn.close(code=1012, reason="A new connection was established.")
                except RuntimeError:
                    # This can happen if the connection is already dead.
                    logging.info(f"WS RECONCILE: Could not close an already dead connection for user {user_id}.")
                    pass
            self.user_connections[user_id].clear()

        # The websocket endpoint is responsible for `await websocket.accept()`.
        # This method just tracks the accepted connection.
        self.user_connections[user_id].add(websocket)
        logging.info(f"WS CONNECT (USER): New connection for user_id: {user_id} added to local manager.")

    def disconnect_user(self, websocket: WebSocket, user_id: str):
        """Removes a user's WebSocket connection from this process's local pool."""
        self.user_connections[user_id].discard(websocket)
        logging.info(f"WS DISCONNECT (USER): Connection closed for user_id: {user_id}. {len(self.user_connections.get(user_id, set()))} connection(s) remain in this process.")

    # --- NEW METHOD: Sends messages to locally-managed connections ---
    async def send_to_user_connections(self, user_id: str, data: dict):
        """
        Sends a message to all WebSockets connected for a specific user WITHIN THIS PROCESS.
        This method is called by the central Redis listener in main.py.
        """
        # It's normal for a process to have no connections for a given user,
        # as the user might be connected to a different server process on Render.
        if user_id not in self.user_connections:
            return

        connections = self.user_connections.get(user_id, set())
        message_to_send = json.dumps(data)
        logging.info(f"WS SEND (from Pub/Sub): Sending to {len(connections)} local connection(s) for user_id: {user_id}: {message_to_send}")

        # Use a copy of the connections set to avoid issues if it's modified during iteration (e.g., by a disconnect)
        for connection in list(connections):
            try:
                await connection.send_text(message_to_send)
            except Exception as e:
                # If sending fails, the connection is likely dead. Log the error and remove it.
                logging.error(f"WS SEND ERROR: Could not send message to a connection for user {user_id}. Removing it. Error: {e}")
                self.disconnect_user(connection, user_id)

# Create a single, globally accessible instance of the manager.
manager = ConnectionManager()