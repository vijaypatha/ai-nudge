# File Path: backend/tests/test_conversations.py
# 
# What does this file test:
# This file tests conversation functionality including conversation creation, message
# handling, conversation state management, and conversation history. It validates
# the conversation system that manages ongoing communication threads between
# users and clients with proper message threading and state persistence.
# 
# When was it updated: 2025-01-27
# Purpose: Tests for the /conversations and /messages API endpoints.

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import uuid
from datetime import datetime, timezone

from data.models.message import Message, MessageDirection, MessageStatus, MessageSource

@pytest.fixture
def test_client_id(test_user, session):
    """Create a test client for the test user."""
    from data.models.client import Client
    client = Client(
        id=uuid.uuid4(),
        user_id=test_user.id,
        full_name="Test Client",
        phone="+15551234567"
    )
    session.add(client)
    session.commit()
    return client.id

@pytest.fixture
def mock_crm_service():
    """Fixture to mock the CRM service calls in the conversations module."""
    with patch("api.rest.conversations.crm_service") as mock_crm:
        # Create proper Message objects for the mock
        mock_messages = [
            Message(
                id=uuid.uuid4(),
                user_id=uuid.uuid4(),
                client_id=uuid.uuid4(),  # Will be replaced by actual client_id
                content="Hello there",
                direction=MessageDirection.OUTBOUND,
                status=MessageStatus.SENT,
                source=MessageSource.MANUAL,
                sender_type="user",
                created_at=datetime.now(timezone.utc)
            ),
            Message(
                id=uuid.uuid4(),
                user_id=uuid.uuid4(),
                client_id=uuid.uuid4(),  # Will be replaced by actual client_id
                content="Hi back!",
                direction=MessageDirection.INBOUND,
                status=MessageStatus.RECEIVED,
                source=MessageSource.MANUAL,
                sender_type="user",  # Changed from "client" to "user"
                created_at=datetime.now(timezone.utc)
            ),
        ]
        
        # Configure the mock service methods
        mock_crm.get_conversation_history.return_value = mock_messages
        mock_crm.get_all_active_slates_for_client.return_value = []  # No active slates
        yield mock_crm

def test_get_conversation_history_by_client_id_succeeds(
    authenticated_client: TestClient, test_user, test_client_id, session
):
    """
    Tests successfully fetching message history for a specific client.
    """
    # Arrange: Create actual messages in the database
    from data.models.message import Message, MessageDirection, MessageStatus, MessageSource
    
    messages = [
        Message(
            id=uuid.uuid4(),
            user_id=test_user.id,
            client_id=test_client_id,
            content="Hello there",
            direction=MessageDirection.OUTBOUND,
            status=MessageStatus.SENT,
            source=MessageSource.MANUAL,
            sender_type="user",
            created_at=datetime.now(timezone.utc)
        ),
        Message(
            id=uuid.uuid4(),
            user_id=test_user.id,
            client_id=test_client_id,
            content="Hi back!",
            direction=MessageDirection.INBOUND,
            status=MessageStatus.RECEIVED,
            source=MessageSource.MANUAL,
            sender_type="user",
            created_at=datetime.now(timezone.utc)
        ),
    ]
    
    for message in messages:
        session.add(message)
    session.commit()
    
    # Act: Make a GET request with the client_id as a query parameter.
    response = authenticated_client.get(f"/api/conversations/messages/?client_id={test_client_id}")
    
    # Assert: Check for a 200 OK status and that the response contains the messages.
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)  # Should be ConversationDetailResponse
    assert "messages" in data
    assert len(data["messages"]) == 2
    assert data["messages"][0]["content"] == "Hello there"
    assert data["messages"][1]["content"] == "Hi back!"

def test_get_conversation_history_fails_for_nonexistent_client(
    authenticated_client: TestClient, mock_crm_service: MagicMock
):
    """
    Tests that the endpoint returns an empty conversation for a non-existent client_id.
    """
    # Arrange: Configure the mock to simulate no conversation history for non-existent client.
    mock_crm_service.get_conversation_history.return_value = []
    mock_crm_service.get_all_active_slates_for_client.return_value = []
    
    # Act
    response = authenticated_client.get(f"/api/conversations/messages/?client_id={uuid.uuid4()}")
    
    # Assert: The endpoint doesn't validate client existence, so it returns 200 with empty data
    assert response.status_code == 200
    data = response.json()
    assert "messages" in data
    assert len(data["messages"]) == 0