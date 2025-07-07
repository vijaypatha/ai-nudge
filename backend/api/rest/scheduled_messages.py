# File Path: backend/api/rest/scheduled_messages.py
# DEFINITIVE FIX: This patch resolves the 500 Internal Server Error.
# The `get_scheduled_messages_for_client` function now correctly accepts
# the `client_id` query parameter from the frontend request.

from fastapi import APIRouter, HTTPException, Depends
from typing import List
from uuid import UUID
from data.models.user import User
from data.models.message import ScheduledMessage, ScheduledMessageUpdate
from data import crm as crm_service
from api.security import get_current_user_from_token

router = APIRouter(
    prefix="/scheduled-messages",
    tags=["Scheduled Messages"]
)

# --- MODIFIED: The endpoint path is now an empty string to avoid redirects. ---
# --- The function now accepts client_id and is secured. ---
@router.get("", response_model=List[ScheduledMessage])
async def get_scheduled_messages_for_client(
    client_id: UUID,
    current_user: User = Depends(get_current_user_from_token)
):
    """
    Get all scheduled messages for a specific client for the current user.
    """
    try:
        # The CRM service is called with both user_id and client_id to ensure
        # data is properly scoped and authorized.
        return crm_service.get_scheduled_messages_for_client(
            user_id=current_user.id,
            client_id=client_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch scheduled messages: {str(e)}")

@router.put("/{message_id}", response_model=ScheduledMessage)
async def update_scheduled_message(
    message_id: UUID,
    message_data: ScheduledMessageUpdate,
    current_user: User = Depends(get_current_user_from_token) # Secured this endpoint
):
    """
    Updates the content or scheduled date of a specific message.
    """
    # Verify the message belongs to the user before updating.
    message = crm_service.get_scheduled_message_by_id(message_id)
    if not message or message.user_id != current_user.id:
         raise HTTPException(status_code=404, detail="Scheduled message not found.")

    updated_message = crm_service.update_scheduled_message(
        message_id=message_id,
        update_data=message_data.model_dump()
    )
    
    if not updated_message:
        raise HTTPException(status_code=404, detail="Scheduled message not found.")
    return updated_message

@router.delete("/{message_id}", status_code=204)
async def delete_scheduled_message(
    message_id: UUID,
    current_user: User = Depends(get_current_user_from_token) # Secured this endpoint
):
    """Delete a scheduled message by ID."""
    # Verify the message belongs to the user before deleting.
    message = crm_service.get_scheduled_message_by_id(message_id)
    if not message or message.user_id != current_user.id:
         raise HTTPException(status_code=404, detail="Scheduled message not found.")

    success = crm_service.delete_scheduled_message(message_id)
    if not success:
        raise HTTPException(status_code=404, detail="Scheduled message not found during deletion.")
    return