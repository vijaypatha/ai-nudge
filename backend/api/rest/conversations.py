# File Path: backend/api/rest/conversations.py
from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Dict, Any
import uuid

# --- MODIFIED: Import User model and security dependency ---
from data.models.user import User
from api.security import get_current_user_from_token

from data import crm as crm_service
from agent_core import orchestrator
from data.models.message import Message
from pydantic import BaseModel

router = APIRouter(
    prefix="/conversations",
    tags=["Conversations"]
)

class ConversationSummary(BaseModel):
    id: str
    client_id: uuid.UUID
    client_name: str
    last_message: str
    last_message_time: str
    unread_count: int

class SendReplyPayload(BaseModel):
    content: str

# --- MODIFIED: Added security dependency ---
@router.get("/", response_model=List[ConversationSummary])
async def get_conversation_list(current_user: User = Depends(get_current_user_from_token)):
    summaries = crm_service.get_conversation_summaries(user_id=current_user.id)
    return summaries

# --- MODIFIED: Added security dependency and tenant-aware logic ---
@router.get("/{client_id}", response_model=List[Message])
async def get_conversation_history(client_id: uuid.UUID, current_user: User = Depends(get_current_user_from_token)):
    history = crm_service.get_conversation_history(client_id=client_id, user_id=current_user.id)
    return history

# --- MODIFIED: Added security dependency and tenant-aware logic ---
@router.post("/{client_id}/send_reply", status_code=status.HTTP_200_OK)
async def send_reply(client_id: uuid.UUID, payload: SendReplyPayload, current_user: User = Depends(get_current_user_from_token)):
    was_sent = await orchestrator.orchestrate_send_message_now(
        client_id=client_id,
        content=payload.content,
        user_id=current_user.id
    )
    if not was_sent:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send message via Twilio."
        )
    return {"status": "Message sent successfully"}