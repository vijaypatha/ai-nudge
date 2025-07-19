# File Path: backend/api/rest/scheduled_messages.py
# File Path: backend/api/rest/scheduled_messages.py

from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional
from uuid import UUID
from data.models.user import User
from data.models.message import ScheduledMessage, ScheduledMessageUpdate, ScheduledMessageCreate
from data import crm as crm_service
from api.security import get_current_user_from_token
from celery_tasks import send_scheduled_message_task
import logging

router = APIRouter(
    prefix="/scheduled-messages",
    tags=["Scheduled Messages"]
)

@router.post("", response_model=ScheduledMessage, status_code=status.HTTP_201_CREATED)
async def create_scheduled_message(
    message_data: ScheduledMessageCreate,
    current_user: User = Depends(get_current_user_from_token)
):
    """
    Schedules a new message to be sent at a future time.
    """
    try:
        # Verify the client belongs to the user before scheduling
        client = crm_service.get_client_by_id(client_id=message_data.client_id, user_id=current_user.id)
        if not client:
            raise HTTPException(status_code=404, detail="Client not found.")

        new_message = crm_service.create_scheduled_message(
            message_data=message_data,
            user_id=current_user.id
        )

        # Schedule the Celery task to send the message at the specified time
        send_scheduled_message_task.apply_async(
            (str(new_message.id),),
            eta=new_message.scheduled_at
        )
        logging.info(f"Scheduled message {new_message.id} for client {new_message.client_id} at {new_message.scheduled_at}")

        return new_message
    except Exception as e:
        logging.error(f"Failed to schedule message: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to schedule message: {str(e)}")


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
    """
    Updates a scheduled message. This can be used to change content, time, or status (e.g., to 'cancelled').
    """
    message = crm_service.get_scheduled_message_by_id(message_id)
    if not message or message.user_id != current_user.id:
         raise HTTPException(status_code=404, detail="Scheduled message not found.")

    updated_message = crm_service.update_scheduled_message(
        message_id=message_id,
        update_data=message_data.model_dump(exclude_unset=True),
        user_id=current_user.id
    )
    
    if not updated_message:
        raise HTTPException(status_code=404, detail="Scheduled message not found during update.")
    
    # If the scheduled time was changed, you would ideally revoke the old task and schedule a new one.
    # This simplified example does not handle task revocation.
    
    return updated_message

@router.delete("/{message_id}", status_code=204)
async def delete_scheduled_message(
    message_id: UUID,
    current_user: User = Depends(get_current_user_from_token)
):
    """
    Permanently deletes a scheduled message.
    """
    message = crm_service.get_scheduled_message_by_id(message_id)
    if not message or message.user_id != current_user.id:
         raise HTTPException(status_code=404, detail="Scheduled message not found.")

    # Note: Also consider revoking the Celery task if it was scheduled.
    success = crm_service.delete_scheduled_message(message_id=message_id, user_id=current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Scheduled message not found during deletion.")
    return