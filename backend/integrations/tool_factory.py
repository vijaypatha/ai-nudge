# File Path: backend/integrations/tool_factory.py
# --- NEW FILE ---
# This is the new, generic factory for creating any vertical-specific tool.
# It replaces the old, hardcoded MLS factory.

import logging
from typing import Optional

from data.models.user import User # To access user-specific configuration
from integrations.tool_interface import ToolInterface

# --- Import all possible tool implementations ---
# Real Estate Tools
from integrations.mls.flexmls_spark_api import FlexmlsSparkApi
from integrations.mls.flexmls_reso_api import FlexmlsResoApi

# --- Example of a future tool for a different vertical ---
# from integrations.ehr.theranest_api import TheranestApi # (This is a placeholder)

logger = logging.getLogger(__name__)

# --- 1. Create a map of all known tool providers ---
# This is the central registry for all integrations. To add a new tool,
# you just add its implementation class here.
TOOL_PROVIDER_MAP = {
    # Real Estate
    "flexmls_spark": FlexmlsSparkApi,
    "flexmls_reso": FlexmlsResoApi,

    # Therapy (Example for the future)
    # "theranest": TheranestApi,
}

# --- 2. Create the generic factory function ---
def get_tool_for_user(user: User) -> Optional[ToolInterface]:
    """
    Instantiates and returns the correct external tool for a given user based
    on their configured vertical and tool provider.

    Args:
        user (User): The user object, which should contain their vertical config.

    Returns:
        Optional[ToolInterface]: An instantiated tool object that conforms to the
                                 ToolInterface, or None if configuration is missing or invalid.
    """
    # We assume the user's tool provider is stored in their configuration.
    # This could be in a JSON field on the User model, e.g., user.config['tool_provider']
    # For now, we'll imagine a simple attribute 'tool_provider' on the user model.
    # TODO: Implement a User.config model or similar to store this.
    provider_name = getattr(user, 'tool_provider', None)

    if not provider_name:
        logger.error(f"User {user.id} has no tool_provider configured. Cannot create tool.")
        return None
    
    # Look up the provider name in our map to find the correct class.
    tool_class = TOOL_PROVIDER_MAP.get(provider_name.lower())

    if not tool_class:
        logger.error(f"Unknown tool_provider '{provider_name}' for user {user.id}. Check configuration.")
        return None
    
    logger.info(f"Creating tool '{provider_name}' for user {user.id}")
    try:
        # Instantiate and return the tool client.
        tool_client = tool_class()
        return tool_client
    except Exception as e:
        logger.error(f"Failed to initialize tool '{provider_name}' for user {user.id}: {e}", exc_info=True)
        return None