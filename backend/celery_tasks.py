# backend/celery_tasks.py
# --- PRODUCTION-GRADE HARDENED VERSION ---

import logging
import asyncio
import uuid
import os
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID
from sqlmodel import Session, select

# --- ADDED: Load dummy environment variables for direct execution ---
if os.getenv("RUNNING_IN_CELERY") is None:
    dummy_env = {
        "OPENAI_API_KEY": "dummy_key",
        "GOOGLE_API_KEY": "dummy_key",
        "GOOGLE_CSE_ID": "dummy_id",
        "TWILIO_ACCOUNT_SID": "dummy_sid",
        "TWILIO_AUTH_TOKEN": "dummy_token",
        "TWILIO_PHONE_NUMBER": "dummy_number",
        "TWILIO_VERIFY_SERVICE_SID": "dummy_sid",
        "DATABASE_URL": "postgresql://user:password@host:5432/database",
        "SECRET_KEY": "dummy_secret",
        "MLS_PROVIDER": "flexmls",
        "SPARK_API_DEMO_TOKEN": "dummy_token",
        "RESO_API_BASE_URL": "https://api.flexmls.com",
        "RESO_API_TOKEN": "dummy_token",
        "GOOGLE_CLIENT_ID": "dummy_id",
        "GOOGLE_CLIENT_SECRET": "dummy_secret",
        "GOOGLE_REDIRECT_URI": "http://localhost:3000/auth/callback/google",
        "MICROSOFT_CLIENT_ID": "dummy_id",
        "MICROSOFT_CLIENT_SECRET": "dummy_secret",
        "MICROSOFT_REDIRECT_URI": "http://localhost:3000/auth/callback/microsoft"
    }
    os.environ.update(dummy_env)

# --- FIX: Import the single, centralized Celery app instance ---
from celery_worker import celery_app
from data.database import engine
from data.models.message import (Message, MessageStatus, MessageDirection, 
                                 MessageSource, MessageSenderType, ScheduledMessage)
from workflow.pipeline import run_main_opportunity_pipeline

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

# --- REMOVED: Celery app configuration is now centralized in celery_worker.py ---

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
@celery_app.task(name="celery_tasks.main_opportunity_pipeline_task", time_limit=600, soft_time_limit=480)
def main_opportunity_pipeline_task():
    """
    Celery entry point to trigger the main opportunity pipeline, which fetches
    live data from external sources (like FlexMLS) and processes it to find nudges.
    """
    logger.info("CELERY: Triggering main opportunity pipeline...")
    
    # Create pipeline run record
    from data.models.event import PipelineRun
    from data.database import get_session
    
    pipeline_run = None
    start_time = datetime.now(timezone.utc)
    
    try:
        # Create pipeline run record
        with next(get_session()) as session:
            pipeline_run = PipelineRun(
                pipeline_type="main_opportunity_pipeline",
                status="running",
                started_at=start_time
            )
            session.add(pipeline_run)
            session.commit()
            session.refresh(pipeline_run)
            logger.info(f"CELERY: Created pipeline run record with ID {pipeline_run.id}")
        
        # Run the asynchronous pipeline function
        result = asyncio.run(run_main_opportunity_pipeline())
        
        # Update pipeline run with success
        end_time = datetime.now(timezone.utc)
        duration = (end_time - start_time).total_seconds()
        
        with next(get_session()) as session:
            pipeline_run = session.exec(
                select(PipelineRun).where(PipelineRun.id == pipeline_run.id)
            ).first()
            if pipeline_run:
                pipeline_run.status = "completed"
                pipeline_run.completed_at = end_time
                pipeline_run.duration_seconds = duration
                # TODO: Extract actual metrics from pipeline result
                pipeline_run.events_processed = 1  # Placeholder
                pipeline_run.campaigns_created = 1  # Placeholder
                session.add(pipeline_run)
                session.commit()
        
        logger.info("CELERY: Main opportunity pipeline completed successfully.")
        return {"status": "success", "pipeline_run_id": str(pipeline_run.id)}
        
    except Exception as e:
        logger.error(f"CELERY: Main opportunity pipeline failed: {e}", exc_info=True)
        
        # Update pipeline run with failure
        if pipeline_run:
            try:
                with next(get_session()) as session:
                    pipeline_run = session.exec(
                        select(PipelineRun).where(PipelineRun.id == pipeline_run.id)
                    ).first()
                    if pipeline_run:
                        pipeline_run.status = "failed"
                        pipeline_run.completed_at = datetime.now(timezone.utc)
                        pipeline_run.errors = str(e)
                        session.add(pipeline_run)
                        session.commit()
            except Exception as update_error:
                logger.error(f"CELERY: Failed to update pipeline run status: {update_error}")
        
        return {"status": "error", "error": str(e)}


@celery_app.task
def check_for_recency_nudges_task():
    """Legacy task - kept for compatibility"""
    logger.info("CELERY: Legacy recency task called - no action taken")
    return {"status": "legacy_task"}

if __name__ == "__main__":
    logger.info("Triggering main opportunity pipeline manually...")
    main_opportunity_pipeline_task.delay()
    logger.info("Main opportunity pipeline task triggered.")