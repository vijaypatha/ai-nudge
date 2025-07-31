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
from unittest.mock import patch, MagicMock, AsyncMock
import uuid
from uuid import UUID

from data.models.client import Client, ClientCreate, ClientUpdate
from data.models.user import User, UserUpdate
from data.models.message import ScheduledMessage

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
@patch("api.rest.clients.crm_service.update_user")
@patch("api.rest.clients.initial_data_fetch_for_user_task")
def test_add_manual_client_succeeds_with_onboarding_update(
    mock_initial_data_fetch, 
    mock_update_user, 
    mock_create_or_update, 
    authenticated_client: TestClient, 
    test_user: User
):
    """Tests that a valid client can be added manually and onboarding state is updated."""
    # Arrange
    client_id = uuid.uuid4()
    payload = {"full_name": "Manual Client", "email": "manual@test.com"}
    
    # Mock the return value from the CRM service
    mock_create_or_update.return_value = (
        Client(id=client_id, user_id=test_user.id, **payload, phone_number="+15553334444"), 
        True
    )
    
    # Mock the user update
    mock_update_user.return_value = test_user
    mock_initial_data_fetch.delay.return_value = None

    # Act
    response = authenticated_client.post("/api/clients/manual", json=payload)

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Manual Client"
    assert data["id"] == str(client_id)
    mock_create_or_update.assert_called_once()
    mock_update_user.assert_called_once()
    mock_initial_data_fetch.delay.assert_called_once_with(user_id=str(test_user.id))

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

@patch("api.rest.clients.crm_service.update_client_intel")
@patch("agent_core.brain.relationship_planner.plan_relationship_campaign")
def test_update_client_intel_succeeds(mock_relationship_planner, mock_update_intel, authenticated_client: TestClient, test_user: User):
    """Tests that client intel can be updated successfully."""
    # Arrange
    client_id = uuid.uuid4()
    payload = {
        "tags_to_add": ["hot-lead", "buyer"],
        "notes_to_add": "Client is very interested in buying soon",
        "active_recommendation_id": str(uuid.uuid4())
    }
    
    mock_client = Client(id=client_id, user_id=test_user.id, full_name="Test Client")
    mock_update_intel.return_value = mock_client
    mock_relationship_planner.return_value = None

    # Act
    response = authenticated_client.post(f"/api/clients/{client_id}/intel", json=payload)

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(client_id)
    mock_update_intel.assert_called_once_with(
        client_id=client_id,
        user_id=test_user.id,
        tags_to_add=payload["tags_to_add"],
        notes_to_add=payload["notes_to_add"]
    )
    mock_relationship_planner.assert_called_once_with(client=mock_client, user=test_user)

@patch("api.rest.clients.crm_service.update_client_intel")
def test_update_client_intel_client_not_found(mock_update_intel, authenticated_client: TestClient, test_user: User):
    """Tests that updating intel for non-existent client returns 404."""
    # Arrange
    client_id = uuid.uuid4()
    payload = {"tags_to_add": ["hot-lead"]}
    
    mock_update_intel.return_value = None

    # Act
    response = authenticated_client.post(f"/api/clients/{client_id}/intel", json=payload)

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Client not found or failed to update."

@patch("api.rest.clients.crm_service.update_client_notes")
def test_update_client_notes_succeeds(mock_update_notes, authenticated_client: TestClient, test_user: User):
    """Tests that client notes can be updated successfully."""
    # Arrange
    client_id = uuid.uuid4()
    payload = {"notes": "Updated client notes"}
    
    mock_client = Client(id=client_id, user_id=test_user.id, full_name="Test Client")
    mock_update_notes.return_value = mock_client

    # Act
    response = authenticated_client.put(f"/api/clients/{client_id}/notes", json=payload)

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(client_id)
    mock_update_notes.assert_called_once_with(
        client_id=client_id,
        notes=payload["notes"],
        user_id=test_user.id
    )

@patch("api.rest.clients.crm_service.update_client_notes")
def test_update_client_notes_client_not_found(mock_update_notes, authenticated_client: TestClient, test_user: User):
    """Tests that updating notes for non-existent client returns 404."""
    # Arrange
    client_id = uuid.uuid4()
    payload = {"notes": "Updated client notes"}
    
    mock_update_notes.return_value = None

    # Act
    response = authenticated_client.put(f"/api/clients/{client_id}/notes", json=payload)

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Client not found."

