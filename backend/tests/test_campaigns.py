# File: backend/tests/test_campaigns.py
# 
# What does this file test:
# This file tests campaign functionality including campaign creation, management,
# campaign briefings, and campaign-related API endpoints. It validates the
# campaign system that handles marketing campaigns, content creation, and
# campaign lifecycle management for different verticals.
# 
# When was it updated: 2025-01-27

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

def test_draft_instant_nudge_succeeds(authenticated_client: TestClient):
    """
    Tests successful generation of an instant nudge draft.
    """
    # Arrange
    mock_draft_content = "This is a mocked AI draft about market trends."
    payload = {"topic": "Latest market trends"}
    
    # Mock the agent call to prevent real network requests
    with patch(
        "api.rest.campaigns.conversation_agent.draft_instant_nudge_message", 
        return_value=mock_draft_content
    ) as mock_draft:
        # Act
        response = authenticated_client.post("/api/campaigns/draft-instant-nudge", json=payload)
        
        # Assert
        assert response.status_code == 200
        assert response.json() == {"draft": mock_draft_content}
        mock_draft.assert_awaited_once()

def test_draft_instant_nudge_fails_with_empty_topic(authenticated_client: TestClient):
    """
    Tests that the endpoint returns a 400 Bad Request for a topic with only whitespace.
    This tests our custom validation logic inside the endpoint.
    """
    # Arrange
    payload = {"topic": " "}
    
    # Act
    response = authenticated_client.post("/api/campaigns/draft-instant-nudge", json=payload)
    
    # Assert
    assert response.status_code == 400
    assert "Topic cannot be empty" in response.json()["detail"]

def test_draft_instant_nudge_fails_with_missing_topic(authenticated_client: TestClient):
    """
    Tests that a request with a missing 'topic' field fails validation.
    This tests FastAPI's automatic request validation.
    """
    # Arrange: Send an empty JSON object
    payload = {}

    # Act
    response = authenticated_client.post("/api/campaigns/draft-instant-nudge", json=payload)

    # Assert: FastAPI should return a 422 Unprocessable Entity
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    assert data["detail"][0]["type"] == "missing"
    assert data["detail"][0]["loc"] == ["body", "topic"]

def test_draft_instant_nudge_fails_unauthenticated(client: TestClient):
    """Tests that unauthenticated access is rejected."""
    # Arrange
    payload = {"topic": "A valid topic"}
    
    # Act
    response = client.post("/api/campaigns/draft-instant-nudge", json=payload)
    
    # Assert
    assert response.status_code == 401
