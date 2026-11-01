"""Redis cache configuration and connection management.

This module provides Redis caching for:
- Event data (15-minute TTL)
- AI copilot responses (1-hour TTL)
- Rate limiting counters
- Session storage

Requirements: 6.6, 9.1, 9.2, 9.3, 9.6
"""

import os
import logging
from typing import Optional, Any
import redis
from redis.connection import ConnectionPool

logger = logging.getLogger(__name__)


class RedisService:
    """Redis caching service with connection pooling."""
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        max_connections: int = 50,
        socket_timeout: int = 5,
        socket_connect_timeout: int = 5
    ):
        """Initialize Redis service with connection pooling.
        
        Args:
            redis_url: Redis connection URL
            max_connections: Maximum connections in pool
            socket_timeout: Socket timeout in seconds
            socket_connect_timeout: Connection timeout in seconds
        """
        self.redis_url = redis_url
        self.connected = False
        self.client: Optional[redis.Redis] = None
        
        try:
            # Create connection pool
            self.pool = ConnectionPool.from_url(
                redis_url,
                max_connections=max_connections,
                socket_timeout=socket_timeout,
                socket_connect_timeout=socket_connect_timeout,
                decode_responses=True  # Automatically decode bytes to strings
            )
            
            # Create Redis client
            self.client = redis.Redis(connection_pool=self.pool)
            
            # Test connection
            self.client.ping()
            self.connected = True
            
            logger.info(f"Connected to Redis at {redis_url}")
            
        except redis.ConnectionError as e:
            logger.warning(f"Redis connection failed: {e}. Caching will be disabled.")
            self.connected = False
        except Exception as e:
            logger.error(f"Unexpected error connecting to Redis: {e}")
            self.connected = False
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/error
        """
        if not self.connected or not self.client:
            return None
        
        try:
            return self.client.get(key)
        except redis.RedisError as e:
            logger.error(f"Redis GET error for key '{key}': {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = 900) -> bool:
        """Set value in cache with TTL.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (default: 900 = 15 minutes)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.connected or not self.client:
            return False
        
        try:
            self.client.setex(key, ttl, value)
            return True
        except redis.RedisError as e:
            logger.error(f"Redis SET error for key '{key}': {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache.
        
        Args:
            key: Cache key to delete
            
        Returns:
            True if deleted, False otherwise
        """
        if not self.connected or not self.client:
            return False
        
        try:
            self.client.delete(key)
            return True
        except redis.RedisError as e:
            logger.error(f"Redis DELETE error for key '{key}': {e}")
            return False
    
    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching pattern.
        
        Args:
            pattern: Redis key pattern (e.g., "event:123:*")
            
        Returns:
            Number of keys deleted
        """
        if not self.connected or not self.client:
            return 0
        
        try:
            keys = self.client.keys(pattern)
            if keys:
                return self.client.delete(*keys)
            return 0
        except redis.RedisError as e:
            logger.error(f"Redis pattern invalidation error for '{pattern}': {e}")
            return 0
    
    def close(self) -> None:
        """Close Redis connection."""
        if self.client:
            self.client.close()
            self.connected = False
            logger.info("Redis connection closed")


# Global Redis service instance
_redis_service: Optional[RedisService] = None


def init_redis_service(config) -> RedisService:
    """Initialize global Redis service.
    
    Args:
        config: Configuration object with REDIS_URL
        
    Returns:
        RedisService instance
    """
    global _redis_service
    
    _redis_service = RedisService(
        redis_url=config.REDIS_URL,
        max_connections=getattr(config, 'REDIS_MAX_CONNECTIONS', 50)
    )
    
    return _redis_service


def get_redis_service() -> Optional[RedisService]:
    """Get global Redis service instance."""
    return _redis_service


def close_redis_service() -> None:
    """Close global Redis service."""
    global _redis_service
    if _redis_service:
        _redis_service.close()
        _redis_service = None
