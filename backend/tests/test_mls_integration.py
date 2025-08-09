# File: backend/tests/test_mls_integration.py
# 
# What does this file test:
# This file tests MLS (Multiple Listing Service) integration functionality including
# new listing event processing, campaign creation from market events, and MLS data
# handling for real estate vertical. It validates the pipeline for processing
# property listings and converting them into marketing campaigns.
# 
# When was it updated: 2025-01-27
# --- CORRECTED: Refactored to use the generic Resource model instead of the deleted Property model.

import pytest
import uuid
from unittest.mock import patch, AsyncMock
from sqlmodel import Session, select

from data.models.user import User
from data.models.client import Client
from data.models.event import MarketEvent
# --- MODIFIED: Import Resource instead of Property ---
from data.models.resource import Resource
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
        
        realtor = User(
            id=uuid.uuid4(), 
            full_name="Test Realtor", 
            email="realtor@test.com", 
            phone_number="+15551112222",
            vertical="real_estate"
        )
        
        matching_client = Client(
            id=uuid.uuid4(), user_id=realtor.id, full_name="Matching Client",
            email="matching@test.com", phone_number="+15553334444",
            preferences={
                "budget_max": 800000, 
                "locations": ["Pleasant Grove"], 
                "min_bedrooms": 4
            },
            user_tags=["buyer"]
        )
        session.add(realtor)
        session.add(matching_client)
        
        property_attributes = {
            "address": "123 Main St, Pleasant Grove, UT", 
            "price": 750000.0, 
            "bedrooms": 4,
            "property_type": "SingleFamily", 
            "listing_url": "http://example.com/123",
            "last_updated": "2025-07-07T12:00:00Z",
            "ListPrice": 750000,
            "BedroomsTotal": 4,
            "City": "Pleasant Grove",
            "SubdivisionName": "Pleasant Grove",
            "PublicRemarks": "Beautiful home in Pleasant Grove with 4 bedrooms"
        }
        # Use a consistent UUID for the resource
        resource_id = uuid.uuid5(uuid.NAMESPACE_DNS, property_attributes["address"])

        resource_to_save = Resource(
            id=resource_id, 
            user_id=realtor.id,
            resource_type="property",
            status="ACTIVE",
            entity_id=str(resource_id), # Ensure entity_id is set
            attributes=property_attributes
        )
        session.add(resource_to_save)
        session.commit()
        
        new_listing_event = MarketEvent(
            id=uuid.uuid4(),
            user_id=realtor.id,
            event_type="new_listing", 
            market_area="pleasant_grove", 
            entity_type="property", # Corrected to match resource_type
            entity_id=str(resource_id), 
            payload=property_attributes
        )

        # 2. ACT
        # --- THIS IS THE FIX ---
        # Call the new, refactored nudge engine function directly.
        await nudge_engine.find_best_match_for_event(
            event=new_listing_event, 
            user=realtor, 
            resource=resource_to_save, 
            db_session=session
        )

        # 3. ASSERT
        statement = select(CampaignBriefing).where(CampaignBriefing.user_id == realtor.id)
        all_campaigns = session.exec(statement).all()

        assert len(all_campaigns) == 1
        campaign_briefing = all_campaigns[0]
        assert len(campaign_briefing.matched_audience) == 1
        assert campaign_briefing.matched_audience[0]["client_id"] == str(matching_client.id)