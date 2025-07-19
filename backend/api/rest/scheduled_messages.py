# File Path: backend/api/rest/scheduled_messages.py
# --- FULLY REVISED AND HARDENED ---

import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID

import pytz
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from api.security import get_current_user_from_token
from celery_worker import celery_app
from data import crm as crm_service
from data.database import engine
from data.models.message import (MessageStatus, ScheduledMessage,
                                 ScheduledMessageCreate, ScheduledMessageUpdate)
from data.models.user import User

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
    Schedules a new message, handling time zones and creating a Celery task.
    """
    try:
        # 1. Validate timezone and client ownership
        try:
            tz = pytz.timezone(message_data.timezone)
        except pytz.UnknownTimeZoneError:
            raise HTTPException(status_code=400, detail=f"Unknown timezone: '{message_data.timezone}'")

        client = crm_service.get_client_by_id(client_id=message_data.client_id, user_id=current_user.id)
        if not client:
            raise HTTPException(status_code=404, detail="Client not found.")

        # 2. Convert local time from frontend to UTC for storage
        local_time = message_data.scheduled_at_local
        if local_time.tzinfo is None:
            local_time = tz.localize(local_time)

        utc_time = local_time.astimezone(pytz.utc)

        # 3. Save the record to our database first
        with Session(engine) as session:
            db_message = ScheduledMessage(
                client_id=message_data.client_id,
                user_id=current_user.id,
                content=message_data.content,
                scheduled_at_utc=utc_time,
                timezone=message_data.timezone,
                status=MessageStatus.PENDING,
            )
            session.add(db_message)
            session.commit()
            session.refresh(db_message)

        # 4. Create the Celery task with the message ID
        from celery_tasks import send_scheduled_message_task
        task = send_scheduled_message_task.apply_async(
            (str(db_message.id),),  # Only pass the message ID
            eta=utc_time
        )
        logging.info(f"API: Scheduled message task {task.id} for message {db_message.id} at {utc_time} UTC.")

        # 5. Update the message with the task ID
        with Session(engine) as session:
            db_message.celery_task_id = task.id
            session.add(db_message)
            session.commit()
            session.refresh(db_message)
            return db_message

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"API: Failed to schedule message: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error while scheduling message.")


@router.put("/{message_id}", response_model=ScheduledMessage)
async def update_scheduled_message(
    message_id: UUID,
    message_data: ScheduledMessageUpdate,
    current_user: User = Depends(get_current_user_from_token)
):
    """
    Updates a pending scheduled message. Revokes the old Celery task and creates a new one.
    """
    with Session(engine) as session:
        db_message = crm_service.get_scheduled_message_by_id(message_id)
        if not db_message or db_message.user_id != current_user.id:
             raise HTTPException(status_code=404, detail="Scheduled message not found.")

        if db_message.status != MessageStatus.PENDING:
            raise HTTPException(status_code=400, detail="Can only edit messages that are pending.")

        # 1. Revoke the old Celery task
        if db_message.celery_task_id:
            celery_app.control.revoke(db_message.celery_task_id)
            logging.info(f"API: Revoked old task {db_message.celery_task_id} for message {message_id}.")

        # 2. Update fields
        update_dict = message_data.model_dump(exclude_unset=True)
        db_message.content = update_dict.get("content", db_message.content)
        new_timezone_str = update_dict.get("timezone", db_message.timezone)

        # 3. Recalculate UTC time if time or timezone changed
        new_local_time = update_dict.get("scheduled_at_local")
        if new_local_time:
            try:
                tz = pytz.timezone(new_timezone_str)
                if new_local_time.tzinfo is None:
                    new_local_time = tz.localize(new_local_time)
                db_message.scheduled_at_utc = new_local_time.astimezone(pytz.utc)
                db_message.timezone = new_timezone_str
            except pytz.UnknownTimeZoneError:
                raise HTTPException(status_code=400, detail=f"Unknown timezone: '{new_timezone_str}'")

        # 4. Schedule a new task with the message ID
        from celery_tasks import send_scheduled_message_task
        new_task = send_scheduled_message_task.apply_async(
            (str(db_message.id),),  # Only pass the message ID
            eta=db_message.scheduled_at_utc
        )
        db_message.celery_task_id = new_task.id
        logging.info(f"API: Scheduled new task {new_task.id} for updated message {message_id}.")

        session.add(db_message)
        session.commit()
        session.refresh(db_message)
        return db_message


@router.delete("/{message_id}", status_code=200, response_model=ScheduledMessage)
async def cancel_scheduled_message(
    message_id: UUID,
    current_user: User = Depends(get_current_user_from_token)
):
    """
    Cancels a pending scheduled message by updating its status to 'cancelled'
    and revoking its Celery task. This is a soft delete for audit purposes.
    """
    db_message = crm_service.get_scheduled_message_by_id(message_id)
    if not db_message or db_message.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Scheduled message not found.")

    if db_message.status != MessageStatus.PENDING:
        raise HTTPException(status_code=400, detail="Message is not pending and cannot be cancelled.")

    # 1. Revoke the Celery task
    if db_message.celery_task_id:
        celery_app.control.revoke(db_message.celery_task_id)
        logging.info(f"API: Revoked task {db_message.celery_task_id} for cancelled message {message_id}.")

    # 2. Use the CRM function for soft-delete
    cancelled_message = crm_service.cancel_scheduled_message(message_id=message_id, user_id=current_user.id)
    if not cancelled_message:
         # This case should be rare given the checks above, but good for safety
         raise HTTPException(status_code=404, detail="Failed to cancel message.")

    return cancelled_message


@router.get("", response_model=List[ScheduledMessage])
async def get_all_scheduled_messages(
    client_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user_from_token)
):
    """
    Get all scheduled messages for the user, optionally filtered by client.
    """
    try:
        # This logic remains correct.
        if client_id:
            return crm_service.get_scheduled_messages_for__client(user_id=current_user.id, client_id=client_id)
        else:
            return crm_service.get_all_scheduled_messages(user_id=current_user.id)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch scheduled messages.")