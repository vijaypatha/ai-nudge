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
import uuid
from fastapi.testclient import TestClient
from unittest.mock import patch
from sqlmodel import Session
# FIX: Correctly import models from their specific locations
from data.models import User, Client, CampaignBriefing, Resource
from data.models.campaign import CampaignStatus

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

def test_update_campaign_audience_succeeds(authenticated_client: TestClient, test_campaign: CampaignBriefing, test_client: Client, session: Session):
    """
    Tests successful update of campaign audience.
    """
    # Arrange - Create a second client to add to the audience
    client2 = Client(id=uuid.uuid4(), user_id=test_campaign.user_id, full_name="Test Client 2", phone_number="+15551234568")
    session.add(client2)
    session.commit()
    
    # Act
    payload = {"client_ids": [str(test_client.id), str(client2.id)]}
    response = authenticated_client.put(f"/api/campaigns/{test_campaign.id}/audience", json=payload)
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(test_campaign.id)
    assert len(data["matched_audience"]) == 2
    assert any(client["client_id"] == str(test_client.id) for client in data["matched_audience"])
    assert any(client["client_id"] == str(client2.id) for client in data["matched_audience"])

def test_update_campaign_audience_fails_briefing_not_found(authenticated_client: TestClient):
    """
    Tests that updating audience for non-existent briefing fails.
    """
    # Arrange
    fake_briefing_id = uuid.uuid4()
    payload = {"client_ids": [str(uuid.uuid4())]}
    
    # Act
    response = authenticated_client.put(f"/api/campaigns/{fake_briefing_id}/audience", json=payload)
    
    # Assert
    assert response.status_code == 404

def test_update_campaign_audience_fails_client_not_found(authenticated_client: TestClient, test_campaign: CampaignBriefing):
    """
    Tests that updating audience with non-existent client IDs fails.
    """
    # Act
    payload = {"client_ids": [str(uuid.uuid4())]}  # Non-existent client ID
    response = authenticated_client.put(f"/api/campaigns/{test_campaign.id}/audience", json=payload)
    
    # Assert
    assert response.status_code == 404

def test_update_campaign_audience_fails_unauthenticated(client: TestClient):
    """
    Tests that unauthenticated access to audience update is rejected.
    """
    # Arrange
    fake_briefing_id = uuid.uuid4()
    payload = {"client_ids": [str(uuid.uuid4())]}
    
    # Act
    response = client.put(f"/api/campaigns/{fake_briefing_id}/audience", json=payload)
    
    # Assert
    assert response.status_code == 401

def test_update_campaign_with_dismissal_succeeds(authenticated_client: TestClient, test_campaign: CampaignBriefing, test_resource: Resource, session: Session):
    """
    Tests successful campaign update with dismissal status.
    """
    # Arrange
    test_campaign.triggering_resource_id = test_resource.id
    session.add(test_campaign)
    session.commit()
    
    # Mock only the embedding generation
    with patch("api.rest.campaigns.llm_client.generate_embedding") as mock_embedding:
        mock_embedding.return_value = [0.1, 0.2, 0.3]  # Mock embedding
    
        # Act
        payload = {"status": CampaignStatus.DISMISSED.value}
        response = authenticated_client.put(f"/api/campaigns/{test_campaign.id}", json=payload)
    
        # Assert
        assert response.status_code == 200
        data = response.json()
    
        assert data["status"] == "dismissed"

def test_update_campaign_succeeds(authenticated_client: TestClient, test_campaign: CampaignBriefing):
    """
    Tests successful campaign update without dismissal.
    """
    # Act
    payload = {
        "headline": "Updated Headline",
        "original_draft": "Updated draft",
        "status": "active"
    }
    response = authenticated_client.put(f"/api/campaigns/{test_campaign.id}", json=payload)
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["headline"] == "Updated Headline"
    assert data["original_draft"] == "Updated draft"
    assert data["status"] == "active"

def test_update_campaign_fails_not_found(authenticated_client: TestClient):
    """
    Tests that updating non-existent campaign fails.
    """
    # Arrange
    fake_campaign_id = uuid.uuid4()
    payload = {"headline": "Updated Headline"}
    
    # Act
    response = authenticated_client.put(f"/api/campaigns/{fake_campaign_id}", json=payload)
    
    # Assert
    assert response.status_code == 404

def test_get_campaign_by_id_succeeds(authenticated_client: TestClient, test_campaign: CampaignBriefing):
    """
    Tests successful retrieval of campaign by ID.
    """
    # Act
    response = authenticated_client.get(f"/api/campaigns/{test_campaign.id}")
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(test_campaign.id)
    assert data["headline"] == "Test Campaign"

def test_get_campaign_by_id_fails_not_found(authenticated_client: TestClient):
    """
    Tests that getting non-existent campaign fails.
    """
    # Arrange
    fake_campaign_id = uuid.uuid4()
    
    # Act
    response = authenticated_client.get(f"/api/campaigns/{fake_campaign_id}")
    
    # Assert
    assert response.status_code == 404
    assert "Campaign not found" in response.json()["detail"]

