# backend/api/rest/scheduled_messages.py
# --- FINAL, CORRECTED VERSION ---

import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from uuid import UUID

import pytz
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session, select

from api.security import get_current_user_from_token
from celery_worker import celery_app
from data import crm as crm_service
from data.database import get_session
from data.models.message import (MessageStatus, ScheduledMessage,
                                 ScheduledMessageCreate, ScheduledMessageUpdate)
from data.models.user import User


class BulkScheduleCreate(BaseModel):
    client_ids: List[UUID]
    content: str
    scheduled_at_local: datetime
    timezone: str # Add timezone to bulk payload for consistency

router = APIRouter(
    prefix="/scheduled-messages",
    tags=["Scheduled Messages"]
)


@router.post("", response_model=ScheduledMessage, status_code=status.HTTP_201_CREATED)
async def create_scheduled_message(
    message_data: ScheduledMessageCreate,
    current_user: User = Depends(get_current_user_from_token),
    session: Session = Depends(get_session)
):
    """
    Schedules a new message, correctly prioritizing the timezone from the frontend payload.
    """
    try:
        # 1. Validate that the client belongs to the user
        client = crm_service.get_client_by_id(client_id=message_data.client_id, user_id=current_user.id)
        if not client:
            raise HTTPException(status_code=404, detail="Client not found.")

        # --- DEFINITIVE FIX IS HERE ---
        # Prioritize the timezone sent from the frontend payload. This reflects the user's actual intent.
        target_tz_str = message_data.timezone
        
        try:
            tz = pytz.timezone(target_tz_str)
        except pytz.UnknownTimeZoneError:
            raise HTTPException(status_code=400, detail=f"Invalid timezone provided: '{target_tz_str}'")

        # 2. Convert the user's local time to a UTC timestamp for storage
        local_time = message_data.scheduled_at_local

            # CRITICAL FIX: Ensure we're working with naive datetime for localization
        if local_time.tzinfo is not None:
        # If timezone info exists, convert to naive datetime first
                    local_time = local_time.replace(tzinfo=None)

            # Now localize the naive datetime to the target timezone
        local_time = tz.localize(local_time)
        utc_time = local_time.astimezone(pytz.utc)

        # Debug logging to verify conversion
        logging.info(f"Original input: {message_data.scheduled_at_local}")
        logging.info(f"Localized time: {local_time}")
        logging.info(f"UTC time stored: {utc_time}")


        # 3. Validate that the calculated UTC time is in the future
        if utc_time <= (datetime.now(timezone.utc) - timedelta(seconds=10)):
            raise HTTPException(status_code=400, detail="Scheduled time must be in the future.")

        # 4. Save the record to the database
        db_message = ScheduledMessage(
            client_id=message_data.client_id,
            user_id=current_user.id,
            content=message_data.content,
            scheduled_at_utc=utc_time,
            timezone=target_tz_str, # Store the timezone that was used
            status=MessageStatus.PENDING,
        )
        session.add(db_message)
        session.flush()  # Use flush to get the new message ID before committing

        # 5. Create the Celery task and link it to the message
        from celery_tasks import send_scheduled_message_task
        task = send_scheduled_message_task.apply_async((str(db_message.id),), eta=utc_time)
        db_message.celery_task_id = task.id
        
        session.add(db_message)
        session.commit()
        session.refresh(db_message)
        
        logging.info(f"API: Successfully scheduled message {db_message.id} with task {task.id}")
        return db_message

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error creating scheduled message: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create scheduled message.")


