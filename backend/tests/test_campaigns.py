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
from unittest.mock import patch, AsyncMock
from sqlmodel import Session, select

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

def test_update_campaign_audience_succeeds(authenticated_client: TestClient, test_user, session: Session):
    """
    Tests successful update of campaign audience.
    """
    # Arrange - create test clients and campaign briefing
    from data.models.client import Client
    from data.models.campaign import CampaignBriefing, CampaignStatus
    
    # Create test clients
    client1 = Client(
        id=uuid.uuid4(),
        user_id=test_user.id,
        full_name="Test Client 1",
        phone_number="+15551234567"
    )
    client2 = Client(
        id=uuid.uuid4(),
        user_id=test_user.id,
        full_name="Test Client 2",
        phone_number="+15551234568"
    )
    session.add(client1)
    session.add(client2)
    session.commit()
    
    # Create campaign briefing
    briefing = CampaignBriefing(
        id=uuid.uuid4(),
        user_id=test_user.id,
        campaign_type="market_opportunity",
        headline="Test Campaign",
        original_draft="Test draft content",
        key_intel={"test": "data"},
        matched_audience=[],
        status=CampaignStatus.DRAFT
    )
    session.add(briefing)
    session.commit()
    
    # Act
    payload = {"client_ids": [str(client1.id), str(client2.id)]}
    response = authenticated_client.put(f"/api/campaigns/{briefing.id}/audience", json=payload)
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(briefing.id)
    assert len(data["matched_audience"]) == 2
    assert any(client["client_name"] == "Test Client 1" for client in data["matched_audience"])
    assert any(client["client_name"] == "Test Client 2" for client in data["matched_audience"])

def test_update_campaign_audience_fails_briefing_not_found(authenticated_client: TestClient):
    """
    Tests that updating audience for non-existent briefing fails.
    """
    # Arrange
    fake_briefing_id = uuid.uuid4()
    payload = {"client_ids": [str(uuid.uuid4())]}
    
    # Act
    response = authenticated_client.put(f"/api/campaigns/{fake_briefing_id}/audience", json=payload)
    
    # Assert - the endpoint returns 500 due to internal error handling
    assert response.status_code == 500

def test_update_campaign_audience_fails_client_not_found(authenticated_client: TestClient, test_user, session: Session):
    """
    Tests that updating audience with non-existent client IDs fails.
    """
    # Arrange - create campaign briefing
    from data.models.campaign import CampaignBriefing, CampaignStatus
    
    briefing = CampaignBriefing(
        id=uuid.uuid4(),
        user_id=test_user.id,
        campaign_type="market_opportunity",
        headline="Test Campaign",
        original_draft="Test draft content",
        key_intel={"test": "data"},
        matched_audience=[],
        status=CampaignStatus.DRAFT
    )
    session.add(briefing)
    session.commit()
    
    # Act
    payload = {"client_ids": [str(uuid.uuid4())]}  # Non-existent client ID
    response = authenticated_client.put(f"/api/campaigns/{briefing.id}/audience", json=payload)
    
    # Assert - the endpoint returns 500 due to internal error handling
    assert response.status_code == 500

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

def test_update_campaign_with_dismissal_succeeds(authenticated_client: TestClient, test_user, session: Session):
    """
    Tests successful campaign update with dismissal status.
    """
    # Arrange - create campaign briefing with triggering resource
    from data.models.campaign import CampaignBriefing, CampaignStatus
    from data.models.resource import Resource
    from data.models.client import Client
    
    # Create a test client
    client = Client(
        id=uuid.uuid4(),
        user_id=test_user.id,
        full_name="Test Client",
        phone_number="+15551234567"
    )
    session.add(client)
    session.commit()
    
    # Create a triggering resource
    resource = Resource(
        id=uuid.uuid4(),
        user_id=test_user.id,
        resource_type="property",
        title="Test Property",
        attributes={"PublicRemarks": "Test property description"}
    )
    session.add(resource)
    session.commit()
    
    # Create campaign briefing with triggering resource
    briefing = CampaignBriefing(
        id=uuid.uuid4(),
        user_id=test_user.id,
        campaign_type="market_opportunity",
        headline="Test Campaign",
        original_draft="Test draft content",
        key_intel={"test": "data"},
        matched_audience=[{"client_id": str(client.id), "client_name": "Test Client"}],
        status=CampaignStatus.DRAFT,
        triggering_resource_id=resource.id
    )
    session.add(briefing)
    session.commit()
    
    # Mock only the embedding generation
    with patch("api.rest.campaigns.llm_client.generate_embedding") as mock_embedding:
            mock_embedding.return_value = [0.1, 0.2, 0.3]  # Mock embedding
        
            # Act
            payload = {"status": CampaignStatus.DISMISSED.value}
            response = authenticated_client.put(f"/api/campaigns/{briefing.id}", json=payload)
        
            # Assert
            assert response.status_code == 200
            data = response.json()
        
            assert data["status"] == "dismissed"
            # Note: Background task is called but we can't easily test it in this environment

