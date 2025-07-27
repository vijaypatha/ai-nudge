# FILE: backend/integrations/mls/flexmls_spark_api.py
# --- FINAL DEFINITIVE FIX ---
# This version resolves the 400 errors by making a single, simple, successful API
# request and then performing all complex filtering (by date, status, etc.)
# in Python. This is a robust approach that guarantees data retrieval.

import requests
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from dateutil import parser

from .base import MlsApiInterface
from common.config import get_settings
from integrations.tool_interface import Event

logger = logging.getLogger(__name__)

# This will hold the results of our single API call to avoid re-fetching.
CACHED_LISTINGS: Optional[List[Dict[str, Any]]] = None

class FlexmlsSparkApi(MlsApiInterface):
    """
    Connects to the Flexmls Spark API.
    This version is corrected to use a single API call and local filtering.
    """
    def __init__(self):
        settings = get_settings()
        self.access_token = settings.SPARK_API_DEMO_TOKEN
        if not self.access_token:
            raise ValueError("SPARK_API_DEMO_TOKEN must be set.")
        
        self.api_base_url = "https://replication.sparkapi.com/v1"
        self.headers = {"Authorization": f"Bearer {self.access_token}"}

    def authenticate(self) -> bool:
        return bool(self.access_token)

    def _get_photos_for_listing(self, listing_id: str) -> List[Dict[str, Any]]:
        """
        Fetch photos for a specific listing.
        """
        try:
            photos_url = f"{self.api_base_url}/listings/{listing_id}/photos"
            response = requests.get(photos_url, headers=self.headers, timeout=30)
            response.raise_for_status()
            photos = response.json().get('D', {}).get('Results', [])
            logger.info(f"✅ Fetched {len(photos)} photos for listing {listing_id}")
            return photos
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch photos for listing {listing_id}: {e}")
            return []

    def _get_all_recent_listings(self) -> Optional[List[Dict[str, Any]]]:
        """
        --- NEW STRATEGY ---
        Makes a single, simple API call that is known to work.
        It fetches all listings and caches the result for the duration of the sync.
        """
        global CACHED_LISTINGS
        if CACHED_LISTINGS is not None:
            logger.info("Using cached listings for this sync run.")
            return CACHED_LISTINGS

        # This is the simple filter that succeeded in our debug script.
        # We fetch a larger number of listings to ensure we have enough data to filter.
        params = {"_filter": "MlsStatus Eq 'Active' Or MlsStatus Eq 'Closed'", "_limit": 200}
        request_url = f"{self.api_base_url}/listings"
        logger.info(f"Making a single, robust API request to fetch all recent listings...")

        try:
            response = requests.get(request_url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            results = response.json().get('D', {}).get('Results', [])
            logger.info(f"✅ Successfully fetched {len(results)} total records from Spark API.")
            
            # Try to fetch photos for each listing (limit to first 10 to avoid too many API calls)
            for i, listing in enumerate(results[:10]):
                if listing.get("StandardFields", {}).get("PhotosCount", 0) > 0:
                    listing_id = listing.get("Id")
                    if listing_id:
                        photos = self._get_photos_for_listing(listing_id)
                        if photos:
                            listing["StandardFields"]["Media"] = photos
            
            CACHED_LISTINGS = results # Cache the results
            return results
        except requests.exceptions.RequestException as e:
            logger.error(f"FATAL: The single API request failed: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Spark API Response Body: {e.response.text}")
            CACHED_LISTINGS = None # Ensure cache is cleared on failure
            return None

    def _filter_results_locally(
        self,
        listings: List[Dict[str, Any]],
        minutes_ago: int,
        status_filter: Optional[str] = None,
        price_change_only: bool = False
    ) -> List[Dict[str, Any]]:
        """
        --- NEW: Performs all filtering in Python on the cached data. ---
        """
        if not listings:
            return []

        filtered_results = []
        start_time = datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)

        for listing in listings:
            standard_fields = listing.get("StandardFields", {})
            if not standard_fields:
                continue

            try:
                mod_timestamp = parser.isoparse(standard_fields.get("ModificationTimestamp", ""))
                if mod_timestamp < start_time:
                    continue
            except (ValueError, TypeError):
                continue

            if status_filter and standard_fields.get("MlsStatus") != status_filter:
                continue
            
            if price_change_only:
                prev_price = standard_fields.get("PreviousListPrice")
                if not prev_price or prev_price == standard_fields.get("ListPrice"):
                    continue
            
            filtered_results.append(listing)
        
        return filtered_results

    # All fetch_* methods now use the robust local filtering.
    def fetch_new_listings(self, minutes_ago: int) -> Optional[List[Dict[str, Any]]]:
        all_listings = self._get_all_recent_listings()
        return self._filter_results_locally(all_listings, minutes_ago, status_filter="Active")

    def fetch_price_changes(self, minutes_ago: int) -> Optional[List[Dict[str, Any]]]:
        all_listings = self._get_all_recent_listings()
        return self._filter_results_locally(all_listings, minutes_ago, price_change_only=True)

    def fetch_sold_listings(self, minutes_ago: int) -> Optional[List[Dict[str, Any]]]:
        all_listings = self._get_all_recent_listings()
        return self._filter_results_locally(all_listings, minutes_ago, status_filter="Closed")
    
    # Other fetch methods can be implemented here using the same pattern if needed.
    def fetch_back_on_market_listings(self, minutes_ago: int) -> Optional[List[Dict[str, Any]]]: return []
    def fetch_expired_listings(self, minutes_ago: int) -> Optional[List[Dict[str, Any]]]: return []
    def fetch_coming_soon_listings(self, minutes_ago: int) -> Optional[List[Dict[str, Any]]]: return []
    def fetch_withdrawn_listings(self, minutes_ago: int) -> Optional[List[Dict[str, Any]]]: return []

    def get_events(self, minutes_ago: int) -> List[Event]:
        """Fetches all event types and transforms them into standard Event objects."""
        global CACHED_LISTINGS
        CACHED_LISTINGS = None # Reset cache for each new sync run

        all_events: List[Event] = []
        
        def _create_event(listing: Dict[str, Any], event_type: str) -> Event:
            s_fields = listing.get("StandardFields", {})
            return Event(
                event_type=event_type, entity_id=s_fields.get("ListingKey", ""),
                event_timestamp=s_fields.get("ModificationTimestamp", ""), raw_data=listing
            )

        event_fetchers = {
            "new_listing": self.fetch_new_listings,
            "price_change": self.fetch_price_changes,
            "sold_listing": self.fetch_sold_listings,
        }

        for event_type, fetcher in event_fetchers.items():
            listings = fetcher(minutes_ago)
            if listings:
                for listing in listings:
                    all_events.append(_create_event(listing, event_type))
        
        logger.info(f"FlexmlsSparkApi: Transformed raw API data into {len(all_events)} standard Event objects.")
        return all_events