# File: backend/tests/test_scheduled_messages.py
# Purpose: Tests for the /scheduled-messages API endpoints, including new bulk functionality.

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, ANY
import uuid
from datetime import datetime, timedelta, timezone
import pytz
from typing import List

from data.models.user import User
from data.models.client import Client
from data.models.message import ScheduledMessage, MessageStatus

# Fixed IDs for predictability
USER_ID = uuid.uuid4()
CLIENT_A_ID = uuid.uuid4() # Lives in New York
CLIENT_B_ID = uuid.uuid4() # Lives in Los Angeles
CLIENT_C_ID = uuid.uuid4() # No timezone set

@pytest.fixture
def mock_clients():
    """Provides a list of mock clients with different timezones."""
    return [
        Client(id=CLIENT_A_ID, user_id=USER_ID, full_name="Client A", timezone="America/New_York"),
        Client(id=CLIENT_B_ID, user_id=USER_ID, full_name="Client B", timezone="America/Los_Angeles"),
        Client(id=CLIENT_C_ID, user_id=USER_ID, full_name="Client C", timezone=None), # Will use user's default
    ]

# This fixture is implicitly used by authenticated_client
@pytest.fixture
def mock_user_from_token_data():
    """Provides a mock User object for dependency injection."""
    return User(id=USER_ID, email="test@example.com", timezone="America/Chicago") # User is in Central Time

@patch('api.rest.scheduled_messages.celery_app')
@patch('api.rest.scheduled_messages.crm_service')
def test_create_bulk_scheduled_messages_succeeds(
    mock_crm: MagicMock,
    mock_celery: MagicMock,
    authenticated_client: TestClient,
    mock_clients: List[Client]
):
    """
    Tests that the bulk endpoint correctly schedules messages for multiple clients,
    respecting each client's individual timezone.
    """
    # --- Arrange ---
    # The CRM service will return our list of mock clients when asked for them
    mock_crm.get_clients_by_ids.return_value = mock_clients
    # Mock the apply_async method to avoid real Celery calls
    mock_task = MagicMock()
    mock_celery.control.revoke.return_value = None
    with patch('celery_tasks.send_scheduled_message_task.apply_async', return_value=mock_task) as mock_apply_async:
        # Define the local time the user picked in the UI
        # User (in Chicago) picks 10:00 AM on a future date
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
        assert response.status_code == 202
        assert response.json() == {"detail": "Successfully scheduled 3 out of 3 messages."}
        
        # Verify it was called 3 times, once for each client
        assert mock_apply_async.call_count == 3
        
        # Check the ETA for each call to ensure timezones were handled correctly
        calls = mock_apply_async.call_args_list
        
        # Expected UTC times
        # Client A (New York, EDT is UTC-4): 10:00 AM -> 14:00 UTC
        expected_eta_a = pytz.timezone("America/New_York").localize(local_schedule_time).astimezone(pytz.utc)
        # Client B (Los Angeles, PDT is UTC-7): 10:00 AM -> 17:00 UTC
        expected_eta_b = pytz.timezone("America/Los_Angeles").localize(local_schedule_time).astimezone(pytz.utc)
        # Client C (No TZ, uses user's Chicago, CDT is UTC-5): 10:00 AM -> 15:00 UTC
        expected_eta_c = pytz.timezone("America/Chicago").localize(local_schedule_time).astimezone(pytz.utc)

        # Extract the actual ETAs from the mock calls
        actual_etas = sorted([call.kwargs['eta'] for call in calls], key=lambda dt: dt.hour)
        expected_etas = sorted([expected_eta_a, expected_eta_c, expected_eta_b], key=lambda dt: dt.hour)

        assert actual_etas == expected_etas

@patch('api.rest.scheduled_messages.celery_app')
@patch('api.rest.scheduled_messages.crm_service')
def test_create_single_scheduled_message_uses_client_timezone(
    mock_crm: MagicMock,
    mock_celery: MagicMock,
    authenticated_client: TestClient,
    mock_clients: List[Client]
):
    """
    Tests that the single schedule endpoint correctly uses the client's timezone
    over the user's timezone.
    """
    # --- Arrange ---
    client_a = mock_clients[0] # New York timezone
    mock_crm.get_client_by_id.return_value = client_a
    mock_task = MagicMock()
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
        assert response.status_code == 201
        mock_apply_async.assert_called_once()
        
        # Expected ETA should be based on New York time, not Chicago time
        expected_eta = pytz.timezone("America/New_York").localize(datetime.fromisoformat(local_schedule_time_str)).astimezone(pytz.utc)
        actual_eta = mock_apply_async.call_args.kwargs['eta']
        
        assert actual_eta == expected_eta