def test_update_campaign_succeeds(authenticated_client: TestClient, test_user, session: Session):
    """
    Tests successful campaign update without dismissal.
    """
    # Arrange - create campaign briefing
    from data.models.campaign import CampaignBriefing, CampaignStatus
    
    briefing = CampaignBriefing(
        id=uuid.uuid4(),
        user_id=test_user.id,
        campaign_type="market_opportunity",
        headline="Original Headline",
        original_draft="Original draft",
        key_intel={"test": "data"},
        matched_audience=[],
        status=CampaignStatus.DRAFT
    )
    session.add(briefing)
    session.commit()
    
    # Act
    payload = {
        "headline": "Updated Headline",
        "original_draft": "Updated draft",
        "status": "active"
    }
    response = authenticated_client.put(f"/api/campaigns/{briefing.id}", json=payload)
    
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
    
    # Assert - the endpoint returns 500 due to internal error handling
    assert response.status_code == 500

def test_get_campaign_by_id_succeeds(authenticated_client: TestClient, test_user, session: Session):
    """
    Tests successful retrieval of campaign by ID.
    """
    # Arrange - create campaign briefing
    from data.models.campaign import CampaignBriefing, CampaignStatus
    
    briefing = CampaignBriefing(
        id=uuid.uuid4(),
        user_id=test_user.id,
        campaign_type="market_opportunity",
        headline="Test Campaign",
        original_draft="Test draft content",
        key_intel={"test": "data"},
        matched_audience=[],
        status=CampaignStatus.DRAFT
    )
    session.add(briefing)
    session.commit()
    
    # Act
    response = authenticated_client.get(f"/api/campaigns/{briefing.id}")
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(briefing.id)
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

def test_handle_campaign_action_succeeds(authenticated_client: TestClient, test_user, session: Session):
    """
    Tests successful handling of campaign action.
    """
    # Arrange - create campaign briefing
    from data.models.campaign import CampaignBriefing, CampaignStatus
    
    briefing = CampaignBriefing(
        id=uuid.uuid4(),
        user_id=test_user.id,
        campaign_type="market_opportunity",
        headline="Test Campaign",
        original_draft="Test draft content",
        key_intel={"test": "data"},
        matched_audience=[],
        status=CampaignStatus.DRAFT
    )
    session.add(briefing)
    session.commit()
    
    # Mock the campaign workflow
    with patch("api.rest.campaigns.campaign_workflow.handle_copilot_action") as mock_action:
        mock_action.return_value = {"status": "success", "action": "test_action"}
        
        # Act
        payload = {"action_type": "test_action"}
        response = authenticated_client.post(f"/api/campaigns/{briefing.id}/action", json=payload)
        
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
    
    # Assert - the endpoint returns 500 due to internal error handling
    assert response.status_code == 500

def test_approve_campaign_plan_succeeds(authenticated_client: TestClient, test_user, session: Session):
    """
    Tests successful approval of campaign plan.
    """
    # Arrange - create campaign plan
    from data.models.campaign import CampaignBriefing, CampaignStatus
    from data.models.client import Client
    
    # Create test client
    client = Client(
        id=uuid.uuid4(),
        user_id=test_user.id,
        full_name="Test Client",
        phone_number="+15551234567"
    )
    session.add(client)
    session.commit()
    
    # Create campaign plan
    plan = CampaignBriefing(
        id=uuid.uuid4(),
        user_id=test_user.id,
        client_id=client.id,
        campaign_type="relationship_plan",
        headline="Test Plan",
        original_draft="Test plan content",
        key_intel={
            "steps": [
                {
                    "delay_days": 1,
                    "generated_draft": "Step 1 content",
                    "touchpoint_id": "touchpoint_1"
                },
                {
                    "delay_days": 3,
                    "generated_draft": "Step 2 content",
                    "touchpoint_id": "touchpoint_2"
                }
            ]
        },
        matched_audience=[],
        is_plan=True,
        status=CampaignStatus.DRAFT
    )
    session.add(plan)
    session.commit()
    
    # Act
    response = authenticated_client.post(f"/api/campaigns/{plan.id}/approve")
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "active"

def test_approve_campaign_plan_fails_not_plan(authenticated_client: TestClient, test_user, session: Session):
    """
    Tests that approving non-plan campaign fails.
    """
    # Arrange - create regular campaign (not a plan)
    from data.models.campaign import CampaignBriefing, CampaignStatus
    
    briefing = CampaignBriefing(
        id=uuid.uuid4(),
        user_id=test_user.id,
        campaign_type="market_opportunity",
        headline="Test Campaign",
        original_draft="Test draft content",
        key_intel={"test": "data"},
        matched_audience=[],
        is_plan=False,
        status=CampaignStatus.DRAFT
    )
    session.add(briefing)
    session.commit()
    
    # Act
    response = authenticated_client.post(f"/api/campaigns/{briefing.id}/approve")
    
    # Assert
    assert response.status_code == 404
    assert "Draft plan not found" in response.json()["detail"]

