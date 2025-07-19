# File: backend/tests/test_messaging.py

import pytest
import uuid
from fastapi.testclient import TestClient
from unittest.mock import patch
from sqlmodel import Session
from datetime import datetime, timezone, timedelta

from data.models.user import User
from data.models.client import Client
from data.models.message import ScheduledMessage, MessageStatus

@patch("api.rest.campaigns.orchestrator.orchestrate_send_message_now")
def test_send_message_now_succeeds(mock_orchestrator, authenticated_client: TestClient, test_user: User, session: Session):
    mock_orchestrator.return_value = True
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

def test_update_scheduled_message_succeeds(authenticated_client: TestClient, scheduled_message: ScheduledMessage, session: Session):
    update_payload = {"content": "This is the updated message content."}
    response = authenticated_client.put(
        f"/api/scheduled-messages/{scheduled_message.id}",
        json=update_payload
    )
    assert response.status_code == 200
    
    session.refresh(scheduled_message)
    assert scheduled_message.content == "This is the updated message content."

def test_delete_scheduled_message_succeeds(authenticated_client: TestClient, scheduled_message: ScheduledMessage, session: Session):
    response = authenticated_client.delete(f"/api/scheduled-messages/{scheduled_message.id}")
    assert response.status_code == 204
    
    # --- FIX: Expunge the object from the test session cache. ---
    # This detaches the instance from the session entirely. Now, session.get()
    # will query the database directly instead of trying to refresh a stale object.
    session.expunge(scheduled_message)
    
    db_msg = session.get(ScheduledMessage, scheduled_message.id)
    assert db_msg is None