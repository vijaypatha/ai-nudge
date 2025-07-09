# File: backend/tests/test_community.py
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
import uuid

@patch("api.rest.community.crm_service.get_community_overview")
def test_get_community_overview_succeeds(mock_get_overview, authenticated_client: TestClient):
    """Tests successful retrieval of the community overview."""
    mock_get_overview.return_value = [] # Return an empty list for simplicity
    response = authenticated_client.get("/api/community")
    assert response.status_code == 200
    mock_get_overview.assert_called_once()

def test_get_community_overview_fails_unauthenticated(client: TestClient):
    """Tests that unauthenticated access is rejected."""
    response = client.get("/api/community")
    # --- FIX: Assert for 401 instead of 403 ---
    assert response.status_code == 401