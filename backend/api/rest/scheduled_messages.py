# File Path: backend/api/rest/scheduled_messages.py
# --- FULLY REVISED AND HARDENED ---

import logging
from datetime import datetime, timezone, time
from typing import List, Optional, Dict, Any
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
from data.models.client import Client
from data.database import get_session

# --- NEW: Pydantic model for the bulk endpoint ---
from pydantic import BaseModel
class BulkScheduleCreate(BaseModel):
    client_ids: List[UUID]
    content: str
    scheduled_at_local: datetime

router = APIRouter(
    prefix="/scheduled-messages",
    tags=["Scheduled Messages"]
)


# --- NEW: Bulk Scheduling Endpoint ---
@router.post("/bulk", status_code=status.HTTP_202_ACCEPTED)
async def create_bulk_scheduled_messages(
    data: BulkScheduleCreate,
    current_user: User = Depends(get_current_user_from_token)
):
    """
    Schedules a message for multiple clients, respecting each client's individual timezone.
    """
    if not data.client_ids:
        raise HTTPException(status_code=400, detail="client_ids list cannot be empty.")

    # 1. Fetch all requested clients in one query to validate ownership and get timezones
    clients = crm_service.get_clients_by_ids(client_ids=data.client_ids, user_id=current_user.id)
    if len(clients) != len(data.client_ids):
        raise HTTPException(status_code=403, detail="One or more clients not found or do not belong to the user.")

    # Create a map for easy timezone lookup
    client_tz_map = {client.id: client.timezone for client in clients}

    # 2. Iterate and create messages and tasks
    scheduled_tasks = 0
    with Session(engine) as session:
        for client_id in data.client_ids:
            # Determine the target timezone for this client
            target_tz_str = client_tz_map.get(client_id) or current_user.timezone or 'UTC'
            try:
                tz = pytz.timezone(target_tz_str)
            except pytz.UnknownTimeZoneError:
                logging.warning(f"API Bulk: Skipping client {client_id} due to unknown timezone '{target_tz_str}'")
                continue

            # Convert local time to UTC for this specific client
            local_time = data.scheduled_at_local
            if local_time.tzinfo is None:
                local_time = tz.localize(local_time)
            utc_time = local_time.astimezone(pytz.utc)

            if utc_time <= datetime.now(timezone.utc):
                logging.warning(f"API Bulk: Skipping client {client_id}, scheduled time is in the past.")
                continue

            # Create and save the DB record
            db_message = ScheduledMessage(
                client_id=client_id,
                user_id=current_user.id,
                content=data.content,
                scheduled_at_utc=utc_time,
                timezone=target_tz_str,
                status=MessageStatus.PENDING,
            )
            session.add(db_message)
            session.flush() # Flush to get the ID for the task

            # Create Celery task
            from celery_tasks import send_scheduled_message_task
            task = send_scheduled_message_task.apply_async((str(db_message.id),), eta=utc_time)
            db_message.celery_task_id = task.id
            session.add(db_message)
            scheduled_tasks += 1

        session.commit()

    return {"detail": f"Successfully scheduled {scheduled_tasks} out of {len(data.client_ids)} messages."}


