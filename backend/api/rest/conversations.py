# ---
# File Path: backend/api/rest/conversations.py
# Purpose: Defines API endpoints for fetching conversation data and sending messages.
# ---

from fastapi import APIRouter, HTTPException, status
from typing import List, Dict, Any
import uuid

from data import crm as crm_service
from agent_core import orchestrator
from data.models.message import Message
from pydantic import BaseModel

router = APIRouter(
    prefix="/conversations",
    tags=["Conversations"]
)

# --- Pydantic Models for API Data Shapes ---
class ConversationSummary(BaseModel):
    id: str
    client_id: uuid.UUID
    client_name: str
    last_message: str
    last_message_time: str
    unread_count: int

class SendReplyPayload(BaseModel):
    content: str

# --- API Endpoints ---

@router.get("/", response_model=List[ConversationSummary])
async def get_conversation_list():
    """
    Fetches a list of conversation summaries for the dashboard's left panel.
    Each summary includes the client's name and the last message exchanged.
    """
    summaries = crm_service.get_conversation_summaries()
    return summaries

@router.get("/{client_id}", response_model=List[Message])
async def get_conversation_history(client_id: uuid.UUID):
    """
    Fetches the full message history for a specific client.
    This powers the main chat window in the dashboard.
    """
    history = crm_service.get_conversation_history(client_id)
    if not history:
        # Return an empty list if no history, which is a valid state.
        return []
    return history

@router.post("/{client_id}/send_reply", status_code=status.HTTP_200_OK)
async def send_reply(client_id: uuid.UUID, payload: SendReplyPayload):
    """
    Sends an immediate reply to a client from the dashboard composer.
    """
    was_sent = await orchestrator.orchestrate_send_message_now(
        client_id=client_id,
        content=payload.content
    )
    if not was_sent:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send message via Twilio."
        )
    return {"status": "Message sent successfully"}
