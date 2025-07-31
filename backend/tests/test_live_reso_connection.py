# FILE: backend/tests/test_live_reso_connection.py
# --- REFACTORED: Updated to use the generic tool factory and test get_events() ---
#
# What does this file test:
# This file tests live RESO (Real Estate Standards Organization) connection
# functionality including MLS data integration, property data retrieval,
# and real-time MLS feed processing. It validates the live connection
# to MLS systems for real estate vertical data synchronization.
# 
# When was it updated: 2025-01-27
#
# HOW TO RUN:
# 1. Ensure your .env file has the correct RESO_API_TOKEN and RESO_API_BASE_URL.
# 2. From your terminal, run:
#    RUN_LIVE_TESTS=1 pytest backend/tests/test_live_reso_connection.py -v -s

import pytest
import os
import logging
import uuid
from typing import List

# --- CHANGE: Import the new generic tool factory and interfaces ---
from integrations.tool_factory import get_tool_for_user
from integrations.tool_interface import ToolInterface, Event
from data.models.user import User

# --- Test Configuration ---
LIVE_TEST_ENABLED = os.environ.get("RUN_LIVE_TESTS") == "1"

# --- REFACTORED Pytest Fixture ---
@pytest.fixture(scope="module")
def live_reso_tool() -> ToolInterface:
    """
    Initializes and returns a live RESO API tool client.
    
    This fixture now creates a dummy user, configures them to use the
    'flexmls_reso' provider, and then uses the generic get_tool_for_user factory.
    """
    # Create a dummy user and configure it for this test run
    test_user = User(id=uuid.uuid4(), email="test@example.com", tool_provider="flexmls_reso")
    
    # Get the tool using our new generic factory
    tool = get_tool_for_user(test_user)
    
    # Ensure the tool was created successfully
    assert tool is not None, "Failed to create the 'flexmls_reso' tool. Check .env settings and factory logic."
    
    # Authenticate with the live service
    is_authenticated = tool.authenticate()
    assert is_authenticated, "Authentication failed. Check your RESO_API_TOKEN."
    
    return tool

# --- REFACTORED Test Class ---
@pytest.mark.skipif(not LIVE_TEST_ENABLED, reason="Skipping live API tests. Set RUN_LIVE_TESTS=1 to enable.")
class TestLiveResoConnection:
    """
    A suite of tests to validate the functionality of any tool that implements ToolInterface.
    The primary test focuses on the get_events() method, which is the main contract.
    """
    
    def _validate_events_response(self, response: List[Event], method_name: str):
        """
        A helper function to perform common assertions on the get_events() response.
        It validates the structure of the standardized Event objects.
        """
        logging.info(f"Response from {method_name}: Found {len(response)} standard Event objects.")
        
        # 1. The call should succeed and return a list of Event objects.
        assert response is not None, f"{method_name} returned None, indicating a request failure."
        assert isinstance(response, list), f"{method_name} did not return a list."
        
        # 2. If the list is not empty, validate the data structure of the first Event.
        if response:
            first_event = response[0]
            logging.info(f"First event for {method_name}: {first_event.model_dump_json(indent=2)}")
            assert isinstance(first_event, Event), "Response item is not a Pydantic Event object."
            
            # Check for essential fields defined in our Event model
            assert first_event.event_type and isinstance(first_event.event_type, str)
            assert first_event.entity_id and isinstance(first_event.entity_id, str)
            assert first_event.raw_data and isinstance(first_event.raw_data, dict)
            assert "ListingKey" in first_event.raw_data, "raw_data missing 'ListingKey'."

    def test_get_events(self, live_reso_tool: ToolInterface):
        """
        Validates the primary get_events method against the live RESO API.
        This single test effectively validates that all the underlying fetch_* methods
        are working and that their data is being correctly transformed into the
        standard Event format.
        """
        logging.info("--- Testing get_events ---")
        # Look back 24 hours to ensure we get a variety of event types
        events = live_reso_tool.get_events(minutes_ago=1440) 
        self._validate_events_response(events, "get_events")