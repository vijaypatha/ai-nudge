# File: trigger_mls_sync.py
# --- FINAL, DEFINITIVE VERSION ---
# Correctly loads all .env variables, then overrides Celery-specific ones.

import os
import sys
from dotenv import load_dotenv

print("--- Loading environment variables and overriding Celery config... ---")

# --- STEP 1: Load all variables from the .env file first ---
dotenv_path = os.path.join(os.path.dirname(__file__), 'backend', '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path=dotenv_path)

# --- STEP 2: Now, OVERRIDE the Celery-specific variables ---
# This forces the Celery app to use localhost for its broker and backend,
# while keeping all other settings (DB, API keys) from the .env file.
os.environ['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
os.environ['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'


# --- STEP 3: Add the 'backend' directory to the Python path ---
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# --- STEP 4: Now, safely import and run the task ---
from backend.celery_tasks import check_mls_for_events_task

print("--- Triggering the MLS event scan task now... ---")
check_mls_for_events_task.delay()
print("--- Task has been sent to the Celery worker. ---")
print("To see its progress, you can run: docker-compose logs -f celery-worker")