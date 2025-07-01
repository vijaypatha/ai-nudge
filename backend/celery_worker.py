# FILE: backend/celery_worker.py
# PURPOSE: Creates and configures the Celery application and its scheduled tasks.

from celery import Celery
from celery.schedules import crontab

# Define the Redis URL for our message broker.
REDIS_URL = "redis://redis:6379/0" # Use the service name 'redis' from docker-compose

# Create the Celery app instance.
celery_app = Celery(
    "worker",
    broker=REDIS_URL,
    backend=REDIS_URL,
    # --- FIX: Corrected the include path ---
    # From within the /app directory, the path is just 'celery_tasks'.
    include=["celery_tasks"] 
)

# --- Celery Beat Schedules (The "Company Clock") ---
celery_app.conf.beat_schedule = {
    'check-mls-every-15-minutes': {
        # --- FIX: Corrected the task path ---
        'task': 'celery_tasks.check_mls_for_events_task',
        'schedule': crontab(minute='*/15'),
    },
    'check-for-recency-nudges-daily': {
        'task': 'celery_tasks.check_for_recency_nudges_task',
        'schedule': crontab(hour=9, minute=0), # Run once a day at 9 AM
    }
}

celery_app.conf.timezone = 'UTC'
