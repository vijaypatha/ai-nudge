# File Path: backend/api/rest/scheduled_messages.py
# File Path: backend/api/rest/scheduled_messages.py

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from uuid import UUID
from data.models.user import User
from data.models.message import ScheduledMessage, ScheduledMessageUpdate
from data import crm as crm_service
from api.security import get_current_user_from_token

router = APIRouter(
    prefix="/scheduled-messages",
    tags=["Scheduled Messages"]
)

# AFTER
@router.get("", response_model=List[ScheduledMessage])
async def get_scheduled_messages(
    client_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user_from_token)
):
    """
    Get scheduled messages. If client_id is provided, it filters for that client.
    Otherwise, it returns all scheduled messages for the current user.
    """
    try:
        if client_id:
            return crm_service.get_scheduled_messages_for_client(
                user_id=current_user.id,
                client_id=client_id
            )
        else:
            return crm_service.get_all_scheduled_messages(user_id=current_user.id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch scheduled messages: {str(e)}")

@router.put("/{message_id}", response_model=ScheduledMessage)
async def update_scheduled_message(
    message_id: UUID,
    message_data: ScheduledMessageUpdate,
    current_user: User = Depends(get_current_user_from_token)
):
    message = crm_service.get_scheduled_message_by_id(message_id)
    if not message or message.user_id != current_user.id:
         raise HTTPException(status_code=404, detail="Scheduled message not found.")

    # --- FIX: Pass the user_id to the update function ---
    updated_message = crm_service.update_scheduled_message(
        message_id=message_id,
        update_data=message_data.model_dump(exclude_unset=True),
        user_id=current_user.id
    )
    
    if not updated_message:
        raise HTTPException(status_code=404, detail="Scheduled message not found during update.")
    return updated_message

@router.delete("/{message_id}", status_code=204)
async def delete_scheduled_message(
    message_id: UUID,
    current_user: User = Depends(get_current_user_from_token)
):
    message = crm_service.get_scheduled_message_by_id(message_id)
    if not message or message.user_id != current_user.id:
         raise HTTPException(status_code=404, detail="Scheduled message not found.")

    # --- FIX: Pass the user_id to the delete function ---
    success = crm_service.delete_scheduled_message(message_id=message_id, user_id=current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Scheduled message not found during deletion.")
    return