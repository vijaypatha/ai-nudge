# FILE: backend/celery_worker.py
# PURPOSE: Creates and configures the Celery application and its scheduled tasks.

from celery import Celery
from celery.schedules import crontab

# Define the Redis URL for our message broker.
# For production, this should come from an environment variable.
REDIS_URL = "redis://localhost:6379/0"

# Create the Celery app instance.
# The first argument is the name of the current module.
# The 'backend' argument specifies where Celery should look for task modules.
celery_app = Celery(
    "worker",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["backend.celery_tasks"] # Point Celery to our tasks file
)

# --- Celery Beat Schedules (The "Company Clock") ---
# This is where we define all our recurring tasks.
celery_app.conf.beat_schedule = {
    # The name of the schedule entry
    'check-mls-every-15-minutes': {
        # The path to the task function to run
        'task': 'backend.celery_tasks.check_mls_for_events_task',
        # The schedule: run every 15 minutes
        'schedule': crontab(minute='*/15'),
    },
    # We can add more scheduled tasks here in the future.
}

celery_app.conf.timezone = 'UTC'