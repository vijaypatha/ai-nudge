import os
import logging

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO").upper(),
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_env_variable(var_name: str, default: str = None) -> str:
    value = os.getenv(var_name)
    if value is None:
        logger.debug(f"Environment variable '{var_name}' not found, using default value: '{default}'.")
        return default
    return value

def example_utility_function():
    logger.info("Example utility function called.")
    return "Utility function executed successfully."
