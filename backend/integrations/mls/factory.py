# backend/integrations/mls/factory.py
# This file contains the factory function for creating the correct MLS client.

import logging
from typing import Optional

from data.models.user import User
from common.config import get_settings
from .base import MlsApiInterface
from .flexmls_reso_api import FlexmlsResoApi
from .flexmls_spark_api import FlexmlsSparkApi

# Configure logging
logger = logging.getLogger(__name__)

# A mapping from the provider name in settings to the actual class.
PROVIDER_MAP = {
    "flexmls_reso": FlexmlsResoApi,
    "flexmls_spark": FlexmlsSparkApi,
}

def get_mls_client(user: User) -> Optional[MlsApiInterface]:
    """
    Factory function that inspects the user's configuration and returns an
    instance of the appropriate MLS API client.

    Args:
        user: The user for whom to get the MLS client.

    Returns:
        An instance of a class that implements MlsApiInterface, or None if
        the provider is not configured or supported.
    """
    settings = get_settings()
    provider_name = user.tool_provider or settings.MLS_PROVIDER
    
    if not provider_name:
        logger.warning(f"No MLS provider configured for user {user.id} or in global settings.")
        return None

    logger.info(f"Attempting to get MLS client for provider: '{provider_name}' for user {user.id}")
    
    client_class = PROVIDER_MAP.get(provider_name.lower())
    
    if not client_class:
        logger.error(f"Unsupported MLS provider specified: {provider_name}")
        return None
        
    try:
        # Create an instance of the appropriate client (e.g., FlexmlsResoApi())
        client_instance = client_class()
        logger.info(f"Successfully instantiated MLS client: {client_class.__name__}")
        return client_instance
    except Exception as e:
        logger.error(f"Failed to instantiate MLS client for provider {provider_name}. Error: {e}", exc_info=True)
        return None