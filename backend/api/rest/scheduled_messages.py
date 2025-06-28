# File Path: backend/api/rest/scheduled_messages.py
# Purpose: Defines API endpoints for managing scheduled messages.
# CORRECTED VERSION: Added missing endpoints for complete CRUD operations

from fastapi import APIRouter, HTTPException, status
from typing import List
from uuid import UUID
from data.models.message import ScheduledMessage, ScheduledMessageUpdate
from data import crm as crm_service

router = APIRouter(
    prefix="/scheduled-messages",
    tags=["Scheduled Messages"]
)

@router.get("/", response_model=List[ScheduledMessage])
async def get_all_scheduled_messages():
    """Get all scheduled messages from the database."""
    try:
        return crm_service.get_all_scheduled_messages()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch scheduled messages: {str(e)}")

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

@router.delete("/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scheduled_message(message_id: UUID):
    """Delete a scheduled message by ID."""
    try:
        # You'll need to add this function to crm.py
        success = crm_service.delete_scheduled_message(message_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scheduled message not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete scheduled message: {str(e)}")
