# File Path: backend/api/rest/inbox.py
# Purpose: Defines API endpoints for handling incoming messages that require AI processing.
# CORRECTED VERSION: Updated to use database functions instead of mock data

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Dict, Any
import uuid
from data.models.message import IncomingMessage
from agent_core import orchestrator

router = APIRouter(
    prefix="/inbox",
    tags=["Inbox"]
)

@router.post("/receive-message", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
async def receive_incoming_message(message: IncomingMessage):
    """Simulates receiving an incoming message from a client and generates an AI draft."""
    from agent_core import orchestrator
    from data import crm as crm_service
    
    # CORRECTED: Use database function instead of mock function
    client_exists = crm_service.get_client_by_id(message.client_id)
    if not client_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Client with ID {message.client_id} not found."
        )  # FIXED: Added missing closing parenthesis
    
    orchestration_result = await orchestrator.handle_incoming_message(
        client_id=message.client_id,
        incoming_message_content=message.content
    )  # FIXED: Added missing closing parenthesis
    
    return orchestration_result

@router.post("/receive-sms-mock", status_code=status.HTTP_200_OK)
async def receive_sms_mock(message: IncomingMessage):
    """
    MOCK ENDPOINT: Simulates receiving an SMS from a client.
    This triggers the full orchestration, including intel extraction.
    """
    await orchestrator.handle_incoming_message(
        client_id=message.client_id,
        incoming_message_content=message.content
    )  # FIXED: Added missing closing parenthesis
    
    return {"status": "message received and processed"}
