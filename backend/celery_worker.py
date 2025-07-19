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
# Note: These are placeholder tasks for future implementation
celery_app.conf.beat_schedule = {
    'health-check-every-hour': {
        'task': 'celery_tasks.health_check_task',
        'schedule': crontab(minute=0), # Run every hour
    }
}

celery_app.conf.timezone = 'UTC'
