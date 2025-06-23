# FILE: backend/integrations/mls/flexmls_spark_api.py
import os
import requests
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional

from backend.integrations.mls.base import MlsApiInterface

logger = logging.getLogger(__name__)

class FlexmlsSparkApi(MlsApiInterface):
    """
    Connects to and fetches data from the FlexMLS Spark RESO Web API.
    This implementation uses a direct bearer token.
    """
    def __init__(self):
        self.access_token = os.getenv("SPARK_API_DEMO_TOKEN")
        if not self.access_token:
            raise ValueError("SPARK_API_DEMO_TOKEN must be set in the environment.")
        self.api_base_url = "https://sparkapi.com/v1/reso"

    def authenticate(self) -> bool:
        if self.access_token:
            logger.info("FlexMLS Spark API is using the provided demo bearer token.")
            return True
        logger.error("Authentication failed: No SPARK_API_DEMO_TOKEN found.")
        return False

    def _make_request(self, endpoint: str, odata_filter: str) -> Optional[List[Dict[str, Any]]]:
        if not self.access_token:
            logger.error("Cannot make request: Authentication token is missing.")
            return None

        headers = {"Authorization": f"Bearer {self.access_token}"}
        select_fields = "ListingId,ListPrice,PreviousListPrice,MlsStatus,UnparsedAddress,ModificationTimestamp,StatusChangeTimestamp"
        request_url = f"{self.api_base_url}/{endpoint}?$filter={odata_filter}&$select={select_fields}"
        logger.info("Making Spark API request to URL: %s", request_url)

        try:
            response = requests.get(request_url, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json().get('value', [])
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching data from Spark API endpoint '{endpoint}': {e}")
            if e.response:
                logger.error(f"Spark API Response Body: {e.response.text}")
            return None

    def fetch_new_listings(self, minutes_ago: int) -> Optional[List[Dict[str, Any]]]:
        filter_time = (datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)).strftime('%Y-%m-%dT%H:%M:%SZ')
        odata_filter = f"ModificationTimestamp ge {filter_time} and MlsStatus eq 'Active'"
        return self._make_request("Property", odata_filter)

    def fetch_price_changes(self, minutes_ago: int) -> Optional[List[Dict[str, Any]]]:
        filter_time = (datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)).strftime('%Y-%m-%dT%H:%M:%SZ')
        odata_filter = f"ModificationTimestamp ge {filter_time} and PreviousListPrice ne null and ListPrice ne PreviousListPrice"
        return self._make_request("Property", odata_filter)