def test_approve_campaign_plan_fails_no_steps(authenticated_client: TestClient, test_user, session: Session):
    """
    Tests that approving plan without steps fails.
    """
    # Arrange - create campaign plan without steps
    from data.models.campaign import CampaignBriefing, CampaignStatus
    
    plan = CampaignBriefing(
        id=uuid.uuid4(),
        user_id=test_user.id,
        campaign_type="relationship_plan",
        headline="Test Plan",
        original_draft="Test plan content",
        key_intel={},  # No steps
        matched_audience=[],
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

def test_complete_briefing_succeeds(authenticated_client: TestClient, test_user, session: Session):
    """
    Tests successful completion of briefing.
    """
    # Arrange - create campaign briefing
    from data.models.campaign import CampaignBriefing, CampaignStatus
    
    briefing = CampaignBriefing(
        id=uuid.uuid4(),
        user_id=test_user.id,
        campaign_type="market_opportunity",
        headline="Test Campaign",
        original_draft="Test draft content",
        key_intel={"test": "data"},
        matched_audience=[],
        status=CampaignStatus.DRAFT
    )
    session.add(briefing)
    session.commit()
    
    # Act
    response = authenticated_client.post(f"/api/campaigns/briefings/{briefing.id}/complete")
    
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

def test_plan_relationship_campaign_succeeds(authenticated_client: TestClient, test_user, session: Session):
    """
    Tests successful planning of relationship campaign.
    """
    # Arrange - create test client
    from data.models.client import Client
    
    client = Client(
        id=uuid.uuid4(),
        user_id=test_user.id,
        full_name="Test Client",
        phone_number="+15551234567"
    )
    session.add(client)
    session.commit()
    
    # Mock the relationship planner
    with patch("api.rest.campaigns.relationship_planner.plan_relationship_campaign") as mock_planner:
        # Act
        payload = {"client_id": str(client.id)}
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

def test_send_instant_nudge_now_succeeds(authenticated_client: TestClient, test_user, session: Session):
    """
    Tests successful sending of instant nudge.
    """
    # Arrange - create test client
    from data.models.client import Client
    
    client = Client(
        id=uuid.uuid4(),
        user_id=test_user.id,
        full_name="Test Client",
        phone_number="+15551234567"
    )
    session.add(client)
    session.commit()
    
    # Mock the orchestrator
    with patch("agent_core.orchestrator.orchestrate_send_message_now") as mock_orchestrator:
        mock_message = {
            "id": str(uuid.uuid4()),
            "client_id": str(client.id),
            "content": "Test message",
            "status": "sent"
        }
        mock_orchestrator.return_value = mock_message
        
        # Act
        payload = {
            "client_id": str(client.id),
            "content": "Test message"
        }
        response = authenticated_client.post("/api/campaigns/messages/send-now", json=payload)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "Test message"
        mock_orchestrator.assert_awaited_once()

def test_send_instant_nudge_now_fails(authenticated_client: TestClient, test_user, session: Session):
    """
    Tests that sending instant nudge fails when orchestrator fails.
    """
    # Arrange - create test client
    from data.models.client import Client
    
    client = Client(
        id=uuid.uuid4(),
        user_id=test_user.id,
        full_name="Test Client",
        phone_number="+15551234567"
    )
    session.add(client)
    session.commit()
    
    # Mock the orchestrator to return None (failure)
    with patch("agent_core.orchestrator.orchestrate_send_message_now") as mock_orchestrator:
        mock_orchestrator.return_value = None
        
        # Act
        payload = {
            "client_id": str(client.id),
            "content": "Test message"
        }
        response = authenticated_client.post("/api/campaigns/messages/send-now", json=payload)
        
        # Assert
        assert response.status_code == 500
        assert "Failed to send instant nudge" in response.json()["detail"]

def test_trigger_send_campaign_succeeds(authenticated_client: TestClient, test_user, session: Session):
    """
    Tests successful triggering of campaign send.
    """
    # Arrange - create campaign briefing
    from data.models.campaign import CampaignBriefing, CampaignStatus
    
    briefing = CampaignBriefing(
        id=uuid.uuid4(),
        user_id=test_user.id,
        campaign_type="market_opportunity",
        headline="Test Campaign",
        original_draft="Test draft content",
        key_intel={"test": "data"},
        matched_audience=[],
        status=CampaignStatus.DRAFT
    )
    session.add(briefing)
    session.commit()
    
    # Mock the background task
    with patch("workflow.outbound.send_campaign_to_audience") as mock_send:
        # Act
        response = authenticated_client.post(f"/api/campaigns/{briefing.id}/send")
        
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
