# ---
# FILE PATH: backend/integrations/mls/flexmls_spark_api.py
# PURPOSE: Connects to Flexmls and implements new event fetching logic.
# --- UPDATED ---
import requests
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from dateutil import parser 

from .base import MlsApiInterface
from common.config import get_settings

logger = logging.getLogger(__name__)

class FlexmlsSparkApi(MlsApiInterface):
    """
    Connects to the Flexmls Spark API using the centralized settings.
    """
    def __init__(self):
        settings = get_settings()
        self.access_token = settings.SPARK_API_DEMO_TOKEN
        if not self.access_token:
            raise ValueError("SPARK_API_DEMO_TOKEN must be set.")
        
        self.api_base_url = "https://api.sparkapi.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Accept-Encoding": "gzip, deflate"
        }

    def authenticate(self) -> bool:
        """Verifies that the access token is present."""
        if self.access_token:
            logger.info("FlexmlsSparkApi: Authentication successful (API key is present).")
            return True
        logger.error("FlexmlsSparkApi: Authentication failed. SPARK_API_DEMO_TOKEN not found.")
        return False

    def _get_listings(self) -> Optional[List[Dict[str, Any]]]:
        """
        Makes a single, proven API call to get a sorted list of recent listings.
        """
        # Fetching more results to increase the chance of finding all event types
        params = {
            "_orderby": "-ModificationTimestamp",
            "_limit": 75 
        }
        request_url = f"{self.api_base_url}/listings"
        logger.info(f"Making Spark API request to URL: {request_url} with params: {params}")

        try:
            response = requests.get(request_url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            results = response.json().get('D', {}).get('Results', [])
            logger.info(f"Successfully fetched {len(results)} raw records from Spark API.")
            return results
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching listings: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Spark API Response Body: {e.response.text}")
            return None

    def _filter_results(
        self, 
        results: List[Dict[str, Any]], 
        minutes_ago: int, 
        price_change_only: bool = False,
        status_filter: Optional[str] = None,
        previous_status_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Performs versatile filtering in Python on the raw results from the API.
        Can filter by time, price changes, current status, and previous status.
        """
        filtered_results = []
        start_time = datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)
        
        for listing in results:
            standard_fields = listing.get("StandardFields", {})
            if not standard_fields: continue

            try:
                mod_timestamp_str = standard_fields.get("ModificationTimestamp")
                if not mod_timestamp_str: continue
                mod_timestamp = parser.isoparse(mod_timestamp_str)
                # If we've gone past our time window in the sorted list, we can stop.
                if mod_timestamp < start_time:
                    break 
            except (ValueError, TypeError):
                logger.warning(f"Could not parse ModificationTimestamp: {mod_timestamp_str}")
                continue
            
            # --- Filtering Logic ---
            passes_filters = True
            
            # 1. Price Change Filter
            if price_change_only:
                prev_price = standard_fields.get("PreviousListPrice")
                list_price = standard_fields.get("ListPrice")
                if not (prev_price is not None and list_price is not None and prev_price != list_price):
                    passes_filters = False

            # 2. Current Status Filter
            current_status = standard_fields.get("MlsStatus")
            if status_filter and current_status != status_filter:
                passes_filters = False

            # 3. Previous Status Filter (for Back on Market)
            previous_status = standard_fields.get("PreviousMlsStatus")
            if previous_status_filter and previous_status != previous_status_filter:
                passes_filters = False

            if passes_filters:
                filtered_results.append(listing)
        
        logger.info(f"Python filtering complete. Found {len(filtered_results)} matching listings.")
        return filtered_results

    def fetch_new_listings(self, minutes_ago: int) -> Optional[List[Dict[str, Any]]]:
        """Fetches and filters listings to find new, active listings."""
        all_recent_listings = self._get_listings()
        if all_recent_listings is None:
            return None 
        
        return self._filter_results(all_recent_listings, minutes_ago, status_filter="Active")

    def fetch_price_changes(self, minutes_ago: int) -> Optional[List[Dict[str, Any]]]:
        """Fetches and filters listings to find recent price changes."""
        all_recent_listings = self._get_listings()
        if all_recent_listings is None:
            return None
            
        return self._filter_results(all_recent_listings, minutes_ago, price_change_only=True)
    
    # --- NEWLY IMPLEMENTED METHODS ---
    def fetch_sold_listings(self, minutes_ago: int) -> Optional[List[Dict[str, Any]]]:
        """Fetches listings with a status of 'Closed' within the time window."""
        all_recent_listings = self._get_listings()
        if all_recent_listings is None: return None
        # In most MLS systems (including Spark API), "Sold" is represented as "Closed".
        return self._filter_results(all_recent_listings, minutes_ago, status_filter="Closed")

    def fetch_back_on_market_listings(self, minutes_ago: int) -> Optional[List[Dict[str, Any]]]:
        """Fetches listings that are now 'Active' but were previously 'Pending'."""
        all_recent_listings = self._get_listings()
        if all_recent_listings is None: return None
        # This event occurs when a sale falls through. The status changes from Pending to Active.
        return self._filter_results(
            all_recent_listings, 
            minutes_ago, 
            status_filter="Active", 
            previous_status_filter="Pending"
        )