def test_get_campaign_by_id_fails_unauthenticated(client: TestClient):
    """
    Tests that unauthenticated access to get campaign is rejected.
    """
    # Arrange
    fake_campaign_id = uuid.uuid4()
    
    # Act
    response = client.get(f"/api/campaigns/{fake_campaign_id}")
    
    # Assert
    assert response.status_code == 401

def test_handle_campaign_action_succeeds(authenticated_client: TestClient, test_campaign: CampaignBriefing):
    """
    Tests successful handling of campaign action.
    """
    # Mock the campaign workflow
    with patch("api.rest.campaigns.campaign_workflow.handle_copilot_action") as mock_action:
        mock_action.return_value = {"status": "success", "action": "test_action"}
        
        # Act
        payload = {"action_type": "test_action"}
        response = authenticated_client.post(f"/api/campaigns/{test_campaign.id}/action", json=payload)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        mock_action.assert_awaited_once()

def test_handle_campaign_action_fails_briefing_not_found(authenticated_client: TestClient):
    """
    Tests that handling action for non-existent briefing fails.
    """
    # Arrange
    fake_briefing_id = uuid.uuid4()
    payload = {"action_type": "test_action"}
    
    # Act
    response = authenticated_client.post(f"/api/campaigns/{fake_briefing_id}/action", json=payload)
    
    # Assert
    assert response.status_code == 404

def test_approve_campaign_plan_succeeds(authenticated_client: TestClient, test_user: User, test_client: Client, session: Session):
    """
    Tests successful approval of campaign plan.
    """
    # Arrange - create campaign plan with steps
    plan = CampaignBriefing(
        id=uuid.uuid4(),
        user_id=test_user.id,
        client_id=test_client.id,
        campaign_type="relationship_plan",
        headline="Test Plan",
        is_plan=True,
        status=CampaignStatus.DRAFT,
        key_intel={
            "steps": [
                {"delay_days": 1, "generated_draft": "Step 1 content", "touchpoint_id": "touchpoint_1"},
                {"delay_days": 3, "generated_draft": "Step 2 content", "touchpoint_id": "touchpoint_2"}
            ]
        }
    )
    session.add(plan)
    session.commit()
    
    # Act
    response = authenticated_client.post(f"/api/campaigns/{plan.id}/approve")
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "active"

def test_approve_campaign_plan_fails_not_plan(authenticated_client: TestClient, test_campaign: CampaignBriefing):
    """
    Tests that approving non-plan campaign fails.
    """
    # Act
    response = authenticated_client.post(f"/api/campaigns/{test_campaign.id}/approve")
    
    # Assert
    assert response.status_code == 404
    assert "Draft plan not found" in response.json()["detail"]

def test_approve_campaign_plan_fails_no_steps(authenticated_client: TestClient, test_user: User, test_client: Client, session: Session):
    """
    Tests that approving plan without steps fails.
    """
    # Arrange - create campaign plan without steps
    plan = CampaignBriefing(
        id=uuid.uuid4(),
        user_id=test_user.id,
        client_id=test_client.id,
        campaign_type="relationship_plan",
        headline="Test Plan",
        key_intel={},  # No steps
        is_plan=True,
        status=CampaignStatus.DRAFT
    )
    session.add(plan)
    session.commit()
    
    # Act
    response = authenticated_client.post(f"/api/campaigns/{plan.id}/approve")
    
    # Assert
    assert response.status_code == 400
    assert "Plan contains no steps" in response.json()["detail"]

def test_complete_briefing_succeeds(authenticated_client: TestClient, test_campaign: CampaignBriefing):
    """
    Tests successful completion of briefing.
    """
    # Act
    response = authenticated_client.post(f"/api/campaigns/briefings/{test_campaign.id}/complete")
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"

def test_complete_briefing_fails_not_found(authenticated_client: TestClient):
    """
    Tests that completing non-existent briefing fails.
    """
    # Arrange
    fake_briefing_id = uuid.uuid4()
    
    # Act
    response = authenticated_client.post(f"/api/campaigns/briefings/{fake_briefing_id}/complete")
    
    # Assert
    assert response.status_code == 404
    assert "Briefing not found" in response.json()["detail"]

def test_plan_relationship_campaign_succeeds(authenticated_client: TestClient, test_client: Client):
    """
    Tests successful planning of relationship campaign.
    """
    # Mock the relationship planner
    with patch("api.rest.campaigns.relationship_planner.plan_relationship_campaign") as mock_planner:
        # Act
        payload = {"client_id": str(test_client.id)}
        response = authenticated_client.post("/api/campaigns/plan-relationship", json=payload)
        
        # Assert
        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "success"
        mock_planner.assert_awaited_once()

def test_plan_relationship_campaign_fails_client_not_found(authenticated_client: TestClient):
    """
    Tests that planning relationship campaign for non-existent client fails.
    """
    # Arrange
    fake_client_id = uuid.uuid4()
    payload = {"client_id": str(fake_client_id)}
    
    # Act
    response = authenticated_client.post("/api/campaigns/plan-relationship", json=payload)
    
    # Assert
    assert response.status_code == 404
    assert "Client not found" in response.json()["detail"]

