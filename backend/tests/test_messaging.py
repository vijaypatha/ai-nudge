# File: backend/tests/test_messaging.py
# 
# What does this file test:
# This file tests messaging functionality including message creation, deletion,
# status updates, and scheduled message management. It validates the core
# messaging system that handles communication between users and clients,
# including message persistence and lifecycle management.
# 
# When was it updated: 2025-01-27

import pytest
import uuid
from fastapi.testclient import TestClient
from unittest.mock import patch
from sqlmodel import Session
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock

from data.models.user import User
from data.models.client import Client
from data.models.message import ScheduledMessage, MessageStatus, Message, MessageDirection, MessageSource

@patch("agent_core.orchestrator.orchestrate_send_message_now")
def test_send_message_now_succeeds(mock_orchestrator, authenticated_client: TestClient, test_user: User, session: Session):
    # Create a mock Message object
    mock_message = Message(
        id=uuid.uuid4(),
        user_id=test_user.id,
        client_id=uuid.uuid4(),
        content="Hello, this is a test message!",
        direction=MessageDirection.OUTBOUND,
        source=MessageSource.INSTANT_NUDGE,
        status=MessageStatus.SENT,
        created_at=datetime.now(timezone.utc)
    )
    mock_orchestrator.return_value = mock_message
    
    test_client = Client(id=uuid.uuid4(), user_id=test_user.id, full_name="Test Client", email="client@test.com", phone_number="+15558887777")
    session.add(test_client)
    session.commit()

    payload = {
        "client_id": str(test_client.id),
        "content": "Hello, this is a test message!"
    }
    response = authenticated_client.post("/api/campaigns/messages/send-now", json=payload)

    assert response.status_code == 200
    mock_orchestrator.assert_called_once()

@pytest.fixture
def scheduled_message(session: Session, test_user: User) -> ScheduledMessage:
    msg = ScheduledMessage(
        id=uuid.uuid4(),
        user_id=test_user.id,
        client_id=uuid.uuid4(),
        content="Original scheduled message.",
        scheduled_at_utc=datetime.now(timezone.utc) + timedelta(days=1),
        timezone="UTC",
        status=MessageStatus.PENDING
    )
    session.add(msg)
    session.commit()
    session.refresh(msg)
    return msg

from data.models.user import User
from data.models.client import Client
from data.models.message import ScheduledMessage
from datetime import datetime, timezone
import uuid

@patch("celery_tasks.send_scheduled_message_task.apply_async")
def test_update_scheduled_message_succeeds(mock_celery, authenticated_client: TestClient, session: Session, test_user: User):
    # --- Arrange ---
    # 1. Mock the Celery task
    mock_celery.return_value = MagicMock(id="mock-task-id")

    # 2. Create all necessary records from scratch in the test DB
    # Use the authenticated test_user instead of creating a new one
    test_client = Client(id=uuid.uuid4(), user_id=test_user.id, full_name="Test Client")
    test_message = ScheduledMessage(
        user_id=test_user.id,
        client_id=test_client.id,
        content="Original message.",
        scheduled_at_utc=datetime.now(timezone.utc),
        timezone="UTC"
    )
    session.add(test_client)
    session.add(test_message)
    session.commit()

    # --- Act ---
    update_payload = {"content": "This is the updated message content."}
    response = authenticated_client.put(
        f"/api/scheduled-messages/{test_message.id}",
        json=update_payload
    )

    # --- Assert ---
    assert response.status_code == 200, response.json()
    assert response.json()["content"] == "This is the updated message content."

def test_delete_scheduled_message_succeeds(authenticated_client: TestClient, scheduled_message: ScheduledMessage, session: Session):
    response = authenticated_client.delete(f"/api/scheduled-messages/{scheduled_message.id}")
    assert response.status_code == 204  # DELETE returns 204 No Content
    
    # --- FIX: Refresh the object in the session to avoid detachment issues. ---
    session.refresh(scheduled_message)
    
    db_msg = session.get(ScheduledMessage, scheduled_message.id)
    # The message should be cancelled, not deleted (for audit purposes)
    assert db_msg is not None
    assert db_msg.status == MessageStatus.CANCELLED