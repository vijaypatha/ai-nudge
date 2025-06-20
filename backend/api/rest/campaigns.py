# ---
# File Path: backend/api/rest/campaigns.py
# Purpose: Defines API endpoints for outbound and scheduled communications.
# ---

from fastapi import APIRouter, HTTPException, status
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone

from backend.data.models.message import ScheduledMessage, ScheduledMessageCreate, MessageStatus, SendMessageImmediate

router = APIRouter(
    prefix="/campaigns",
    tags=["Campaigns"]
)

@router.post("/messages/schedule", response_model=ScheduledMessage, status_code=status.HTTP_201_CREATED)
async def schedule_message(message_data: ScheduledMessageCreate):
    """Schedules a single message."""
    from backend.agent_core.tools import communication as comm_tool
    if message_data.scheduled_at.tzinfo is None:
        message_data.scheduled_at = message_data.scheduled_at.replace(tzinfo=timezone.utc)
    scheduled_msg = comm_tool.schedule_message(message_data)
    return scheduled_msg

@router.get("/messages", response_model=List[ScheduledMessage])
async def get_all_scheduled_messages(status: Optional[MessageStatus] = None):
    """Retrieves all scheduled messages."""
    from backend.agent_core.tools import communication as comm_tool
    messages = comm_tool.get_scheduled_messages(status_filter=status)
    return messages

@router.post("/messages/send-now", status_code=status.HTTP_200_OK)
async def send_message_now(message_data: SendMessageImmediate):
    """Sends a message immediately."""
    from backend.agent_core.tools import communication as comm_tool
    from backend.data import crm as crm_service

    client = crm_service.get_client_by_id_mock(message_data.client_id)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
    
    success = comm_tool.send_message_now(message_data.client_id, message_data.content)
    
    if success:
        return {"message": "Message sent successfully!", "client_id": message_data.client_id}
    else:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to send message.")

@router.post("/messages/{message_id}/mark-sent", response_model=ScheduledMessage)
async def mark_message_as_sent(message_id: UUID):
    """Marks a specific scheduled message as 'sent'."""
    from backend.agent_core.tools import communication as comm_tool
    updated_msg = comm_tool.mark_message_as_sent(message_id)
    if updated_msg:
        return updated_msg
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scheduled message not found.")

@router.post("/messages/{message_id}/mark-failed", response_model=ScheduledMessage)
async def mark_message_as_failed(message_id: UUID, error_message: str):
    """Marks a specific scheduled message as 'failed'."""
    from backend.agent_core.tools import communication as comm_tool
    updated_msg = comm_tool.mark_message_as_failed(message_id, error_message)
    if updated_msg:
        return updated_msg
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scheduled message not found.")