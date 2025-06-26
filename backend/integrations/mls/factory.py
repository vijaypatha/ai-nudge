# ---
# FILE: backend/integrations/mls/factory.py
# PURPOSE: Creates the correct MLS client using the new config pattern.
# ---
import logging
from typing import Optional

from .base import MlsApiInterface
from .flexmls_spark_api import FlexmlsSparkApi
from common.config import get_settings # <-- CHANGED: Import the get_settings function

logger = logging.getLogger(__name__)

PROVIDER_MAP = {
    "flexmls_spark": FlexmlsSparkApi,
}

def get_mls_client() -> Optional[MlsApiInterface]:
    settings = get_settings() # <-- CHANGED: Get settings object
    provider_name = settings.MLS_PROVIDER # <-- CHANGED: Use settings object

    if not provider_name:
        logger.error("MLS_PROVIDER environment variable is not set. Cannot create MLS client.")
        return None
    
    client_class = PROVIDER_MAP.get(provider_name.lower())
    if not client_class:
        logger.error(f"Unknown MLS_PROVIDER '{provider_name}'. Check configuration.")
        return None
    
    logger.info(f"Creating MLS client for provider: {provider_name}")
    try:
        client = client_class()
        return client
    except Exception as e:
        logger.error(f"Failed to initialize MLS client for provider '{provider_name}': {e}")
        return None