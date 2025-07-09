# File: backend/tests/test_mls_integration.py

import pytest
import uuid
from unittest.mock import patch, AsyncMock
from sqlmodel import Session, select

from data.models.user import User
from data.models.client import Client
from data.models.event import MarketEvent
from data.models.property import Property
from data.models.campaign import CampaignBriefing
from agent_core.brain import nudge_engine

@pytest.mark.asyncio
async def test_mls_new_listing_event_creates_campaign(session: Session):
    """
    An integration test for the core business logic that uses the live
    test database session to ensure data visibility.
    """
    # 1. ARRANGE
    with patch("agent_core.brain.nudge_engine.conversation_agent.draft_outbound_campaign_message", new_callable=AsyncMock) as mock_draft:
        mock_draft.return_value = "Check out this amazing new property!"
        
        realtor = User(id=uuid.uuid4(), full_name="Test Realtor", email="realtor@test.com", phone_number="+15551112222")
        
        matching_client = Client(
            id=uuid.uuid4(), user_id=realtor.id, full_name="Matching Client",
            email="matching@test.com", phone_number="+15553334444",
            preferences={"budget_max": 800000, "locations": ["Pleasant Grove"], "min_bedrooms": 4}
        )
        session.add(realtor)
        session.add(matching_client)
        
        property_payload = {
            "address": "123 Main St, Pleasant Grove, UT", "price": 750000.0, "bedrooms": 4,
            "property_type": "SingleFamily", "status": "Active", "listing_url": "http://example.com/123",
            "last_updated": "2025-07-07T12:00:00Z"
        }
        entity_id = uuid.uuid5(uuid.NAMESPACE_DNS, property_payload["address"])
        property_to_save = Property(id=entity_id, **property_payload)
        
        session.add(property_to_save)
        session.commit()
        
        new_listing_event = MarketEvent(
            id=uuid.uuid4(),
            event_type="new_listing", market_area="pleasant_grove", entity_type="PROPERTY",
            entity_id=entity_id, payload=property_payload
        )

        # 2. ACT
        await nudge_engine.process_market_event(event=new_listing_event, realtor=realtor, db_session=session)

        # 3. ASSERT
        statement = select(CampaignBriefing).where(CampaignBriefing.user_id == realtor.id)
        all_campaigns = session.exec(statement).all()

        assert len(all_campaigns) == 1
        campaign_briefing = all_campaigns[0]
        assert len(campaign_briefing.matched_audience) == 1
        assert campaign_briefing.matched_audience[0]["client_id"] == str(matching_client.id)