# backend/celery_tasks.py
# --- PRODUCTION-GRADE HARDENED VERSION ---

import logging
import asyncio
import uuid
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID
from celery import Celery
from sqlmodel import Session, select
from data.database import engine
from data.models.message import Message, MessageStatus, MessageDirection, MessageSource, MessageSenderType, ScheduledMessage
from data.models.user import User
from data.models.client import Client
from data import crm as crm_service
from integrations import twilio_outgoing

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Celery app configuration
REDIS_URL = "redis://redis:6379/0"  # Use the service name 'redis' from docker-compose

celery_app = Celery('ai_nudge')
celery_app.conf.update(
    broker=REDIS_URL,
    backend=REDIS_URL,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes max
    task_soft_time_limit=240,  # 4 minutes soft limit
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    broker_connection_retry_on_startup=True,
    broker_connection_max_retries=10,
    result_expires=3600,  # 1 hour
)

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_scheduled_message_task(self, message_id: str) -> dict:
    """
    Sends a scheduled message with production-grade error handling and monitoring.
    """
    message_uuid = UUID(message_id)
    session = None
    
    try:
        logger.info(f"CELERY: Starting scheduled message delivery for message {message_id}")
        
        # 1. Fetch the scheduled message with validation
        session = Session(engine)
        scheduled_message = session.exec(
            select(ScheduledMessage).where(ScheduledMessage.id == message_uuid)
        ).first()
        
        if not scheduled_message:
            logger.error(f"CELERY: Scheduled message {message_id} not found")
            return {"status": "error", "reason": "message_not_found"}
        
        if scheduled_message.status != MessageStatus.PENDING:
            logger.warning(f"CELERY: Scheduled message {message_id} is not pending (status: {scheduled_message.status})")
            return {"status": "skipped", "reason": "not_pending"}
        
        # 2. Validate user and client
        user = session.exec(select(User).where(User.id == scheduled_message.user_id)).first()
        if not user or not user.twilio_phone_number:
            logger.error(f"CELERY: User {scheduled_message.user_id} not found or missing Twilio number")
            self.update_state(state='FAILURE', meta={'error': 'user_not_found'})
            return {"status": "error", "reason": "user_not_found"}
        
        client = session.exec(
            select(Client).where(
                Client.id == scheduled_message.client_id,
                Client.user_id == scheduled_message.user_id
            )
        ).first()
        
        if not client or not client.phone:
            logger.error(f"CELERY: Client {scheduled_message.client_id} not found or missing phone")
            self.update_state(state='FAILURE', meta={'error': 'client_not_found'})
            return {"status": "error", "reason": "client_not_found"}
        
        # 3. Personalize content
        first_name = client.full_name.strip().split(' ')[0] if client.full_name else "there"
        personalized_content = scheduled_message.content.replace("[Client Name]", first_name)
        
        # 4. Send SMS with comprehensive retry logic
        max_sms_retries = 3
        sms_retry_delay = 2  # seconds
        
        sms_sent = False
        last_sms_error = None
        
        for attempt in range(max_sms_retries):
            try:
                logger.info(f"CELERY: SMS send attempt {attempt + 1} for message {message_id}")
                
                was_sent = twilio_outgoing.send_sms(
                    from_number=user.twilio_phone_number,
                    to_number=client.phone,
                    body=personalized_content
                )
                
                if was_sent:
                    sms_sent = True
                    logger.info(f"CELERY: SMS sent successfully on attempt {attempt + 1}")
                    break
                else:
                    raise Exception("Twilio returned False for send_sms")
                    
            except Exception as e:
                last_sms_error = str(e)
                logger.warning(f"CELERY: SMS send attempt {attempt + 1} failed: {e}")
                
                if attempt < max_sms_retries - 1:
                    import time
                    time.sleep(sms_retry_delay * (2 ** attempt))  # Exponential backoff
                else:
                    logger.error(f"CELERY: All SMS send attempts failed for message {message_id}")
        
        if not sms_sent:
            # Update message status to failed
            scheduled_message.status = MessageStatus.FAILED
            scheduled_message.error_message = f"SMS delivery failed after {max_sms_retries} attempts: {last_sms_error}"
            session.add(scheduled_message)
            session.commit()
            
            self.update_state(state='FAILURE', meta={'error': 'sms_delivery_failed'})
            return {"status": "error", "reason": "sms_delivery_failed", "error": last_sms_error}
        
        # 5. Create message record
        try:
            message_log = Message(
                user_id=scheduled_message.user_id,
                client_id=scheduled_message.client_id,
                content=personalized_content,
                direction=MessageDirection.OUTBOUND,
                status=MessageStatus.SENT,
                source=MessageSource.SCHEDULED,
                sender_type=MessageSenderType.USER,
                created_at=datetime.now(timezone.utc),
                originally_scheduled_at=scheduled_message.scheduled_at_utc
            )
            
            session.add(message_log)
            session.flush()  # Ensure ID is generated
            session.refresh(message_log)
            logger.info(f"CELERY: Message record created with ID {message_log.id}")
            
        except Exception as e:
            logger.error(f"CELERY: Failed to create message record: {e}")
            # Even if message record fails, we still sent the SMS
            # Mark scheduled message as sent but log the error
            scheduled_message.status = MessageStatus.SENT
            scheduled_message.error_message = f"SMS sent but message record failed: {str(e)}"
            session.add(scheduled_message)
            session.commit()
            
            self.update_state(state='FAILURE', meta={'error': 'message_record_failed'})
            return {"status": "partial_success", "reason": "message_record_failed", "error": str(e)}
        
        # 6. Update scheduled message status
        try:
            scheduled_message.status = MessageStatus.SENT
            scheduled_message.sent_at = datetime.now(timezone.utc)
            session.add(scheduled_message)
            
            # Update client interaction timestamp
            crm_service.update_last_interaction(scheduled_message.client_id, user_id=scheduled_message.user_id, session=session)
            
            session.commit()
            logger.info(f"CELERY: Scheduled message {message_id} marked as sent")
            
        except Exception as e:
            logger.error(f"CELERY: Failed to update scheduled message status: {e}")
            # Don't fail the entire operation for this
            try:
                session.rollback()
                session.commit()  # Try to commit just the message record
            except Exception as commit_error:
                logger.error(f"CELERY: Failed to commit after status update error: {commit_error}")
        
        logger.info(f"CELERY: Scheduled message delivery completed successfully for message {message_id}")
        return {"status": "success", "message_id": str(message_log.id)}
        
    except Exception as e:
        logger.error(f"CELERY: Critical error in scheduled message delivery: {e}", exc_info=True)
        
        # Try to update scheduled message status to failed
        if session and scheduled_message:
            try:
                scheduled_message.status = MessageStatus.FAILED
                scheduled_message.error_message = f"Critical error: {str(e)}"
                session.add(scheduled_message)
                session.commit()
            except Exception as update_error:
                logger.error(f"CELERY: Failed to update message status after critical error: {update_error}")
        
        # Retry the task if it's a transient error
        if self.request.retries < self.max_retries:
            logger.info(f"CELERY: Retrying task for message {message_id} (attempt {self.request.retries + 1})")
            raise self.retry(countdown=60 * (2 ** self.request.retries), exc=e)
        else:
            logger.error(f"CELERY: Max retries exceeded for message {message_id}")
            self.update_state(state='FAILURE', meta={'error': str(e)})
            return {"status": "error", "reason": "max_retries_exceeded", "error": str(e)}
    
    finally:
        if session:
            try:
                session.close()
            except Exception as e:
                logger.error(f"CELERY: Failed to close session: {e}")

@celery_app.task(bind=True)
def process_incoming_message_task(self, message_data: dict) -> dict:
    """
    Processes an incoming message asynchronously with error handling.
    """
    try:
        logger.info(f"CELERY: Processing incoming message for client {message_data.get('client_id')}")
        
        # This would be called when a webhook receives an incoming message
        # Implementation depends on your webhook structure
        
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"CELERY: Error processing incoming message: {e}", exc_info=True)
        return {"status": "error", "error": str(e)}

# Health check task
@celery_app.task
def health_check_task() -> dict:
    """
    Simple health check task for monitoring.
    """
    try:
        with Session(engine) as session:
            # Test database connection
            session.exec(select(User).limit(1)).first()
        
        return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}
        
    except Exception as e:
        logger.error(f"CELERY: Health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}

# Legacy tasks for compatibility
@celery_app.task
def main_opportunity_pipeline_task():
    """Legacy task - kept for compatibility"""
    logger.info("CELERY: Legacy pipeline task called - no action taken")
    return {"status": "legacy_task"}

@celery_app.task
def check_for_recency_nudges_task():
    """Legacy task - kept for compatibility"""
    logger.info("CELERY: Legacy recency task called - no action taken")
    return {"status": "legacy_task"}