@patch("api.rest.clients.crm_service.clear_active_recommendations")
def test_clear_client_recommendations_succeeds(mock_clear_recommendations, authenticated_client: TestClient, test_user: User):
    """Tests that client recommendations can be cleared successfully."""
    # Arrange
    client_id = uuid.uuid4()
    mock_clear_recommendations.return_value = True

    # Act
    response = authenticated_client.post(f"/api/clients/{client_id}/recommendations/clear")

    # Assert
    assert response.status_code == 204
    mock_clear_recommendations.assert_called_once_with(
        client_id=client_id,
        user_id=test_user.id
    )

@patch("api.rest.clients.crm_service.clear_active_recommendations")
def test_clear_client_recommendations_handles_failure(mock_clear_recommendations, authenticated_client: TestClient, test_user: User):
    """Tests that clearing recommendations handles failure gracefully."""
    # Arrange
    client_id = uuid.uuid4()
    mock_clear_recommendations.return_value = False

    # Act
    response = authenticated_client.post(f"/api/clients/{client_id}/recommendations/clear")

    # Assert
    assert response.status_code == 204  # Should still return 204 even on failure
    mock_clear_recommendations.assert_called_once_with(
        client_id=client_id,
        user_id=test_user.id
    )

@patch("api.rest.clients.crm_service.get_client_by_id")
@patch("api.rest.clients.crm_service.add_client_tags")
def test_add_tags_to_client_succeeds(mock_add_tags, mock_get_client, authenticated_client: TestClient, test_user: User):
    """Tests that tags can be added to a client successfully."""
    # Arrange
    client_id = uuid.uuid4()
    payload = {"tags": ["hot-lead", "buyer"]}
    
    mock_client = Client(id=client_id, user_id=test_user.id, full_name="Test Client")
    mock_get_client.return_value = mock_client
    mock_add_tags.return_value = mock_client

    # Act
    response = authenticated_client.post(f"/api/clients/{client_id}/tags", json=payload)

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(client_id)
    mock_add_tags.assert_called_once_with(
        client_id=client_id,
        tags_to_add=payload["tags"],
        user_id=test_user.id
    )

@patch("api.rest.clients.crm_service.get_client_by_id")
def test_add_tags_to_client_not_found(mock_get_client, authenticated_client: TestClient, test_user: User):
    """Tests that adding tags to non-existent client returns 404."""
    # Arrange
    client_id = uuid.uuid4()
    payload = {"tags": ["hot-lead"]}
    
    mock_get_client.return_value = None

    # Act
    response = authenticated_client.post(f"/api/clients/{client_id}/tags", json=payload)

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Client not found."

@patch("api.rest.clients.crm_service.update_client_tags")
def test_update_client_tags_succeeds(mock_update_tags, authenticated_client: TestClient, test_user: User):
    """Tests that client tags can be updated successfully."""
    # Arrange
    client_id = uuid.uuid4()
    payload = {"user_tags": ["hot-lead", "buyer"]}
    
    mock_client = Client(id=client_id, user_id=test_user.id, full_name="Test Client")
    mock_update_tags.return_value = mock_client

    # Act
    response = authenticated_client.put(f"/api/clients/{client_id}/tags", json=payload)

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(client_id)
    mock_update_tags.assert_called_once_with(
        client_id,
        payload["user_tags"],
        user_id=test_user.id
    )

@patch("api.rest.clients.crm_service.update_client_tags")
def test_update_client_tags_client_not_found(mock_update_tags, authenticated_client: TestClient, test_user: User):
    """Tests that updating tags for non-existent client returns 404."""
    # Arrange
    client_id = uuid.uuid4()
    payload = {"user_tags": ["hot-lead"]}
    
    mock_update_tags.return_value = None

    # Act
    response = authenticated_client.put(f"/api/clients/{client_id}/tags", json=payload)

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Client not found."

@patch("api.rest.clients.crm_service.get_all_clients")
def test_get_all_clients_succeeds(mock_get_all, authenticated_client: TestClient, test_user: User):
    """Tests that all clients can be retrieved successfully."""
    # Arrange
    mock_clients = [
        Client(id=uuid.uuid4(), user_id=test_user.id, full_name="Client 1"),
        Client(id=uuid.uuid4(), user_id=test_user.id, full_name="Client 2"),
    ]
    mock_get_all.return_value = mock_clients

    # Act
    response = authenticated_client.get("/api/clients")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    mock_get_all.assert_called_once_with(user_id=test_user.id)

@patch("api.rest.clients.crm_service.get_all_clients")
def test_list_client_ids_debug_endpoint(mock_get_all, authenticated_client: TestClient, test_user: User):
    """Tests the debug endpoint that lists client IDs."""
    # Arrange
    mock_clients = [
        Client(id=uuid.uuid4(), user_id=test_user.id, full_name="Client 1", phone_number="+15551111111"),
        Client(id=uuid.uuid4(), user_id=test_user.id, full_name="Client 2", phone_number="+15552222222"),
    ]
    mock_get_all.return_value = mock_clients

    # Act
    response = authenticated_client.get("/api/clients/debug/list-ids")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == str(test_user.id)
    assert data["client_count"] == 2
    assert len(data["clients"]) == 2
    assert "id" in data["clients"][0]
    assert "name" in data["clients"][0]
    assert "phone" in data["clients"][0]

