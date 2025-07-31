# File: backend/tests/test_clients.py
# 
# What does this file test:
# This file tests client management functionality including client creation, updates,
# client intelligence, tagging, and client-related API endpoints. It validates
# the client system that handles client profiles, preferences, and relationship
# management for different verticals.
# 
# When was it updated: 2025-01-27

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import uuid

from data.models.client import Client, ClientCreate
from data.models.user import User

def test_search_clients_succeeds(authenticated_client: TestClient, test_user: User):
    """
    Tests that the client search endpoint correctly filters based on a mocked
    semantic search result.
    """
    # Arrange
    matched_client_id = uuid.uuid4()
    mock_all_clients = [
        Client(id=matched_client_id, user_id=test_user.id, full_name="Matched Client", email="match@test.com", phone_number="+15551111111"),
        Client(id=uuid.uuid4(), user_id=test_user.id, full_name="Unmatched Client", email="unmatch@test.com", phone_number="+15552222222"),
    ]
    mock_matched_ids = {matched_client_id}
    payload = {"natural_language_query": "clients who want to buy soon"}

    # Mock the two functions called by the endpoint
    with patch("api.rest.clients.audience_builder.find_clients_by_semantic_query", return_value=mock_matched_ids), \
         patch("api.rest.clients.crm_service.get_all_clients", return_value=mock_all_clients):
        
        # Act
        response = authenticated_client.post("/api/clients/search", json=payload)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == str(matched_client_id)

@patch("api.rest.clients.crm_service.create_or_update_client")
def test_add_manual_client_succeeds(mock_create_or_update, authenticated_client: TestClient, test_user: User):
    """Tests that a valid client can be added manually."""
    # Arrange
    client_id = uuid.uuid4()
    payload = {"full_name": "Manual Client", "email": "manual@test.com"}
    
    # Mock the return value from the CRM service
    mock_create_or_update.return_value = (
        Client(id=client_id, user_id=test_user.id, **payload, phone_number="+15553334444"), 
        True
    )

    # Act
    response = authenticated_client.post("/api/clients/manual", json=payload)

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Manual Client"
    assert data["id"] == str(client_id)
    mock_create_or_update.assert_called_once()


def test_add_manual_client_fails_missing_data(authenticated_client: TestClient):
    """
    Tests that creating a client with missing required data fails validation.
    """
    # Arrange: Send an empty payload
    payload = {"email": "missing_name@test.com"}

    # Act
    response = authenticated_client.post("/api/clients/manual", json=payload)

    # Assert
    assert response.status_code == 422
    data = response.json()
    assert data["detail"][0]["type"] == "missing"
    assert data["detail"][0]["loc"] == ["body", "full_name"]
