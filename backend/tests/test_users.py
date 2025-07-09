# File: backend/tests/test_users.py

from fastapi.testclient import TestClient
from data.models.user import User

def test_get_current_user_profile_succeeds(authenticated_client: TestClient, test_user: User):
    """Tests successful retrieval of the current user's profile."""
    response = authenticated_client.get("/api/users/me")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(test_user.id)

def test_update_user_profile_succeeds(authenticated_client: TestClient, test_user: User):
    """Tests that a valid user profile update succeeds."""
    # Arrange
    payload = {"full_name": "Updated Test User"}

    # Act
    response = authenticated_client.put("/api/users/me", json=payload)

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Updated Test User"
    assert data["id"] == str(test_user.id)

def test_update_user_profile_fails_invalid_data_type(authenticated_client: TestClient):
    """
    Tests that sending an invalid data type for a field fails validation.
    """
    # Arrange: 'onboarding_complete' should be a boolean, not a string
    payload = {"onboarding_complete": "not-a-boolean"}

    # Act
    response = authenticated_client.put("/api/users/me", json=payload)

    # Assert
    assert response.status_code == 422
    data = response.json()
    assert data["detail"][0]["type"] == "bool_parsing"
    assert data["detail"][0]["loc"] == ["body", "onboarding_complete"]

def test_get_current_user_profile_fails_unauthenticated(client: TestClient):
    """Tests that unauthenticated access is rejected."""
    response = client.get("/api/users/me")
    assert response.status_code == 401
