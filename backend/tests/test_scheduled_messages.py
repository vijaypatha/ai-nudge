# File: backend/tests/test_scheduled_messages.py
# --- CORRECTED VERSION ---

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import uuid
from datetime import datetime, timedelta, timezone
import pytz
from sqlmodel import Session

from data.models.user import User
from data.models.client import Client

# Fixed IDs for predictability
USER_ID = uuid.uuid4()
CLIENT_A_ID = uuid.uuid4() # Lives in New York
CLIENT_B_ID = uuid.uuid4() # Lives in Los Angeles
CLIENT_C_ID = uuid.uuid4() # No timezone set


@patch('api.rest.scheduled_messages.celery_app')
def test_create_bulk_scheduled_messages_succeeds(
    mock_celery: MagicMock,
    authenticated_client: TestClient,
    session: Session, # Use the real test session
    test_user: User
):
    """
    Tests that the bulk endpoint correctly schedules messages for multiple clients,
    respecting each client's individual timezone.
    """
    # --- Arrange ---
    # 1. Create the necessary records in the test database
    # Use the authenticated test_user instead of mock_user_from_token_data
    clients = [
        Client(id=CLIENT_A_ID, user_id=test_user.id, full_name="Client A", timezone="America/New_York"),
        Client(id=CLIENT_B_ID, user_id=test_user.id, full_name="Client B", timezone="America/Los_Angeles"),
        Client(id=CLIENT_C_ID, user_id=test_user.id, full_name="Client C", timezone=None),
    ]
    for client in clients:
        session.add(client)
    session.commit()

    # 2. Mock the Celery task to avoid real Celery calls
    mock_task = MagicMock()
    mock_task.id = "mock-task-id-123"
    with patch('celery_tasks.send_scheduled_message_task.apply_async', return_value=mock_task) as mock_apply_async:
        local_schedule_time_str = (datetime.now() + timedelta(days=5)).strftime('%Y-%m-%dT10:00:00')
        local_schedule_time = datetime.fromisoformat(local_schedule_time_str)

        payload = {
            "client_ids": [str(CLIENT_A_ID), str(CLIENT_B_ID), str(CLIENT_C_ID)],
            "content": "Bulk message test",
            "scheduled_at_local": local_schedule_time_str
        }

        # --- Act ---
        response = authenticated_client.post("/api/scheduled-messages/bulk", json=payload)

        # --- Assert ---
        assert response.status_code == 202, response.json()
        assert response.json() == {"detail": "Successfully scheduled 3 out of 3 messages."}
        assert mock_apply_async.call_count == 3

@patch('api.rest.scheduled_messages.celery_app')
def test_create_single_scheduled_message_uses_client_timezone(
    mock_celery: MagicMock,
    authenticated_client: TestClient,
    session: Session, # Use the real test session
    test_user: User
):
    """
    Tests that the single schedule endpoint correctly uses the client's timezone.
    """
    # --- Arrange ---
    # 1. Create records in the test DB
    # Use the authenticated test_user instead of mock_user_from_token_data
    client_a = Client(id=CLIENT_A_ID, user_id=test_user.id, full_name="Client A", timezone="America/New_York")
    session.add(client_a)
    session.commit()

    # 2. Mock celery
    mock_task = MagicMock()
    mock_task.id = "mock-task-id-456"
    with patch('celery_tasks.send_scheduled_message_task.apply_async', return_value=mock_task) as mock_apply_async:
        local_schedule_time_str = (datetime.now() + timedelta(days=5)).strftime('%Y-%m-%dT14:00:00')

        payload = {
            "client_id": str(CLIENT_A_ID),
            "content": "Single message test for NY client",
            "scheduled_at_local": local_schedule_time_str,
            "timezone": "America/Chicago" # User's timezone is sent, but should be ignored
        }

        # --- Act ---
        response = authenticated_client.post("/api/scheduled-messages", json=payload)

        # --- Assert ---
        assert response.status_code == 201, response.json()
        mock_apply_async.assert_called_once()

        expected_eta = pytz.timezone("America/New_York").localize(datetime.fromisoformat(local_schedule_time_str)).astimezone(pytz.utc)
        actual_eta = mock_apply_async.call_args.kwargs['eta']
        assert actual_eta == expected_eta