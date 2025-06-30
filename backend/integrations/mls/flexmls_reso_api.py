# ---
# FILE PATH: backend/integrations/mls/flexmls_reso_api.py
# PURPOSE: Connects to the live Flexmls RESO Web API.
# This client uses the live credentials and is adapted for the OData standard.
# ---
import requests
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from dateutil import parser 

from .base import MlsApiInterface
from common.config import get_settings

logger = logging.getLogger(__name__)

class FlexmlsResoApi(MlsApiInterface):
    """
    Connects to the Flexmls RESO Web API (OData) using live credentials.
    """
    def __init__(self):
        settings = get_settings()
        self.access_token = settings.RESO_API_TOKEN
        self.api_base_url = settings.RESO_API_BASE_URL

        if not self.access_token or not self.api_base_url:
            raise ValueError("RESO_API_TOKEN and RESO_API_BASE_URL must be set.")
        
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Accept-Encoding": "gzip, deflate"
        }

    def authenticate(self) -> bool:
        """Verifies that the access token is present."""
        if self.access_token:
            logger.info("FlexmlsResoApi: Authentication successful (API key is present).")
            return True
        logger.error("FlexmlsResoApi: Authentication failed. RESO_API_TOKEN not found.")
        return False

    def _get_listings(self) -> Optional[List[Dict[str, Any]]]:
        """
        Makes a single API call to the RESO API to get recent property listings.
        """
        # OData uses different query parameter syntax ($orderby, $top).
        params = {
            "$orderby": "ModificationTimestamp desc",
            "$top": 100, # Fetching more results to ensure we capture all recent changes
            "$expand": "Media" # Expands to include photos, etc.
        }
        # The resource for listings in the RESO standard is typically 'Property'.
        request_url = f"{self.api_base_url}/Property"
        logger.info(f"Making RESO API request to URL: {request_url} with params: {params}")

        try:
            response = requests.get(request_url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            # RESO OData standard places results in a 'value' array.
            results = response.json().get('value', [])
            logger.info(f"Successfully fetched {len(results)} raw records from RESO API.")
            return results
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching listings from RESO API: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"RESO API Response Body: {e.response.text}")
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
        Performs filtering in Python on the raw results from the RESO API.
        NOTE: Adapted for the RESO Data Dictionary standard field names.
        """
        filtered_results = []
        start_time = datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)
        
        for listing in results:
            # RESO fields are typically at the top level, not nested in "StandardFields".
            try:
                mod_timestamp_str = listing.get("ModificationTimestamp")
                if not mod_timestamp_str: continue
                mod_timestamp = parser.isoparse(mod_timestamp_str)
                if mod_timestamp < start_time:
                    break 
            except (ValueError, TypeError):
                logger.warning(f"Could not parse ModificationTimestamp: {mod_timestamp_str}")
                continue
            
            passes_filters = True
            
            if price_change_only:
                prev_price = listing.get("OriginalListPrice") # RESO may use different fields
                list_price = listing.get("ListPrice")
                if not (prev_price is not None and list_price is not None and prev_price != list_price):
                    passes_filters = False

            # RESO standard often uses 'StandardStatus'
            current_status = listing.get("StandardStatus")
            if status_filter and current_status != status_filter:
                passes_filters = False
            
            # RESO standard may use 'PreviousStandardStatus'
            previous_status = listing.get("PreviousStandardStatus")
            if previous_status_filter and previous_status != previous_status_filter:
                passes_filters = False

            if passes_filters:
                filtered_results.append(listing)
        
        logger.info(f"Python filtering complete. Found {len(filtered_results)} matching listings.")
        return filtered_results

    def fetch_new_listings(self, minutes_ago: int) -> Optional[List[Dict[str, Any]]]:
        """Fetches new, active listings from the RESO API."""
        all_recent_listings = self._get_listings()
        if all_recent_listings is None: return None 
        return self._filter_results(all_recent_listings, minutes_ago, status_filter="Active")

    def fetch_price_changes(self, minutes_ago: int) -> Optional[List[Dict[str, Any]]]:
        """Fetches recent price changes from the RESO API."""
        all_recent_listings = self._get_listings()
        if all_recent_listings is None: return None
        return self._filter_results(all_recent_listings, minutes_ago, price_change_only=True)
    
    def fetch_sold_listings(self, minutes_ago: int) -> Optional[List[Dict[str, Any]]]:
        """Fetches recently 'Closed' listings from the RESO API."""
        all_recent_listings = self._get_listings()
        if all_recent_listings is None: return None
        return self._filter_results(all_recent_listings, minutes_ago, status_filter="Closed")

    def fetch_back_on_market_listings(self, minutes_ago: int) -> Optional[List[Dict[str, Any]]]:
        """Fetches listings that are now 'Active' but were previously 'Pending' from RESO API."""
        all_recent_listings = self._get_listings()
        if all_recent_listings is None: return None
        return self._filter_results(
            all_recent_listings, 
            minutes_ago, 
            status_filter="Active", 
            previous_status_filter="Pending"
        )
    def fetch_expired_listings(self, minutes_ago: int) -> Optional[List[Dict[str, Any]]]:
        """Fetches listings with a status of 'Expired' from RESO API."""
        all_recent_listings = self._get_listings()
        if all_recent_listings is None: return None
        return self._filter_results(all_recent_listings, minutes_ago, status_filter="Expired")

    def fetch_coming_soon_listings(self, minutes_ago: int) -> Optional[List[Dict[str, Any]]]:
        """Fetches listings with a status of 'Coming Soon' from RESO API."""
        all_recent_listings = self._get_listings()
        if all_recent_listings is None: return None
        return self._filter_results(all_recent_listings, minutes_ago, status_filter="Coming Soon")
    
    def fetch_withdrawn_listings(self, minutes_ago: int) -> Optional[List[Dict[str, Any]]]:
        """Fetches listings with a status of 'Withdrawn' from RESO API."""
        all_recent_listings = self._get_listings()
        if all_recent_listings is None: return None
        return self._filter_results(all_recent_listings, minutes_ago, status_filter="Withdrawn")
