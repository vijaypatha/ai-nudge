# File Path: backend/tests/test_conversations.py
# Purpose: Tests for the /conversations and /messages API endpoints.

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import uuid

# A fixed UUID for our test client for predictability
TEST_CLIENT_ID = uuid.uuid4()

@pytest.fixture
def mock_crm_service():
    """Fixture to mock the entire crm_service module."""
    with patch("api.rest.conversations.crm_service") as mock_crm:
        # Mock the client object that get_client_by_id returns
        mock_client = MagicMock()
        mock_client.id = TEST_CLIENT_ID
        
        # Configure the mock service methods
        mock_crm.get_client_by_id.return_value = mock_client
        mock_crm.get_conversation_history.return_value = [
            {"id": str(uuid.uuid4()), "content": "Hello there", "sender": "user"},
            {"id": str(uuid.uuid4()), "content": "Hi back!", "sender": "client"},
        ]
        yield mock_crm

def test_get_conversation_history_by_client_id_succeeds(
    authenticated_client: TestClient, mock_crm_service: MagicMock
):
    """
    Tests successfully fetching message history for a specific client.
    """
    # Arrange: Fixtures provide the authenticated client and mocked CRM service.
    
    # Act: Make a GET request with the client_id as a query parameter.
    response = authenticated_client.get(f"/api/messages/?client_id={TEST_CLIENT_ID}")
    
    # Assert: Check for a 200 OK status and that the response is a list.
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]["content"] == "Hello there"
    
    # Assert that our mocks were called correctly
    mock_crm_service.get_client_by_id.assert_called_with(client_id=TEST_CLIENT_ID, user_id=mock_crm_service.get_client_by_id.call_args[1]['user_id'])
    mock_crm_service.get_conversation_history.assert_called_with(client_id=TEST_CLIENT_ID, user_id=mock_crm_service.get_conversation_history.call_args[1]['user_id'])

def test_get_conversation_history_fails_for_nonexistent_client(
    authenticated_client: TestClient, mock_crm_service: MagicMock
):
    """
    Tests that a 404 is returned for a non-existent client_id.
    """
    # Arrange: Configure the mock to simulate a client not being found.
    mock_crm_service.get_client_by_id.return_value = None
    
    # Act
    response = authenticated_client.get(f"/api/messages/?client_id={uuid.uuid4()}")
    
    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Client not found."