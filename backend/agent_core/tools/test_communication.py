# FILE: backend/agent_core/tools/test_communication.py
# PURPOSE: Tests the full 'Act' layer from orchestrator to communication tool.

import pytest
import uuid
from unittest.mock import patch, MagicMock

# Use absolute imports
from backend.agent_core import orchestrator
from backend.data import crm as crm_service
from backend.data.models.campaign import CampaignBriefing, MatchedClient
from backend.data.models.client import Client
from backend.data.models.user import User

@pytest.fixture(autouse=True)
def setup_teardown():
    """Ensures the mock database is clean for every test."""
    crm_service.clear_all_data()
    yield
    crm_service.clear_all_data()

@pytest.mark.asyncio
@patch('backend.integrations.twilio_outgoing.send_sms') # Mock the actual SMS sending function
async def test_orchestrate_launch_campaign(mock_send_sms: MagicMock):
    """
    Tests that the orchestrator correctly launches a campaign,
    and the communication tool calls the Twilio integration for each client.
    """
    # 1. ARRANGE: Create mock user, clients, and a campaign
    mock_send_sms.return_value = True # Assume SMS sending is always successful

    realtor = User(full_name="Test Realtor", email="realtor@test.com")
    crm_service.save_user(realtor)

    client1 = Client(full_name="Client One", email="client1@test.com", phone="+15551112222")
    crm_service.save_client(client1)
    
    client2 = Client(full_name="Client Two", email="client2@test.com", phone="+15553334444")
    crm_service.save_client(client2)

    # --- (FIX) Added the missing required fields to the mock CampaignBriefing ---
    campaign = CampaignBriefing(
        user_id=realtor.id,
        headline="Test Campaign",
        original_draft="This is a test nudge!",
        key_intel={"info": "Test data"}, # Add required key_intel
        triggering_event_id=uuid.uuid4(), # Add required triggering_event_id
        matched_audience=[
            MatchedClient(client_id=client1.id, client_name=client1.full_name, match_score=100, match_reason="Test"),
            MatchedClient(client_id=client2.id, client_name=client2.full_name, match_score=100, match_reason="Test")
        ]
    )
    crm_service.save_campaign_briefing(campaign)

    # 2. ACT: Call the orchestrator, which is the entry point from the API
    success = await orchestrator.orchestrate_launch_campaign(campaign.id)

    # 3. ASSERT: Verify the outcome
    assert success is True, "Orchestrator should report success."
    
    assert mock_send_sms.call_count == 2
    
    mock_send_sms.assert_any_call(to_number=client1.phone, body=campaign.original_draft)
    mock_send_sms.assert_any_call(to_number=client2.phone, body=campaign.original_draft)
    
    # Verify the campaign status was updated after sending
    updated_campaign = next((c for c in crm_service.mock_campaigns_db if c.id == campaign.id), None)
    assert updated_campaign is not None, "Campaign should still exist."
    assert updated_campaign.status == "sent", "Campaign status should be updated to 'sent'."
    
    print("\n✅ Test Passed: 'Act' layer successfully orchestrated campaign launch.")