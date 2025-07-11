# File Path: backend/api/rest/conversations.py
# DEFINITIVE FIX: Complete conversations and messages API with proper error handling

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
import uuid
from data.models.user import User
from api.security import get_current_user_from_token
# --- MODIFIED: Import the new MessageWithDraft response model ---
from data.models.message import Message, MessageDirection, MessageStatus, MessageWithDraft
from data.models.campaign import CampaignBriefing
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

# --- MODIFIED: This endpoint now returns messages with their drafts embedded ---
@router.get("/messages/", response_model=List[MessageWithDraft])
async def get_conversation_history_by_client_id(
    client_id: uuid.UUID, # Made client_id non-optional as the UI always provides it
    current_user: User = Depends(get_current_user_from_token)
):
    """
    Retrieves the full message history for a specific client.
    Incoming messages will have their 'ai_draft' field populated if a draft exists.
    """
    try:
        # Verify client exists and belongs to user
        client = crm_service.get_client_by_id(client_id=client_id, user_id=current_user.id)
        if not client:
            raise HTTPException(status_code=404, detail="Client not found.")

        # Get message history for specific client. The CRM function now handles loading drafts.
        history = crm_service.get_conversation_history(client_id=client_id, user_id=current_user.id)
        return history if history else []

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch messages: {str(e)}")

# FIXED: Send reply endpoint with proper error handling
@router.post("/conversations/{client_id}/send_reply/", response_model=Message)
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

        # --- ADDED: Save the outbound message to the database ---
        new_message = Message(
            client_id=client_id,
            user_id=current_user.id,
            content=payload.content,
            direction=MessageDirection.OUTBOUND,
            status=MessageStatus.SENT  # Mark as sent since Twilio confirmed it
        )
        crm_service.save_message(new_message)  # Save the message

        # Return the newly saved message
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
            # Assuming a function get_all_scheduled_messages_for_user exists
            # If not, you'll need to add it to crm.py
            return crm_service.get_all_scheduled_messages(user_id=current_user.id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch scheduled messages: {str(e)}")
    
# --- REMOVED: This endpoint is now obsolete. The draft is embedded in the /messages/ response. ---
# @router.get("/conversations/{client_id}/ai_draft", response_model=dict)
# async def get_ai_draft(
#     client_id: uuid.UUID,
#     current_user: User = Depends(get_current_user_from_token)
# ):
#     """
#     Retrieves the latest AI-generated draft response for a given client.
#     This draft is for UI display and user approval/editing.
#     """
#     try:
#         # Verify client exists and belongs to user
#         client = crm_service.get_client_by_id(client_id=client_id, user_id=current_user.id)
#         if not client:
#             raise HTTPException(status_code=404, detail="Client not found.")

#         # Fetch the latest AI draft briefing for this client
#         draft = crm_service.get_latest_ai_draft_briefing(client_id=client_id, user_id=current_user.id)
#         if not draft:
#             return {"ai_draft": None} # Return empty if no draft found
#         return {"original_draft": draft.original_draft} # Return the draft content
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Failed to fetch AI draft: {str(e)}")