def test_send_instant_nudge_now_succeeds(authenticated_client: TestClient, test_client: Client):
    """
    Tests successful sending of instant nudge.
    """
    # Mock the orchestrator
    with patch("agent_core.orchestrator.orchestrate_send_message_now") as mock_orchestrator:
        mock_message = {
            "id": str(uuid.uuid4()),
            "client_id": str(test_client.id),
            "content": "Test message",
            "status": "sent"
        }
        mock_orchestrator.return_value = mock_message
        
        # Act
        payload = {
            "client_id": str(test_client.id),
            "content": "Test message"
        }
        response = authenticated_client.post("/api/campaigns/messages/send-now", json=payload)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "Test message"
        mock_orchestrator.assert_awaited_once()

def test_send_instant_nudge_now_fails(authenticated_client: TestClient, test_client: Client):
    """
    Tests that sending instant nudge fails when orchestrator fails.
    """
    # Mock the orchestrator to return None (failure)
    with patch("agent_core.orchestrator.orchestrate_send_message_now") as mock_orchestrator:
        mock_orchestrator.return_value = None
        
        # Act
        payload = {
            "client_id": str(test_client.id),
            "content": "Test message"
        }
        response = authenticated_client.post("/api/campaigns/messages/send-now", json=payload)
        
        # Assert
        assert response.status_code == 500
        assert "Failed to send instant nudge" in response.json()["detail"]

def test_trigger_send_campaign_succeeds(authenticated_client: TestClient, test_campaign: CampaignBriefing):
    """
    Tests successful triggering of campaign send.
    """
    # Mock the background task
    with patch("workflow.outbound.send_campaign_to_audience.delay") as mock_send:
        # Act
        response = authenticated_client.post(f"/api/campaigns/{test_campaign.id}/send")
        
        # Assert
        assert response.status_code == 202
        data = response.json()
        assert data["message"] == "Campaign sending process started."
        mock_send.assert_called_once()

def test_trigger_send_campaign_fails_not_found(authenticated_client: TestClient):
    """
    Tests that triggering send for non-existent campaign fails.
    """
    # Arrange
    fake_campaign_id = uuid.uuid4()
    
    # Act
    response = authenticated_client.post(f"/api/campaigns/{fake_campaign_id}/send")
    
    # Assert
    assert response.status_code == 404
    assert "Campaign not found" in response.json()["detail"]

# --- NEW TESTS FOR CLIENT SUMMARIES ENDPOINT ---

def test_get_client_summaries_succeeds(authenticated_client: TestClient, test_user: User):
    """Tests successful retrieval of client nudge summaries."""
    # Act
    response = authenticated_client.get("/api/campaigns/client-summaries")

    # Assert
    assert response.status_code == 200
    data = response.json()
    
    # Check for required fields based on ClientNudgeSummaryResponse model
    assert "client_summaries" in data
    assert "display_config" in data
    
    # client_summaries should be a list
    assert isinstance(data["client_summaries"], list)
    
    # display_config should be a dict
    assert isinstance(data["display_config"], dict)

def test_get_client_summaries_fails_unauthenticated(client: TestClient):
    """Tests that unauthenticated access to client summaries is rejected."""
    # Act
    response = client.get("/api/campaigns/client-summaries")

    # Assert
    assert response.status_code == 401

def test_get_client_summaries_returns_correct_structure(authenticated_client: TestClient, test_client: Client):
    """Tests that the client summaries endpoint returns the correct data structure."""
    # Act
    response = authenticated_client.get("/api/campaigns/client-summaries")

    # Assert
    assert response.status_code == 200
    data = response.json()
    
    # If there are client summaries, verify the structure
    if len(data["client_summaries"]) > 0:
        summary = data["client_summaries"][0]
        # Check for required fields based on the expected structure
        assert "client_id" in summary
        assert "client_name" in summary
        assert "total_nudges" in summary
        assert "nudge_type_counts" in summary
        
        # Verify data types
        assert isinstance(summary["client_id"], str)
        assert isinstance(summary["client_name"], str)
        assert isinstance(summary["total_nudges"], int)
        assert isinstance(summary["nudge_type_counts"], dict)

def test_get_client_summaries_display_config_structure(authenticated_client: TestClient):
    """Tests that the display_config has the expected structure."""
    # Act
    response = authenticated_client.get("/api/campaigns/client-summaries")

    # Assert
    assert response.status_code == 200
    data = response.json()
    
    display_config = data["display_config"]
    assert isinstance(display_config, dict)
    
    # Check that display_config contains expected campaign types
    # This may vary based on the user's vertical, but should have some structure
    for campaign_type, config in display_config.items():
        assert isinstance(config, dict)
        # Check for expected display config fields
        if "icon" in config:
            assert isinstance(config["icon"], str)
        if "color" in config:
            assert isinstance(config["color"], str)
        if "title" in config:
            assert isinstance(config["title"], str)