# FILE: backend/celery_worker.py
# PURPOSE: Creates and configures the Celery application and its scheduled tasks.

from celery import Celery
from celery.schedules import crontab
from common.config import get_settings

# Get Redis URL from configuration
settings = get_settings()
REDIS_URL = settings.REDIS_URL

# Create the Celery app instance with production-grade configuration
celery_app = Celery(
    "worker",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["celery_tasks"]
)

# Production-grade configuration (same as celery_tasks.py)
celery_app.conf.update(
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

# --- Celery Beat Schedules (The "Company Clock") ---
celery_app.conf.beat_schedule = {
    'health-check-every-hour': {
        'task': 'celery_tasks.health_check_task',
        'schedule': crontab(minute=0), # Run every hour
    },
    'main-opportunity-pipeline-every-2-hours': {
        'task': 'celery_tasks.main_opportunity_pipeline_task',
        'schedule': crontab(minute=0, hour='*/2'), # Run every 2 hours
    }
}