@router.post("", response_model=ScheduledMessage, status_code=status.HTTP_201_CREATED)
async def create_scheduled_message(
    message_data: ScheduledMessageCreate,
    current_user: User = Depends(get_current_user_from_token)
):
    """
    Schedules a new message, handling time zones and creating a Celery task.
    Now uses recipient-centric timezone logic.
    """
    try:
        # 1. Fetch client to determine the correct timezone
        client = crm_service.get_client_by_id(client_id=message_data.client_id, user_id=current_user.id)
        if not client:
            raise HTTPException(status_code=404, detail="Client not found.")
            
        # --- MODIFIED: Use client's timezone first, fall back to user's, then UTC ---
        target_tz_str = client.timezone or current_user.timezone or 'UTC'

        try:
            tz = pytz.timezone(target_tz_str)
        except pytz.UnknownTimeZoneError:
            raise HTTPException(status_code=400, detail=f"Invalid timezone configured: '{target_tz_str}'")

        # 2. Convert local time from frontend to UTC for storage
        local_time = message_data.scheduled_at_local
        if local_time.tzinfo is None:
            local_time = tz.localize(local_time)

        utc_time = local_time.astimezone(pytz.utc)
        
        if utc_time <= datetime.now(timezone.utc):
            raise HTTPException(status_code=400, detail="Scheduled time must be in the future.")

        # 3. Save the record to our database first
        with Session(engine) as session:
            db_message = ScheduledMessage(
                client_id=message_data.client_id,
                user_id=current_user.id,
                content=message_data.content,
                scheduled_at_utc=utc_time,
                timezone=target_tz_str,
                status=MessageStatus.PENDING,
            )
            session.add(db_message)
            session.commit()
            session.refresh(db_message)

            # 4. Create the Celery task with the message ID
            from celery_tasks import send_scheduled_message_task
            task = send_scheduled_message_task.apply_async((str(db_message.id),), eta=utc_time)
            logging.info(f"API: Scheduled message task {task.id} for message {db_message.id} at {utc_time} UTC.")
            
            # 5. Update the message with the task ID
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
    current_user: User = Depends(get_current_user_from_token),
    session: Session = Depends(get_session)
):
    """
    Updates a pending scheduled message. Revokes the old Celery task and creates a new one.
    """
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

    # --- MODIFIED: Ensure timezone from client record is used if not provided in payload ---
    new_timezone_str = update_dict.get("timezone")
    if not new_timezone_str:
        client = crm_service.get_client_by_id(db_message.client_id, current_user.id)
        # --- NEW: Add a check for the client's existence ---
        if not client:
            logging.error(f"Data integrity error: ScheduledMessage {db_message.id} exists but Client {db_message.client_id} not found.")
            raise HTTPException(status_code=500, detail="Data integrity error: Client for message not found.")
        new_timezone_str = client.timezone or current_user.timezone or 'UTC'

    # 3. Recalculate UTC time if time or timezone changed
    new_local_time = update_dict.get("scheduled_at_local")
    if new_local_time:
        try:
            tz = pytz.timezone(new_timezone_str)
            # Naive datetime from frontend needs to be localized
            if new_local_time.tzinfo is None:
                localized_time = tz.localize(new_local_time)
            else: # If frontend sends aware datetime, just convert
                localized_time = new_local_time.astimezone(tz)

            db_message.scheduled_at_utc = localized_time.astimezone(pytz.utc)
            db_message.timezone = new_timezone_str
            db_message.content = update_dict.get("content", db_message.content)

        except pytz.UnknownTimeZoneError:
            raise HTTPException(status_code=400, detail=f"Unknown timezone: '{new_timezone_str}'")
    else: # Only content is being updated
         db_message.content = update_dict.get("content", db_message.content)

    # 4. Schedule a new task with the message ID
    from celery_tasks import send_scheduled_message_task
    new_task = send_scheduled_message_task.apply_async((str(db_message.id),), eta=db_message.scheduled_at_utc)
    db_message.celery_task_id = new_task.id
    logging.info(f"API: Scheduled new task {new_task.id} for updated message {message_id}.")

    # Update the message record
    session.add(db_message)
    session.commit()
    session.refresh(db_message)

    return db_message

# --- DELETE endpoint is unchanged, no modification needed ---
@router.delete("/{message_id}", status_code=200, response_model=ScheduledMessage)
async def cancel_scheduled_message(
    message_id: UUID,
    current_user: User = Depends(get_current_user_from_token)
):
    db_message = crm_service.get_scheduled_message_by_id(message_id)
    if not db_message or db_message.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Scheduled message not found.")
    if db_message.status != MessageStatus.PENDING:
        raise HTTPException(status_code=400, detail="Message is not pending and cannot be cancelled.")
    if db_message.celery_task_id:
        celery_app.control.revoke(db_message.celery_task_id)
        logging.info(f"API: Revoked task {db_message.celery_task_id} for cancelled message {message_id}.")
    cancelled_message = crm_service.cancel_scheduled_message(message_id=message_id, user_id=current_user.id)
    if not cancelled_message:
         raise HTTPException(status_code=404, detail="Failed to cancel message.")
    return cancelled_message

# --- GET endpoint is unchanged ---
@router.get("", response_model=List[ScheduledMessage])
async def get_all_scheduled_messages(
    client_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user_from_token)
):
    try:
        if client_id:
            return crm_service.get_scheduled_messages_for_client(client_id=client_id, user_id=current_user.id)
        else:
            return crm_service.get_all_scheduled_messages(user_id=current_user.id)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch scheduled messages.")