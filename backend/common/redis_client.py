# File Path: backend/common/redis_client.py

import redis
import logging
from functools import lru_cache
from common.config import get_settings

logger = logging.getLogger(__name__)

# Global connection pool - will be initialized on first use
_redis_pool = None

def _get_redis_pool():
    """Get or create the Redis connection pool."""
    global _redis_pool
    if _redis_pool is None:
        try:
            settings = get_settings()
            _redis_pool = redis.ConnectionPool.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                max_connections=20
            )
            logger.info(f"Successfully created Redis connection pool from URL")
        except Exception as e:
            logger.error(f"Could not create Redis connection pool: {e}", exc_info=True)
            raise
    return _redis_pool

@lru_cache()
def get_redis_client():
    """
    Returns a Redis client from the shared connection pool.
    Uses LRU cache to ensure we return the same client instance.
    """
    try:
        pool = _get_redis_pool()
        return redis.Redis(connection_pool=pool)
    except Exception as e:
        logger.error(f"Failed to get Redis client: {e}")
        raise ConnectionError("Redis connection is not available.")