@router.post("/bulk", status_code=status.HTTP_202_ACCEPTED)
async def create_bulk_scheduled_messages(
    data: BulkScheduleCreate,
    current_user: User = Depends(get_current_user_from_token),
    session: Session = Depends(get_session)
):
    """
    Schedules a message for multiple clients, now using the single timezone from the payload.
    """
    if not data.client_ids:
        raise HTTPException(status_code=400, detail="client_ids list cannot be empty.")

    clients = crm_service.get_clients_by_ids(client_ids=data.client_ids, user_id=current_user.id)
    if len(clients) != len(data.client_ids):
        raise HTTPException(status_code=403, detail="One or more clients not found or do not belong to the user.")

    # --- DEFINITIVE FIX IS HERE ---
    # Use the timezone from the payload for all clients in the bulk request.
    target_tz_str = data.timezone
    try:
        tz = pytz.timezone(target_tz_str)
    except pytz.UnknownTimeZoneError:
        raise HTTPException(status_code=400, detail=f"Invalid timezone provided: '{target_tz_str}'")

    local_time = data.scheduled_at_local
    if local_time.tzinfo is None:
        local_time = tz.localize(local_time)
    utc_time = local_time.astimezone(pytz.utc)

    if utc_time <= (datetime.now(timezone.utc) - timedelta(seconds=10)):
        raise HTTPException(status_code=400, detail="Scheduled time must be in the future.")

    for client in clients:
        db_message = ScheduledMessage(
            client_id=client.id,
            user_id=current_user.id,
            content=data.content,
            scheduled_at_utc=utc_time,
            timezone=target_tz_str,
            status=MessageStatus.PENDING,
        )
        session.add(db_message)
        session.flush()

        from celery_tasks import send_scheduled_message_task
        task = send_scheduled_message_task.apply_async((str(db_message.id),), eta=utc_time)
        db_message.celery_task_id = task.id
        session.add(db_message)

    session.commit()
    return {"detail": f"Successfully scheduled messages for {len(clients)} clients."}


@router.put("/{message_id}", response_model=ScheduledMessage)
async def update_scheduled_message(
    message_id: UUID,
    message_data: ScheduledMessageUpdate,
    current_user: User = Depends(get_current_user_from_token),
    session: Session = Depends(get_session)
):
    db_message = session.exec(select(ScheduledMessage).where(
        ScheduledMessage.id == message_id, 
        ScheduledMessage.user_id == current_user.id
    )).first()
    
    if not db_message:
         raise HTTPException(status_code=404, detail="Scheduled message not found.")

    if db_message.status != MessageStatus.PENDING:
        raise HTTPException(status_code=400, detail="Can only edit messages that are pending.")

    if db_message.celery_task_id:
        from celery_worker import celery_app
        celery_app.control.revoke(db_message.celery_task_id)

    update_dict = message_data.model_dump(exclude_unset=True)
    db_message.content = update_dict.get("content", db_message.content)

    from celery_tasks import send_scheduled_message_task
    new_task = send_scheduled_message_task.apply_async((str(db_message.id),), eta=db_message.scheduled_at_utc)
    db_message.celery_task_id = new_task.id

    session.add(db_message)
    session.commit()
    session.refresh(db_message)
    return db_message


@router.delete("/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_scheduled_message(
    message_id: UUID,
    current_user: User = Depends(get_current_user_from_token),
    session: Session = Depends(get_session)
):
    db_message = session.exec(select(ScheduledMessage).where(
        ScheduledMessage.id == message_id,
        ScheduledMessage.user_id == current_user.id
    )).first()

    if not db_message:
        raise HTTPException(status_code=404, detail="Scheduled message not found.")
    
    if db_message.status != MessageStatus.PENDING:
        raise HTTPException(status_code=400, detail="Message is not pending and cannot be cancelled.")
    
    if db_message.celery_task_id:
        from celery_worker import celery_app
        celery_app.control.revoke(db_message.celery_task_id)

    db_message.status = MessageStatus.CANCELLED
    session.add(db_message)
    session.commit()
    return None


@router.get("", response_model=List[ScheduledMessage])
async def get_all_scheduled_messages(
    client_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user_from_token),
    session: Session = Depends(get_session)
):
    statement = select(ScheduledMessage).where(ScheduledMessage.user_id == current_user.id)
    if client_id:
        statement = statement.where(ScheduledMessage.client_id == client_id)
    
    results = session.exec(statement).all()
    return results