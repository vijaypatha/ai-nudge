# FILE: rescore_all.py
import asyncio
import os
import uuid
import logging

from sqlmodel import Session, select
from data.database import engine
from data.models.user import User
from data.models.client import Client

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def main():
    """
    Finds a specific user and triggers the re-scoring Celery task
    for every one of their clients.
    """
    # --- IMPORTANT ---
    # Replace this with the actual UUID of the user whose clients you want to rescore.
    # You can find your user_id in the 'user' table of your database.
    USER_ID_TO_RESCORE = '01bbcb67-8536-4085-b3a4-65051965e2b2'
    # -----------------

    try:
        user_id_uuid = uuid.UUID(USER_ID_TO_RESCORE)
    except ValueError:
        logging.error(f"Invalid UUID format for USER_ID_TO_RESCORE. Please provide a valid UUID.")
        return

    # This import must be here, after the environment is potentially set up
    try:
        from celery_tasks import rescore_client_against_recent_events_task
    except ImportError:
        logging.error("Could not import Celery task. Make sure you are running this script from" \
                      " within your project's environment where 'celery_tasks' is accessible.")
        return

    with Session(engine) as session:
        user = session.get(User, user_id_uuid)
        if not user:
            logging.error(f"User with ID {USER_ID_TO_RESCORE} not found.")
            return

        clients_to_rescore = session.exec(select(Client).where(Client.user_id == user.id)).all()
        
        if not clients_to_rescore:
            logging.warning(f"User {user.id} has no clients to rescore.")
            return

        logging.info(f"Found {len(clients_to_rescore)} clients for user {user.id}. Queuing re-score tasks...")

        for client in clients_to_rescore:
            # This is the same task triggered when a client's profile is updated
            rescore_client_against_recent_events_task.delay(
                client_id=str(client.id), 
                user_id=str(user.id)
            )
            logging.info(f"  -> Queued re-score task for client: {client.full_name} ({client.id})")

    logging.info("\n--- All re-scoring tasks have been queued! ---")
    logging.info("Your Celery workers will now process these tasks.")
    logging.info("Nudges will begin to appear in the UI as the processing completes.")


if __name__ == "__main__":
    asyncio.run(main())