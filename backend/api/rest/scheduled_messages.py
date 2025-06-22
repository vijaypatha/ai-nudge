# ---
# File Path: backend/api/rest/scheduled_messages.py
# Purpose: Defines API endpoints for managing scheduled messages.
# ---
from fastapi import APIRouter, HTTPException, status
from uuid import UUID
from data.models.message import ScheduledMessage, ScheduledMessageUpdate
from data import crm as crm_service

router = APIRouter(
    prefix="/scheduled-messages",
    tags=["Scheduled Messages"]
)

@router.put("/{message_id}", response_model=ScheduledMessage)
async def update_scheduled_message(message_id: UUID, message_data: ScheduledMessageUpdate):
    """
    Updates the content or scheduled date of a specific message.
    """
    updated_message = crm_service.update_scheduled_message(
        message_id=message_id,
        update_data=message_data.model_dump()
    )
    if not updated_message:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scheduled message not found.")

    return updated_message