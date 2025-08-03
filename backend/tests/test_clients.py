# File: backend/tests/test_clients.py
# 
# What does this file test:
# This file tests client management functionality including client creation, updates,
# deletion, and client-related API endpoints. It validates the client system
# that handles contact management and client relationships across different verticals.
# 
# When was it updated: 2025-01-27

import pytest
import uuid
from fastapi.testclient import TestClient
from sqlmodel import Session, select

# --- FIXED: Remove direct model imports to prevent table redefinition ---
# Models are now imported centrally in conftest.py

def test_create_client_succeeds(authenticated_client: TestClient, test_user, session: Session):
    """Tests successful client creation."""
    # Arrange
    payload = {
        "full_name": "Test Client",
        "phone_number": "+15551234567",
        "email": "client@example.com"
    }

    # Act
    response = authenticated_client.post("/api/clients", json=payload)

    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["full_name"] == "Test Client"
    assert data["phone_number"] == "+15551234567"
    assert data["email"] == "client@example.com"
    assert data["user_id"] == str(test_user.id)

def test_get_clients_succeeds(authenticated_client: TestClient, test_user, session: Session):
    """Tests successful retrieval of user's clients."""
    # Arrange - create a test client
    from data.models.client import Client
    client = Client(
        id=uuid.uuid4(),
        user_id=test_user.id,
        full_name="Test Client",
        phone_number="+15551234567"
    )
    session.add(client)
    session.commit()

    # Act
    response = authenticated_client.get("/api/clients")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any(client["full_name"] == "Test Client" for client in data)

def test_get_client_by_id_succeeds(authenticated_client: TestClient, test_user, session: Session):
    """Tests successful retrieval of a specific client."""
    # Arrange - create a test client
    from data.models.client import Client
    client = Client(
        id=uuid.uuid4(),
        user_id=test_user.id,
        full_name="Test Client",
        phone_number="+15551234567"
    )
    session.add(client)
    session.commit()

    # Act
    response = authenticated_client.get(f"/api/clients/{client.id}")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(client.id)
    assert data["full_name"] == "Test Client"

def test_update_client_succeeds(authenticated_client: TestClient, test_user, session: Session):
    """Tests successful client update."""
    # Arrange - create a test client
    from data.models.client import Client
    client = Client(
        id=uuid.uuid4(),
        user_id=test_user.id,
        full_name="Original Name",
        phone_number="+15551234567"
    )
    session.add(client)
    session.commit()

    # Act
    payload = {"full_name": "Updated Name"}
    response = authenticated_client.put(f"/api/clients/{client.id}", json=payload)

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Updated Name"

def test_delete_client_succeeds(authenticated_client: TestClient, test_user, session: Session):
    """Tests successful client deletion."""
    # Arrange - create a test client
    from data.models.client import Client
    client = Client(
        id=uuid.uuid4(),
        user_id=test_user.id,
        full_name="Test Client",
        phone_number="+15551234567"
    )
    session.add(client)
    session.commit()

    # Act
    response = authenticated_client.delete(f"/api/clients/{client.id}")

    # Assert
    assert response.status_code == 204

    # Verify client was actually deleted
    response = authenticated_client.get(f"/api/clients/{client.id}")
    assert response.status_code == 404

def test_create_client_fails_invalid_data(authenticated_client: TestClient):
    """Tests that client creation fails with invalid data."""
    # Arrange
    payload = {
        "full_name": "",  # Invalid: empty name
        "phone_number": "invalid-phone"  # Invalid: not a valid phone number
    }

    # Act
    response = authenticated_client.post("/api/clients", json=payload)

    # Assert
    assert response.status_code == 422

def test_get_clients_fails_unauthenticated(client: TestClient):
    """Tests that unauthenticated access to clients is rejected."""
    response = client.get("/api/clients")
    assert response.status_code == 401

def test_client_ownership_isolation(authenticated_client: TestClient, session: Session):
    """Tests that users can only access their own clients."""
    # Arrange - create another user and client
    from data.models.user import User
    other_user = User(
        id=uuid.uuid4(),
        full_name="Other User",
        phone_number="+15551234568"
    )
    session.add(other_user)
    session.commit()

    from data.models.client import Client
    other_client = Client(
        id=uuid.uuid4(),
        user_id=other_user.id,
        full_name="Other Client",
        phone_number="+15551234569"
    )
    session.add(other_client)
    session.commit()

    # Act - try to access other user's client
    response = authenticated_client.get(f"/api/clients/{other_client.id}")

    # Assert - should be forbidden
    assert response.status_code == 404  # or 403, depending on implementation
