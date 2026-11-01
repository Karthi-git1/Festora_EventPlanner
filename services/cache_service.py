"""Caching service for event data and AI responses.

This module provides intelligent caching with:
- Event data caching (15-minute TTL)
- AI copilot response caching (1-hour TTL)
- Automatic cache invalidation
- Cache statistics tracking

Requirements: 9.1, 9.2, 9.3, 9.4, 9.6
"""

import json
import hashlib
import logging
from typing import Optional, Dict, Any, List
from datetime import timedelta

logger = logging.getLogger(__name__)


class CacheService:
    """Intelligent caching service with Redis backend."""
    
    # Cache TTLs in seconds
    EVENT_TTL = 900  # 15 minutes (Requirement 9.1)
    AI_RESPONSE_TTL = 3600  # 1 hour (Requirement 9.3)
    
    def __init__(self, redis_service):
        """Initialize cache service with Redis backend.
        
        Args:
            redis_service: RedisService instance
        """
        self.redis = redis_service
        self.stats = {
            'hits': 0,
            'misses': 0,
            'total_requests': 0
        }
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value (parsed from JSON) or None
        """
        self.stats['total_requests'] += 1
        
        if not self.redis or not self.redis.connected:
            self.stats['misses'] += 1
            return None
        
        try:
            value = self.redis.get(key)
            if value:
                self.stats['hits'] += 1
                return json.loads(value)
            else:
                self.stats['misses'] += 1
                return None
        except Exception as e:
            logger.error(f"Cache GET error: {e}")
            self.stats['misses'] += 1
            return None
    
    def set(self, key: str, value: Any, ttl: int) -> bool:
        """Set value in cache with TTL.
        
        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time to live in seconds
            
        Returns:
            True if successful
        """
        if not self.redis or not self.redis.connected:
            return False
        
        try:
            json_value = json.dumps(value)
            return self.redis.set(key, json_value, ttl)
        except Exception as e:
            logger.error(f"Cache SET error: {e}")
            return False
    
    def invalidate(self, pattern: str) -> int:
        """Invalidate cache entries matching pattern.
        
        Args:
            pattern: Redis key pattern (e.g., "event:123:*")
            
        Returns:
            Number of keys invalidated
            
        Requirement: 9.2 (Automatic cache invalidation on updates)
        """
        if not self.redis or not self.redis.connected:
            return 0
        
        try:
            count = self.redis.invalidate_pattern(pattern)
            logger.info(f"Invalidated {count} cache entries matching '{pattern}'")
            return count
        except Exception as e:
            logger.error(f"Cache invalidation error: {e}")
            return 0
    
    def cache_event_data(self, event_id: str, event_data: Dict[str, Any]) -> bool:
        """Cache event data with 15-minute TTL.
        
        Args:
            event_id: Event identifier
            event_data: Event data to cache
            
        Returns:
            True if cached successfully
            
        Requirement: 9.1 (Cache event data with 15-minute TTL)
        """
        key = f"event:{event_id}"
        return self.set(key, event_data, self.EVENT_TTL)
    
    def get_event_data(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Get cached event data.
        
        Args:
            event_id: Event identifier
            
        Returns:
            Cached event data or None
        """
        key = f"event:{event_id}"
        return self.get(key)
    
    def invalidate_event(self, event_id: str) -> int:
        """Invalidate all cache entries for an event.
        
        Args:
            event_id: Event identifier
            
        Returns:
            Number of keys invalidated
            
        Requirement: 9.2 (Invalidate cache on event updates)
        """
        pattern = f"event:{event_id}*"
        return self.invalidate(pattern)
    
    def cache_ai_response(self, query: str, response: str, event_id: Optional[str] = None) -> bool:
        """Cache AI copilot response with 1-hour TTL.
        
        Args:
            query: User query text
            response: AI response text
            event_id: Optional event context
            
        Returns:
            True if cached successfully
            
        Requirement: 9.3 (Cache AI responses for 1 hour)
        """
        # Create cache key from query hash
        query_hash = hashlib.md5(query.encode()).hexdigest()
        key = f"ai:{event_id}:{query_hash}" if event_id else f"ai:global:{query_hash}"
        
        cache_data = {
            'query': query,
            'response': response,
            'event_id': event_id
        }
        
        return self.set(key, cache_data, self.AI_RESPONSE_TTL)
    
    def get_ai_response(self, query: str, event_id: Optional[str] = None) -> Optional[str]:
        """Get cached AI response.
        
        Args:
            query: User query text
            event_id: Optional event context
            
        Returns:
            Cached AI response or None
        """
        query_hash = hashlib.md5(query.encode()).hexdigest()
        key = f"ai:{event_id}:{query_hash}" if event_id else f"ai:global:{query_hash}"
        
        cache_data = self.get(key)
        if cache_data:
            return cache_data.get('response')
        return None
    
    def warm_cache(self, event_ids: List[str], fetch_function) -> int:
        """Pre-populate cache with active event data.
        
        Args:
            event_ids: List of event IDs to warm
            fetch_function: Function to fetch event data (event_id) -> event_data
            
        Returns:
            Number of events cached
            
        Requirement: 9.4 (Cache warming on application startup)
        """
        if not self.redis or not self.redis.connected:
            logger.warning("Cannot warm cache: Redis not connected")
            return 0
        
        cached_count = 0
        for event_id in event_ids:
            try:
                event_data = fetch_function(event_id)
                if event_data:
                    if self.cache_event_data(event_id, event_data):
                        cached_count += 1
            except Exception as e:
                logger.error(f"Error warming cache for event {event_id}: {e}")
        
        logger.info(f"Cache warmed with {cached_count} events")
        return cached_count
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics including hit rate.
        
        Returns:
            Dictionary with hit_rate, hits, misses, total_requests
            
        Requirement: 9.6 (Monitor cache hit rates)
        """
        hit_rate = 0.0
        if self.stats['total_requests'] > 0:
            hit_rate = (self.stats['hits'] / self.stats['total_requests']) * 100
        
        return {
            'hit_rate': round(hit_rate, 2),
            'hits': self.stats['hits'],
            'misses': self.stats['misses'],
            'total_requests': self.stats['total_requests'],
            'connected': self.redis.connected if self.redis else False
        }
    
    def reset_stats(self) -> None:
        """Reset cache statistics."""
        self.stats = {
            'hits': 0,
            'misses': 0,
            'total_requests': 0
        }


# Global cache service instance
_cache_service: Optional[CacheService] = None


def init_cache_service(redis_service) -> CacheService:
    """Initialize global cache service.
    
    Args:
        redis_service: RedisService instance
        
    Returns:
        CacheService instance
    """
    global _cache_service
    _cache_service = CacheService(redis_service)
    return _cache_service


def get_cache_service() -> Optional[CacheService]:
    """Get global cache service instance."""
    return _cache_service
