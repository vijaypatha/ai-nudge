# File Path: backend/api/rest/conversations.py
# --- CORRECTED: Uses the new RecommendationSlateResponse model to prevent 500 Internal Server Errors.

import logging
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
import uuid
from sqlmodel import Session
from data.models.user import User
from api.security import get_current_user_from_token
from data.models.message import Message, MessageWithDraft, MessageDirection, MessageStatus
# --- MODIFIED: Use the base Pydantic model for the response ---
from data.models.campaign import RecommendationSlateResponse
from pydantic import BaseModel
from data import crm as crm_service
from agent_core import orchestrator

router = APIRouter(tags=["Conversations"])

class ConversationSummary(BaseModel):
    id: str
    client_id: uuid.UUID
    client_name: str
    last_message: str
    last_message_time: str
    unread_count: int

# --- MODIFIED: The response model now uses the safe Pydantic schema for recommendations ---
class ConversationDetailResponse(BaseModel):
    messages: List[MessageWithDraft]
    immediate_recommendations: Optional[RecommendationSlateResponse] = None
    active_plan: Optional[RecommendationSlateResponse] = None
    
    class Config:
        from_attributes = True

class SendReplyPayload(BaseModel):
    content: str


@router.get("/conversations/", response_model=List[ConversationSummary])
async def get_conversation_list(current_user: User = Depends(get_current_user_from_token)):
    """Retrieves a summary of all conversations for the logged-in user."""
    try:
        summaries = crm_service.get_conversation_summaries(user_id=current_user.id)
        return summaries
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch conversations: {str(e)}")


@router.get("/messages/", response_model=ConversationDetailResponse)
async def get_conversation_history_by_client_id(
    client_id: uuid.UUID,
    current_user: User = Depends(get_current_user_from_token)
):
    """
    Retrieves message history and separates active AI recommendations into an immediate
    slate and a long-term plan.
    """
    try:
        with Session(crm_service.engine) as session:
            history = crm_service.get_conversation_history(client_id=client_id, user_id=current_user.id)
            
            # --- MODIFIED: Fetch ALL active slates and separate them ---
            all_active_slates = crm_service.get_all_active_slates_for_client(
                client_id=client_id, user_id=current_user.id, session=session
            )
            
            immediate_rec_slate = next((s for s in all_active_slates if not s.is_plan), None)
            active_plan_slate = next((s for s in all_active_slates if s.is_plan), None)

        return ConversationDetailResponse(
            messages=history if history else [],
            immediate_recommendations=immediate_rec_slate,
            active_plan=active_plan_slate
        )
    except Exception as e:
        logging.error(f"Error fetching messages for client {client_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch messages.")



@router.post("/conversations/{client_id}/send_reply/", response_model=Message)
async def send_reply(
    client_id: uuid.UUID,
    payload: SendReplyPayload,
    current_user: User = Depends(get_current_user_from_token)
):
    """Sends a new message from the user to a client."""
    try:
        client = crm_service.get_client_by_id(client_id=client_id, user_id=current_user.id)
        if not client:
            raise HTTPException(status_code=404, detail="Client not found.")

        was_sent = await orchestrator.orchestrate_send_message_now(
            client_id=client_id,
            content=payload.content,
            user_id=current_user.id
        )

        if not was_sent:
            raise HTTPException(status_code=500, detail="Failed to send message.")

        new_message = Message(
            client_id=client_id,
            user_id=current_user.id,
            content=payload.content,
            direction=MessageDirection.OUTBOUND,
            status=MessageStatus.SENT
        )
        crm_service.save_message(new_message)
        return new_message

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send reply: {str(e)}")


@router.get("/scheduled-messages/", response_model=List)
async def get_scheduled_messages(
    client_id: Optional[uuid.UUID] = Query(None),
    current_user: User = Depends(get_current_user_from_token)
):
    """Get scheduled messages, optionally filtered by client_id."""
    try:
        if client_id:
            client = crm_service.get_client_by_id(client_id=client_id, user_id=current_user.id)
            if not client:
                raise HTTPException(status_code=404, detail="Client not found.")
            return crm_service.get_scheduled_messages_for_client(client_id=client_id, user_id=current_user.id)
        else:
            return crm_service.get_all_scheduled_messages(user_id=current_user.id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch scheduled messages: {str(e)}")