@patch("api.rest.clients.crm_service.get_client_by_id")
def test_get_client_by_id_succeeds(mock_get_client, authenticated_client: TestClient, test_user: User):
    """Tests that a specific client can be retrieved by ID."""
    # Arrange
    client_id = uuid.uuid4()
    mock_client = Client(id=client_id, user_id=test_user.id, full_name="Test Client")
    mock_get_client.return_value = mock_client

    # Act
    response = authenticated_client.get(f"/api/clients/{client_id}")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(client_id)
    assert data["full_name"] == "Test Client"
    mock_get_client.assert_called_once_with(client_id=client_id, user_id=test_user.id)

@patch("api.rest.clients.crm_service.get_client_by_id")
def test_get_client_by_id_not_found(mock_get_client, authenticated_client: TestClient, test_user: User):
    """Tests that getting non-existent client returns 404."""
    # Arrange
    client_id = uuid.uuid4()
    mock_get_client.return_value = None

    # Act
    response = authenticated_client.get(f"/api/clients/{client_id}")

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Client not found"

@patch("api.rest.clients.crm_service.get_scheduled_messages_for_client")
def test_get_client_scheduled_messages_succeeds(mock_get_messages, authenticated_client: TestClient, test_user: User):
    """Tests that scheduled messages for a client can be retrieved."""
    # Arrange
    client_id = uuid.uuid4()
    mock_messages = [
        ScheduledMessage(id=uuid.uuid4(), client_id=client_id, user_id=test_user.id, message="Test message 1"),
        ScheduledMessage(id=uuid.uuid4(), client_id=client_id, user_id=test_user.id, message="Test message 2"),
    ]
    mock_get_messages.return_value = mock_messages

    # Act
    response = authenticated_client.get(f"/api/clients/{client_id}/scheduled-messages")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    mock_get_messages.assert_called_once_with(client_id=client_id, user_id=test_user.id)

@patch("api.rest.clients.crm_service.update_client")
@patch("agent_core.brain.relationship_planner.plan_relationship_campaign")
@patch("api.rest.clients.websocket_manager.broadcast_to_user")
def test_update_client_details_with_notes_update(
    mock_broadcast, 
    mock_relationship_planner, 
    mock_update_client, 
    authenticated_client: TestClient, 
    test_user: User
):
    """Tests that updating client details with notes triggers relationship planner and websocket notification."""
    # Arrange
    client_id = uuid.uuid4()
    payload = {"notes": "Updated client notes"}
    
    mock_client = Client(id=client_id, user_id=test_user.id, full_name="Test Client")
    mock_update_client.return_value = (mock_client, True)  # notes_were_updated = True
    mock_relationship_planner.return_value = None
    mock_broadcast.return_value = None

    # Act
    response = authenticated_client.put(f"/api/clients/{client_id}", json=payload)

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(client_id)
    mock_update_client.assert_called_once_with(
        client_id=client_id,
        update_data=ClientUpdate(**payload),
        user_id=test_user.id
    )
    mock_relationship_planner.assert_called_once_with(client=mock_client, user=test_user)
    mock_broadcast.assert_called_once_with(
        user_id=str(test_user.id),
        data={"event": "PLAN_UPDATED", "clientId": str(client_id)}
    )

@patch("api.rest.clients.crm_service.update_client")
def test_update_client_details_without_notes_update(mock_update_client, authenticated_client: TestClient, test_user: User):
    """Tests that updating client details without notes doesn't trigger relationship planner."""
    # Arrange
    client_id = uuid.uuid4()
    payload = {"full_name": "Updated Name"}
    
    mock_client = Client(id=client_id, user_id=test_user.id, full_name="Updated Name")
    mock_update_client.return_value = (mock_client, False)  # notes_were_updated = False

    # Act
    response = authenticated_client.put(f"/api/clients/{client_id}", json=payload)

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(client_id)
    mock_update_client.assert_called_once_with(
        client_id=client_id,
        update_data=ClientUpdate(**payload),
        user_id=test_user.id
    )

@patch("api.rest.clients.crm_service.update_client")
def test_update_client_details_client_not_found(mock_update_client, authenticated_client: TestClient, test_user: User):
    """Tests that updating non-existent client returns 404."""
    # Arrange
    client_id = uuid.uuid4()
    payload = {"full_name": "Updated Name"}
    
    mock_update_client.return_value = (None, False)

    # Act
    response = authenticated_client.put(f"/api/clients/{client_id}", json=payload)

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Client not found."

