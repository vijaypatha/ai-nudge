# FILE: backend/integrations/mls/factory.py
import os
import logging
from typing import Optional

from backend.integrations.mls.base import MlsApiInterface
from backend.integrations.mls.flexmls_spark_api import FlexmlsSparkApi

logger = logging.getLogger(__name__)

PROVIDER_MAP = {
    "flexmls_spark": FlexmlsSparkApi,
}

def get_mls_client() -> Optional[MlsApiInterface]:
    provider_name = os.getenv("MLS_PROVIDER")
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