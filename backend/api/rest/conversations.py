# File Path: backend/api/rest/conversations.py
# DEFINITIVE FIX: Complete conversations and messages API with proper error handling

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
import uuid
from data.models.user import User
from api.security import get_current_user_from_token
from data.models.message import Message
from pydantic import BaseModel
from data import crm as crm_service
from agent_core import orchestrator

# Router with proper prefix handling
router = APIRouter(tags=["Conversations"])

class ConversationSummary(BaseModel):
    id: str
    client_id: uuid.UUID
    client_name: str
    last_message: str
    last_message_time: str
    unread_count: int

class SendReplyPayload(BaseModel):
    content: str

# FIXED: Conversations list endpoint
@router.get("/conversations/", response_model=List[ConversationSummary])
async def get_conversation_list(current_user: User = Depends(get_current_user_from_token)):
    """Retrieves a summary of all conversations for the logged-in user."""
    try:
        summaries = crm_service.get_conversation_summaries(user_id=current_user.id)
        return summaries
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch conversations: {str(e)}")

# FIXED: Messages endpoint with proper query parameter handling
@router.get("/messages/", response_model=List[Message])
async def get_conversation_history_by_client_id(
    client_id: Optional[uuid.UUID] = Query(None),
    current_user: User = Depends(get_current_user_from_token)
):
    """Retrieves the full message history for a specific client via query parameter."""
    try:
        if not client_id:
            # Return all messages for user if no client_id specified
            return crm_service.get_all_messages_for_user(user_id=current_user.id)
        
        # Verify client exists and belongs to user
        client = crm_service.get_client_by_id(client_id=client_id, user_id=current_user.id)
        if not client:
            raise HTTPException(status_code=404, detail="Client not found.")
        
        # Get message history for specific client
        history = crm_service.get_conversation_history(client_id=client_id, user_id=current_user.id)
        return history if history else []
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch messages: {str(e)}")

# FIXED: Send reply endpoint with proper error handling
@router.post("/conversations/{client_id}/send_reply/", status_code=201)
async def send_reply(
    client_id: uuid.UUID,
    payload: SendReplyPayload,
    current_user: User = Depends(get_current_user_from_token)
):
    """Sends a new message from the user to a client."""
    try:
        # Verify client exists and belongs to user
        client = crm_service.get_client_by_id(client_id=client_id, user_id=current_user.id)
        if not client:
            raise HTTPException(status_code=404, detail="Client not found.")
        
        # Send message via orchestrator
        was_sent = await orchestrator.orchestrate_send_message_now(
            client_id=client_id,
            content=payload.content,
            user_id=current_user.id
        )
        
        if not was_sent:
            raise HTTPException(status_code=500, detail="Failed to send message.")
        
        # Return the newly created message
        new_message = crm_service.get_last_message_for_client(client_id, current_user.id)
        return new_message
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send reply: {str(e)}")

# FIXED: Add missing scheduled messages endpoint
@router.get("/scheduled-messages/", response_model=List)
async def get_scheduled_messages(
    client_id: Optional[uuid.UUID] = Query(None),
    current_user: User = Depends(get_current_user_from_token)
):
    """Get scheduled messages, optionally filtered by client_id."""
    try:
        if client_id:
            # Verify client exists and belongs to user
            client = crm_service.get_client_by_id(client_id=client_id, user_id=current_user.id)
            if not client:
                raise HTTPException(status_code=404, detail="Client not found.")
            
            return crm_service.get_scheduled_messages_for_client(
                client_id=client_id, 
                user_id=current_user.id
            )
        else:
            return crm_service.get_all_scheduled_messages_for_user(
                user_id=current_user.id
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch scheduled messages: {str(e)}")
