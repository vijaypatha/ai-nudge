# FILE: backend/agent_core/brain/test_nudge_engine.py

import pytest
import uuid
import logging
from unittest.mock import AsyncMock

from backend.agent_core.brain import nudge_engine
from backend.data import crm as crm_service
from backend.data.models.user import User
from backend.data.models.client import Client
from backend.data.models.event import MarketEvent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@pytest.mark.asyncio
async def test_process_new_listing_event(monkeypatch):
    logger.info("Setting up test data...")
    crm_service.clear_all_data()

    mock_draft = {"ai_draft": "Check out this new property!"}
    monkeypatch.setattr(nudge_engine.conversation_agent, 'generate_response', AsyncMock(return_value=mock_draft))

    realtor = User(full_name="Test Realtor", email="realtor@test.com")
    crm_service.save_user(realtor)

    matching_client = Client(full_name="John Doe", email="john.doe@test.com", preferences={"budget_max": 500000, "locations": ["St. George"], "min_bedrooms": 3})
    crm_service.save_client(matching_client)

    non_matching_client = Client(full_name="Jane Smith", email="jane.smith@test.com", preferences={"budget_max": 300000})
    crm_service.save_client(non_matching_client)

    logger.info("Arranging sample MarketEvent...")
    property_payload = {"ListingId": "DEMO-123", "UnparsedAddress": "123 Main St, St. George, UT", "ListPrice": 450000.0, "BedsTotal": 3, "PropertyType": "A", "MlsStatus": "Active", "ModificationTimestamp": "2025-06-23T12:00:00-06:00"}
    
    UUID_NAMESPACE = uuid.UUID('f1a2b3c4-d5e6-f7a8-b9c0-d1e2f3a4b5c6')
    entity_id = uuid.uuid5(UUID_NAMESPACE, property_payload["ListingId"])

    new_listing_event = MarketEvent(event_type="new_listing", market_area="washington_county_bor", entity_type="PROPERTY", entity_id=entity_id, payload=property_payload)

    logger.info("Calling the Nudge Engine...")
    await nudge_engine.process_market_event(event=new_listing_event, realtor=realtor)

    logger.info("Asserting test outcomes...")
    synced_property = crm_service.get_property_by_id(new_listing_event.entity_id)
    assert synced_property is not None, "Property was not created in CRM"
    assert synced_property.price == 450000.0

    all_campaigns = crm_service.get_new_campaign_briefings_for_user(realtor.id)
    assert len(all_campaigns) == 1, "Expected 1 campaign briefing to be created"
    
    campaign_briefing = all_campaigns[0]
    assert len(campaign_briefing.matched_audience) == 1, "Expected only 1 matched client"
    
    matched_client_in_campaign = campaign_briefing.matched_audience[0]
    assert matched_client_in_campaign.client_id == matching_client.id
    
    logger.info("✅ Test Passed: Nudge Engine successfully processed the event.")