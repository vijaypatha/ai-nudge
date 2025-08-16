# FILE PATH: backend/integrations/mls/flexmls_reso_api.py
import requests
import logging
import time # <-- ADDED for retry logic
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from dateutil import parser 

from .base import MlsApiInterface
from common.config import get_settings
from integrations.tool_interface import Event

logger = logging.getLogger(__name__)

class FlexmlsResoApi(MlsApiInterface):
    """
    Connects to the Flexmls RESO Web API (OData) using live credentials.
    """
    def __init__(self, access_token: Optional[str] = None, api_base_url: Optional[str] = None):
        settings = get_settings()
        self.access_token = settings.RESO_API_TOKEN
        self.api_base_url = settings.RESO_API_BASE_URL
        if not self.access_token or not self.api_base_url:
            raise ValueError("Access token and API base URL must be provided.")
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Accept-Encoding": "gzip, deflate"
        }

    def authenticate(self) -> bool:
        if self.access_token:
            logger.info("FlexmlsResoApi: Authentication successful (API key is present).")
            return True
        logger.error("FlexmlsResoApi: Authentication failed. RESO_API_TOKEN not found.")
        return False

    def _get_listings(self) -> Optional[List[Dict[str, Any]]]:
        # --- THIS IS THE FIX ---
        # Implements a retry mechanism with exponential backoff to handle rate limiting.
        params = {
            "$orderby": "ModificationTimestamp desc",
            "$top": 200, 
            "$expand": "Media"
        }
        request_url = f"{self.api_base_url}/Property"
        max_retries = 4
        base_delay = 2  # seconds

        for attempt in range(max_retries):
            try:
                logger.info(f"Making RESO API request to URL: {request_url} (Attempt {attempt + 1})")
                response = requests.get(request_url, headers=self.headers, params=params, timeout=30)
                
                if response.status_code == 429:
                    delay = base_delay * (2 ** attempt)
                    logger.warning(f"Rate limit exceeded (429). Retrying in {delay} seconds...")
                    time.sleep(delay)
                    continue # Go to the next attempt

                response.raise_for_status() # Raise HTTPError for other bad responses (4xx or 5xx)
                results = response.json().get('value', [])
                logger.info(f"Successfully fetched {len(results)} raw records from RESO API.")
                return results

            except requests.exceptions.RequestException as e:
                logger.error(f"Error fetching listings from RESO API on attempt {attempt + 1}: {e}")
                if attempt == max_retries - 1:
                    logger.error("All retry attempts failed.")
                    if hasattr(e, 'response') and e.response:
                        logger.error(f"RESO API Final Response Body: {e.response.text}")
                    return None
                
                delay = base_delay * (2 ** attempt)
                time.sleep(delay)
        
        return None # Should not be reached, but as a fallback
        # --- END FIX ---

    def _filter_results(
        self, 
        results: List[Dict[str, Any]], 
        minutes_ago: int, 
        price_change_only: bool = False,
        status_filter: Optional[str] = None,
        previous_status_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        filtered_results = []
        start_time = datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)
        
        for listing in results:
            try:
                mod_timestamp_str = listing.get("ModificationTimestamp")
                if not mod_timestamp_str: continue
                mod_timestamp = parser.isoparse(mod_timestamp_str)
                if mod_timestamp < start_time:
                    continue
            except (ValueError, TypeError):
                logger.warning(f"Could not parse ModificationTimestamp: {mod_timestamp_str}")
                continue
            
            passes_filters = True
            if price_change_only:
                prev_price = listing.get("OriginalListPrice")
                list_price = listing.get("ListPrice")
                if not (prev_price is not None and list_price is not None and prev_price != list_price):
                    passes_filters = False

            current_status = listing.get("StandardStatus")
            if status_filter and current_status != status_filter:
                passes_filters = False
            
            previous_status = listing.get("PreviousStandardStatus")
            if previous_status_filter and previous_status != previous_status_filter:
                passes_filters = False

            if passes_filters:
                filtered_results.append(listing)
        
        return filtered_results

    def fetch_new_listings(self, minutes_ago: int) -> Optional[List[Dict[str, Any]]]: pass
    def fetch_price_changes(self, minutes_ago: int) -> Optional[List[Dict[str, Any]]]: pass
    def fetch_sold_listings(self, minutes_ago: int) -> Optional[List[Dict[str, Any]]]: pass
    def fetch_back_on_market_listings(self, minutes_ago: int) -> Optional[List[Dict[str, Any]]]: pass
    def fetch_expired_listings(self, minutes_ago: int) -> Optional[List[Dict[str, Any]]]: pass
    def fetch_coming_soon_listings(self, minutes_ago: int) -> Optional[List[Dict[str, Any]]]: pass
    def fetch_withdrawn_listings(self, minutes_ago: int) -> Optional[List[Dict[str, Any]]]: pass

    def get_events(self, minutes_ago: int) -> List[Event]:
        all_events: List[Event] = []
        all_recent_listings = self._get_listings()

        if all_recent_listings is None:
            logger.error("Failed to fetch listings batch, cannot generate events.")
            return []

        event_filters = {
            "new_listing": {"status_filter": "Active"},
            "price_change": {"price_change_only": True},
            "sold_listing": {"status_filter": "Closed"},
            "back_on_market": {"status_filter": "Active", "previous_status_filter": "Pending"},
            "expired_listing": {"status_filter": "Expired"},
            "coming_soon": {"status_filter": "Coming Soon"},
            "withdrawn_listing": {"status_filter": "Withdrawn"},
        }

        def _create_event(listing: Dict[str, Any], event_type: str) -> Event:
            return Event(
                event_type=event_type,
                entity_id=listing.get("ListingKey", ""),
                event_timestamp=listing.get("ModificationTimestamp", ""),
                raw_data=listing,
            )

        for event_type, filters in event_filters.items():
            filtered_listings = self._filter_results(all_recent_listings, minutes_ago, **filters)
            if filtered_listings:
                for listing in filtered_listings:
                    all_events.append(_create_event(listing, event_type))
        
        logger.info(f"FlexmlsResoApi: Transformed raw API data into {len(all_events)} standard Event objects.")
        return all_events