@patch("api.rest.clients.crm_service.delete_client")
def test_delete_client_succeeds(mock_delete_client, authenticated_client: TestClient, test_user: User):
    """Tests that a client can be deleted successfully."""
    # Arrange
    client_id = uuid.uuid4()
    mock_delete_client.return_value = True

    # Act
    response = authenticated_client.delete(f"/api/clients/{client_id}")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Client deleted successfully"
    mock_delete_client.assert_called_once_with(
        client_id=client_id,
        user_id=test_user.id
    )

@patch("api.rest.clients.crm_service.delete_client")
def test_delete_client_not_found(mock_delete_client, authenticated_client: TestClient, test_user: User):
    """Tests that deleting non-existent client returns 404."""
    # Arrange
    client_id = uuid.uuid4()
    mock_delete_client.return_value = False

    # Act
    response = authenticated_client.delete(f"/api/clients/{client_id}")

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Client not found"

@patch("api.rest.clients.crm_service.get_all_clients")
@patch("api.rest.clients.crm_service.update_client")
@patch("data.crm.format_phone_number")
def test_fix_phone_number_formatting_succeeds(
    mock_format_phone, 
    mock_update_client, 
    mock_get_all, 
    authenticated_client: TestClient, 
    test_user: User
):
    """Tests that phone number formatting can be fixed for existing clients."""
    # Arrange
    client_id = uuid.uuid4()
    mock_clients = [
        Client(id=client_id, user_id=test_user.id, full_name="Test Client", phone="5551111111"),
    ]
    mock_get_all.return_value = mock_clients
    mock_format_phone.return_value = "+15551111111"
    
    updated_client = Client(id=client_id, user_id=test_user.id, full_name="Test Client", phone="+15551111111")
    mock_update_client.return_value = (updated_client, False)

    # Act
    response = authenticated_client.post("/api/clients/fix-phone-formatting")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["phone"] == "+15551111111"
    mock_format_phone.assert_called_once_with("5551111111")
    mock_update_client.assert_called_once()

@patch("api.rest.clients.crm_service.delete_scheduled_messages_for_client")
def test_delete_client_scheduled_messages_succeeds(mock_delete_messages, authenticated_client: TestClient, test_user: User):
    """Tests that scheduled messages for a client can be deleted."""
    # Arrange
    client_id = uuid.uuid4()
    mock_delete_messages.return_value = None

    # Act
    response = authenticated_client.delete(f"/api/clients/{client_id}/scheduled-messages")

    # Assert
    assert response.status_code == 204
    mock_delete_messages.assert_called_once_with(client_id=client_id, user_id=test_user.id)

# Test the new Pydantic models
def test_update_intel_payload_model():
    """Tests the UpdateIntelPayload Pydantic model."""
    from api.rest.clients import UpdateIntelPayload
    
    # Test with all fields
    payload = UpdateIntelPayload(
        tags_to_add=["hot-lead", "buyer"],
        notes_to_add="Test notes",
        active_recommendation_id=uuid.uuid4()
    )
    assert payload.tags_to_add == ["hot-lead", "buyer"]
    assert payload.notes_to_add == "Test notes"
    assert payload.active_recommendation_id is not None

    # Test with optional fields
    payload = UpdateIntelPayload()
    assert payload.tags_to_add is None
    assert payload.notes_to_add is None
    assert payload.active_recommendation_id is None

def test_update_notes_payload_model():
    """Tests the UpdateNotesPayload Pydantic model."""
    from api.rest.clients import UpdateNotesPayload
    
    payload = UpdateNotesPayload(notes="Test notes")
    assert payload.notes == "Test notes"

def test_client_search_query_model():
    """Tests the ClientSearchQuery Pydantic model."""
    from api.rest.clients import ClientSearchQuery
    
    # Test with all fields
    query = ClientSearchQuery(
        natural_language_query="clients who want to buy",
        tags=["hot-lead", "buyer"]
    )
    assert query.natural_language_query == "clients who want to buy"
    assert query.tags == ["hot-lead", "buyer"]

    # Test with optional fields
    query = ClientSearchQuery()
    assert query.natural_language_query is None
    assert query.tags is None

def test_add_tags_payload_model():
    """Tests the AddTagsPayload Pydantic model."""
    from api.rest.clients import AddTagsPayload
    
    payload = AddTagsPayload(tags=["hot-lead", "buyer"])
    assert payload.tags == ["hot-lead", "buyer"]
