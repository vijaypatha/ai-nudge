# ---
# File Path: backend/api/rest/inbox.py
# Purpose: Defines API endpoints for handling incoming messages that require AI processing.
# ---

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Dict, Any
import uuid

from backend.data.models.message import IncomingMessage

router = APIRouter(
    prefix="/inbox",
    tags=["Inbox"]
)

# CORRECTED: The path is now standardized to be relative and slash-free.
@router.post("/receive-message", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
async def receive_incoming_message(message: IncomingMessage):
    """Simulates receiving an incoming message from a client and generates an AI draft."""
    # Local imports to prevent circular dependencies
    from backend.agent_core import orchestrator
    from backend.data import crm as crm_service

    client_exists = crm_service.get_client_by_id_mock(message.client_id)
    if not client_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Client with ID {message.client_id} not found."
        )
    orchestration_result = await orchestrator.handle_incoming_message(
        client_id=message.client_id,
        incoming_message_content=message.content
    )
    return orchestration_result
