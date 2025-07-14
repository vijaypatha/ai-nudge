# FILE: backend/tests/test_live_reso_connection.py
# PURPOSE: A dedicated, manually-triggered test to validate the live Flexmls RESO API connection.
#
# HOW TO RUN:
# 1. Ensure your .env file has the correct RESO_API_TOKEN and RESO_API_BASE_URL.
# 2. From your terminal, run the following command:
#    RUN_LIVE_TESTS=1 pytest backend/tests/test_live_reso_connection.py -v -s
#
# NOTE: This test is skipped by default to prevent accidental runs against the live,
# paid API during regular development and automated CI/CD checks.

import pytest
import os
import logging
from typing import List, Dict, Any

from integrations.mls.factory import get_mls_client
from integrations.mls.base import MlsApiInterface

# --- Test Configuration ---
# This test will only run if the environment variable 'RUN_LIVE_TESTS' is set to '1'.
LIVE_TEST_ENABLED = os.environ.get("RUN_LIVE_TESTS") == "1"

# --- Pytest Fixture ---
# A fixture to set up our test environment. It temporarily overrides the MLS_PROVIDER
# environment variable to ensure we are testing the 'flexmls_reso' client.
@pytest.fixture(scope="function")
def live_reso_client(monkeypatch) -> MlsApiInterface:
    """
    Initializes and returns a live RESO API client.
    
    This fixture uses monkeypatch to temporarily set the MLS_PROVIDER environment
    variable to 'flexmls_reso', ensuring the factory creates the correct client.
    It will only yield a client if the live tests are explicitly enabled.
    """
    # Set the environment variable for the factory to pick up
    monkeypatch.setenv("MLS_PROVIDER", "flexmls_reso")
    
    # Get the client using our factory
    client = get_mls_client()
    
    # Ensure the client was created successfully
    assert client is not None, "Failed to create the 'flexmls_reso' client. Check .env settings."
    
    # Authenticate with the live service
    is_authenticated = client.authenticate()
    assert is_authenticated, "Authentication failed. Check your RESO_API_TOKEN."
    
    return client


# --- Test Class ---
@pytest.mark.skipif(not LIVE_TEST_ENABLED, reason="Skipping live API tests. Set RUN_LIVE_TESTS=1 to enable.")
class TestLiveResoConnection:
    """
    A suite of tests to validate the functionality of the FlexmlsResoApi client.
    Each test corresponds to a method required by the MlsApiInterface.
    """
    
    # --- FIX: Corrected the type hint from List[Dict, Any] to List[Dict[str, Any]] ---
    def _validate_response(self, response: List[Dict[str, Any]], method_name: str):
        """
        A helper function to perform common assertions on the API response.
        
        Args:
            response: The data returned from the API client call.
            method_name: The name of the method being tested, for logging purposes.
        """
        logging.info(f"Response from {method_name}: Found {len(response)} records.")
        
        # 1. The call should succeed and return a list, even if it's empty.
        assert response is not None, f"{method_name} returned None, indicating a request failure."
        assert isinstance(response, list), f"{method_name} did not return a list."
        
        # 2. If the list is not empty, validate the data structure of the first item.
        if response:
            first_item = response[0]
            logging.info(f"First item structure for {method_name}: {first_item.keys()}")
            assert isinstance(first_item, dict), "Response item is not a dictionary."
            # Check for essential RESO standard fields to confirm we're getting valid data
            assert "ListingKey" in first_item, "Response item missing 'ListingKey'."
            assert "StandardStatus" in first_item, "Response item missing 'StandardStatus'."
            assert "ListPrice" in first_item, "Response item missing 'ListPrice'."

    def test_fetch_new_listings(self, live_reso_client: MlsApiInterface):
        """Validates the fetch_new_listings method against the live RESO API."""
        logging.info("--- Testing fetch_new_listings ---")
        result = live_reso_client.fetch_new_listings(minutes_ago=1440) # Look back 24 hours
        self._validate_response(result, "fetch_new_listings")

    def test_fetch_price_changes(self, live_reso_client: MlsApiInterface):
        """Validates the fetch_price_changes method against the live RESO API."""
        logging.info("--- Testing fetch_price_changes ---")
        result = live_reso_client.fetch_price_changes(minutes_ago=1440)
        self._validate_response(result, "fetch_price_changes")

    def test_fetch_sold_listings(self, live_reso_client: MlsApiInterface):
        """Validates the fetch_sold_listings method against the live RESO API."""
        logging.info("--- Testing fetch_sold_listings ---")
        result = live_reso_client.fetch_sold_listings(minutes_ago=1440)
        self._validate_response(result, "fetch_sold_listings")

    def test_fetch_back_on_market_listings(self, live_reso_client: MlsApiInterface):
        """Validates the fetch_back_on_market_listings method against the live RESO API."""
        logging.info("--- Testing fetch_back_on_market_listings ---")
        result = live_reso_client.fetch_back_on_market_listings(minutes_ago=1440)
        self._validate_response(result, "fetch_back_on_market_listings")

    def test_fetch_expired_listings(self, live_reso_client: MlsApiInterface):
        """Validates the fetch_expired_listings method against the live RESO API."""
        logging.info("--- Testing fetch_expired_listings ---")
        result = live_reso_client.fetch_expired_listings(minutes_ago=1440)
        self._validate_response(result, "fetch_expired_listings")

    def test_fetch_coming_soon_listings(self, live_reso_client: MlsApiInterface):
        """Validates the fetch_coming_soon_listings method against the live RESO API."""
        logging.info("--- Testing fetch_coming_soon_listings ---")
        result = live_reso_client.fetch_coming_soon_listings(minutes_ago=1440)
        self._validate_response(result, "fetch_coming_soon_listings")
        
    def test_fetch_withdrawn_listings(self, live_reso_client: MlsApiInterface):
        """Validates the fetch_withdrawn_listings method against the live RESO API."""
        logging.info("--- Testing fetch_withdrawn_listings ---")
        result = live_reso_client.fetch_withdrawn_listings(minutes_ago=1440)
        self._validate_response(result, "fetch_withdrawn_listings")