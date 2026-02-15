"""
Redis caching layer for the Agri-Analytics platform.

This module provides:
- Async Redis client wrapper
- Caching decorators for functions
- Cache invalidation utilities
- Session storage for WhatsApp bot
"""
import asyncio
import functools
import hashlib
import json
import logging
import pickle
from datetime import timedelta
from typing import Any, Callable, Optional, TypeVar, Union, List, Dict

import redis.asyncio as redis
from redis.asyncio.connection import ConnectionPool
from redis.exceptions import RedisError

from app.config import settings


logger = logging.getLogger(__name__)


T = TypeVar("T")


# ============================================================================
# REDIS CLIENT
# ============================================================================

class RedisClient:
    """
    Async Redis client wrapper with connection pooling.
    
    Provides high-level caching operations with automatic serialization.
    """
    
    def __init__(
        self,
        url: Optional[str] = None,
        max_connections: int = 10,
        decode_responses: bool = False,
    ):
        """
        Initialize Redis client.
        
        Args:
            url: Redis connection URL
            max_connections: Maximum connections in pool
            decode_responses: Whether to decode responses to strings
        """
        self.url = url or settings.REDIS_URL
        self.max_connections = max_connections
        self.decode_responses = decode_responses
        self._pool: Optional[ConnectionPool] = None
        self._client: Optional[redis.Redis] = None
    
    async def connect(self) -> None:
        """Establish connection to Redis."""
        if self._client is None:
            self._pool = ConnectionPool.from_url(
                self.url,
                max_connections=self.max_connections,
                decode_responses=self.decode_responses,
            )
            self._client = redis.Redis(connection_pool=self._pool)
            logger.info("Connected to Redis")
    
    async def disconnect(self) -> None:
        """Close Redis connection."""
        if self._client:
            await self._client.close()
            self._client = None
        if self._pool:
            await self._pool.disconnect()
            self._pool = None
            logger.info("Disconnected from Redis")
    
    @property
    def client(self) -> redis.Redis:
        """Get Redis client instance."""
        if self._client is None:
            raise RuntimeError("Redis client not connected. Call connect() first.")
        return self._client
    
    async def get(self, key: str) -> Optional[bytes]:
        """
        Get value from Redis.
        
        Args:
            key: Cache key
        
        Returns:
            Cached value or None
        """
        try:
            return await self.client.get(key)
        except RedisError as e:
            logger.warning(f"Redis get error: {e}")
            return None
    
    async def set(
        self,
        key: str,
        value: Union[bytes, str],
        ttl: Optional[int] = None,
    ) -> bool:
        """
        Set value in Redis.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds
        
        Returns:
            True if successful
        """
        try:
            if ttl:
                await self.client.setex(key, ttl, value)
            else:
                await self.client.set(key, value)
            return True
        except RedisError as e:
            logger.warning(f"Redis set error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """
        Delete key from Redis.
        
        Args:
            key: Cache key
        
        Returns:
            True if key was deleted
        """
        try:
            result = await self.client.delete(key)
            return result > 0
        except RedisError as e:
            logger.warning(f"Redis delete error: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """
        Check if key exists in Redis.
        
        Args:
            key: Cache key
        
        Returns:
            True if key exists
        """
        try:
            return await self.client.exists(key) > 0
        except RedisError as e:
            logger.warning(f"Redis exists error: {e}")
            return False
    
    async def expire(self, key: str, ttl: int) -> bool:
        """
        Set TTL on a key.
        
        Args:
            key: Cache key
            ttl: Time-to-live in seconds
        
        Returns:
            True if successful
        """
        try:
            return await self.client.expire(key, ttl)
        except RedisError as e:
            logger.warning(f"Redis expire error: {e}")
            return False
    
    async def ttl(self, key: str) -> int:
        """
        Get TTL of a key.
        
        Args:
            key: Cache key
        
        Returns:
            TTL in seconds, -1 if no TTL, -2 if key doesn't exist
        """
        try:
            return await self.client.ttl(key)
        except RedisError as e:
            logger.warning(f"Redis TTL error: {e}")
            return -2
    
    async def incr(self, key: str) -> int:
        """
        Increment a counter.
        
        Args:
            key: Counter key
        
        Returns:
            New value
        """
        try:
            return await self.client.incr(key)
        except RedisError as e:
            logger.warning(f"Redis incr error: {e}")
            return 0
    
    async def incrby(self, key: str, amount: int) -> int:
        """
        Increment counter by amount.
        
        Args:
            key: Counter key
            amount: Amount to increment
        
        Returns:
            New value
        """
        try:
            return await self.client.incrby(key, amount)
        except RedisError as e:
            logger.warning(f"Redis incrby error: {e}")
            return 0
    
    async def keys(self, pattern: str) -> List[str]:
        """
        Get keys matching pattern.
        
        Args:
            pattern: Key pattern
        
        Returns:
            List of matching keys
        """
        try:
            return await self.client.keys(pattern)
        except RedisError as e:
            logger.warning(f"Redis keys error: {e}")
            return []
    
    async def flush_db(self) -> bool:
        """
        Clear all keys in current database.
        
        Returns:
            True if successful
        """
        try:
            await self.client.flushdb()
            return True
        except RedisError as e:
            logger.warning(f"Redis flush error: {e}")
            return False
    
    # Hash operations
    async def hget(self, name: str, key: str) -> Optional[bytes]:
        """Get hash field value."""
        try:
            return await self.client.hget(name, key)
        except RedisError as e:
            logger.warning(f"Redis hget error: {e}")
            return None
    
    async def hset(
        self,
        name: str,
        key: str,
        value: Union[bytes, str],
    ) -> bool:
        """Set hash field value."""
        try:
            await self.client.hset(name, key, value)
            return True
        except RedisError as e:
            logger.warning(f"Redis hset error: {e}")
            return False
    
    async def hgetall(self, name: str) -> Dict[bytes, bytes]:
        """Get all hash fields."""
        try:
            return await self.client.hgetall(name)
        except RedisError as e:
            logger.warning(f"Redis hgetall error: {e}")
            return {}
    
    async def hdel(self, name: str, key: str) -> bool:
        """Delete hash field."""
        try:
            return await self.client.hdel(name, key) > 0
        except RedisError as e:
            logger.warning(f"Redis hdel error: {e}")
            return False


# Global Redis client instance
_redis_client: Optional[RedisClient] = None


async def get_redis() -> RedisClient:
    """
    Get or create Redis client.
    
    Returns:
        RedisClient instance
    """
    global _redis_client
    if _redis_client is None:
        _redis_client = RedisClient()
        await _redis_client.connect()
    return _redis_client


async def close_redis() -> None:
    """Close Redis connection."""
    global _redis_client
    if _redis_client:
        await _redis_client.disconnect()
        _redis_client = None


# ============================================================================
# CACHE SERVICE
# ============================================================================

class CacheService:
    """
    High-level caching service with serialization support.
    """
    
    def __init__(self, redis_client: Optional[RedisClient] = None):
        """
        Initialize cache service.
        
        Args:
            redis_client: Redis client instance
        """
        self._redis = redis_client
        self._prefix = "agri:"
    
    async def _get_redis(self) -> RedisClient:
        """Get Redis client."""
        if self._redis is None:
            self._redis = await get_redis()
        return self._redis
    
    def _make_key(self, key: str) -> str:
        """Create prefixed cache key."""
        return f"{self._prefix}{key}"
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get cached value with automatic deserialization.
        
        Args:
            key: Cache key
        
        Returns:
            Cached value or None
        """
        redis = await self._get_redis()
        full_key = self._make_key(key)
        
        data = await redis.get(full_key)
        if data is None:
            return None
        
        try:
            return pickle.loads(data)
        except (pickle.PickleError, TypeError):
            # Try JSON decode
            try:
                return json.loads(data.decode())
            except (json.JSONDecodeError, UnicodeDecodeError):
                return data
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[Union[int, timedelta]] = None,
    ) -> bool:
        """
        Set cached value with automatic serialization.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live (seconds or timedelta)
        
        Returns:
            True if successful
        """
        redis = await self._get_redis()
        full_key = self._make_key(key)
        
        # Serialize value
        try:
            if isinstance(value, (dict, list, str, int, float, bool)):
                data = json.dumps(value).encode()
            else:
                data = pickle.dumps(value)
        except (pickle.PickleError, TypeError) as e:
            logger.warning(f"Cache serialization error: {e}")
            return False
        
        # Convert timedelta to seconds
        if isinstance(ttl, timedelta):
            ttl = int(ttl.total_seconds())
        
        return await redis.set(full_key, data, ttl)
    
    async def delete(self, key: str) -> bool:
        """
        Delete cached value.
        
        Args:
            key: Cache key
        
        Returns:
            True if key was deleted
        """
        redis = await self._get_redis()
        full_key = self._make_key(key)
        return await redis.delete(full_key)
    
    async def exists(self, key: str) -> bool:
        """
        Check if key exists.
        
        Args:
            key: Cache key
        
        Returns:
            True if key exists
        """
        redis = await self._get_redis()
        full_key = self._make_key(key)
        return await redis.exists(full_key)
    
    async def get_or_set(
        self,
        key: str,
        factory: Callable[[], T],
        ttl: Optional[Union[int, timedelta]] = None,
    ) -> T:
        """
        Get cached value or compute and cache it.
        
        Args:
            key: Cache key
            factory: Function to compute value if not cached
            ttl: Time-to-live
        
        Returns:
            Cached or computed value
        """
        value = await self.get(key)
        if value is not None:
            return value
        
        # Compute value
        if asyncio.iscoroutinefunction(factory):
            value = await factory()
        else:
            value = factory()
        
        # Cache value
        await self.set(key, value, ttl)
        
        return value
    
    async def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all keys matching pattern.
        
        Args:
            pattern: Key pattern (e.g., "prices:*")
        
        Returns:
            Number of keys deleted
        """
        redis = await self._get_redis()
        full_pattern = self._make_key(pattern)
        
        keys = await redis.keys(full_pattern)
        if not keys:
            return 0
        
        deleted = 0
        for key in keys:
            if await redis.delete(key):
                deleted += 1
        
        return deleted
    
    async def increment(self, key: str, amount: int = 1) -> int:
        """
        Increment a counter.
        
        Args:
            key: Counter key
            amount: Amount to increment
        
        Returns:
            New value
        """
        redis = await self._get_redis()
        full_key = self._make_key(key)
        return await redis.incrby(full_key, amount)


# ============================================================================
# CACHING DECORATOR
# ============================================================================

def cached(
    key: Optional[str] = None,
    key_builder: Optional[Callable[..., str]] = None,
    ttl: Optional[Union[int, timedelta]] = None,
    skip_cache: Optional[Callable[..., bool]] = None,
):
    """
    Decorator to cache function results.
    
    Args:
        key: Static cache key
        key_builder: Function to build cache key from arguments
        ttl: Time-to-live
        skip_cache: Function to determine if caching should be skipped
    
    Returns:
        Decorated function
    
    Example:
        @cached(key_builder=lambda commodity, mandi: f"price:{commodity}:{mandi}", ttl=300)
        async def get_price(commodity: str, mandi: str) -> float:
            ...
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            # Build cache key
            if key:
                cache_key = key
            elif key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                # Default key from function name and arguments
                arg_hash = hashlib.md5(
                    pickle.dumps((args, sorted(kwargs.items())))
                ).hexdigest()[:16]
                cache_key = f"{func.__name__}:{arg_hash}"
            
            # Check skip condition
            if skip_cache and skip_cache(*args, **kwargs):
                return await func(*args, **kwargs)
            
            # Try to get from cache
            cache = CacheService()
            cached_value = await cache.get(cache_key)
            
            if cached_value is not None:
                logger.debug(f"Cache hit: {cache_key}")
                return cached_value
            
            # Compute value
            logger.debug(f"Cache miss: {cache_key}")
            result = await func(*args, **kwargs)
            
            # Cache result
            if result is not None:
                await cache.set(cache_key, result, ttl)
            
            return result
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            # For sync functions, just execute without caching
            # (could be enhanced with sync Redis client)
            return func(*args, **kwargs)
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


# ============================================================================
# SESSION STORAGE
# ============================================================================

class SessionStorage:
    """
    Session storage using Redis for WhatsApp bot and user sessions.
    """
    
    def __init__(
        self,
        redis_client: Optional[RedisClient] = None,
        prefix: str = "session:",
        default_ttl: int = 86400,  # 24 hours
    ):
        """
        Initialize session storage.
        
        Args:
            redis_client: Redis client instance
            prefix: Key prefix for sessions
            default_ttl: Default session TTL in seconds
        """
        self._redis = redis_client
        self._prefix = prefix
        self._default_ttl = default_ttl
    
    async def _get_redis(self) -> RedisClient:
        """Get Redis client."""
        if self._redis is None:
            self._redis = await get_redis()
        return self._redis
    
    def _make_key(self, session_id: str) -> str:
        """Create session key."""
        return f"{self._prefix}{session_id}"
    
    async def get(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session data.
        
        Args:
            session_id: Session identifier
        
        Returns:
            Session data or None
        """
        redis = await self._get_redis()
        key = self._make_key(session_id)
        
        data = await redis.hgetall(key)
        if not data:
            return None
        
        # Decode session data
        session = {}
        for k, v in data.items():
            try:
                key_str = k.decode() if isinstance(k, bytes) else k
                value_str = v.decode() if isinstance(v, bytes) else v
                session[key_str] = json.loads(value_str)
            except (json.JSONDecodeError, UnicodeDecodeError):
                session[key_str] = value_str
        
        return session
    
    async def set(
        self,
        session_id: str,
        data: Dict[str, Any],
        ttl: Optional[int] = None,
    ) -> bool:
        """
        Set session data.
        
        Args:
            session_id: Session identifier
            data: Session data
            ttl: Time-to-live in seconds
        
        Returns:
            True if successful
        """
        redis = await self._get_redis()
        key = self._make_key(session_id)
        
        # Clear existing data
        await redis.delete(key)
        
        # Set new data
        for field, value in data.items():
            value_str = json.dumps(value) if not isinstance(value, str) else value
            await redis.hset(key, field, value_str)
        
        # Set TTL
        ttl = ttl or self._default_ttl
        await redis.expire(key, ttl)
        
        return True
    
    async def update(
        self,
        session_id: str,
        data: Dict[str, Any],
    ) -> bool:
        """
        Update session data (merge with existing).
        
        Args:
            session_id: Session identifier
            data: Data to update
        
        Returns:
            True if successful
        """
        redis = await self._get_redis()
        key = self._make_key(session_id)
        
        for field, value in data.items():
            value_str = json.dumps(value) if not isinstance(value, str) else value
            await redis.hset(key, field, value_str)
        
        return True
    
    async def delete(self, session_id: str) -> bool:
        """
        Delete session.
        
        Args:
            session_id: Session identifier
        
        Returns:
            True if session was deleted
        """
        redis = await self._get_redis()
        key = self._make_key(session_id)
        return await redis.delete(key)
    
    async def exists(self, session_id: str) -> bool:
        """
        Check if session exists.
        
        Args:
            session_id: Session identifier
        
        Returns:
            True if session exists
        """
        redis = await self._get_redis()
        key = self._make_key(session_id)
        return await redis.exists(key)
    
    async def refresh_ttl(
        self,
        session_id: str,
        ttl: Optional[int] = None,
    ) -> bool:
        """
        Refresh session TTL.
        
        Args:
            session_id: Session identifier
            ttl: New TTL in seconds
        
        Returns:
            True if successful
        """
        redis = await self._get_redis()
        key = self._make_key(session_id)
        ttl = ttl or self._default_ttl
        return await redis.expire(key, ttl)


# ============================================================================
# RATE LIMITER
# ============================================================================

class RateLimiter:
    """
    Redis-based rate limiter using sliding window algorithm.
    """
    
    def __init__(
        self,
        redis_client: Optional[RedisClient] = None,
        prefix: str = "ratelimit:",
    ):
        """
        Initialize rate limiter.
        
        Args:
            redis_client: Redis client instance
            prefix: Key prefix
        """
        self._redis = redis_client
        self._prefix = prefix
    
    async def _get_redis(self) -> RedisClient:
        """Get Redis client."""
        if self._redis is None:
            self._redis = await get_redis()
        return self._redis
    
    def _make_key(self, identifier: str, action: str) -> str:
        """Create rate limit key."""
        return f"{self._prefix}{action}:{identifier}"
    
    async def is_allowed(
        self,
        identifier: str,
        action: str,
        max_requests: int,
        window_seconds: int,
    ) -> bool:
        """
        Check if request is allowed within rate limit.
        
        Args:
            identifier: Unique identifier (e.g., user ID, IP)
            action: Action being rate limited
            max_requests: Maximum requests allowed
            window_seconds: Time window in seconds
        
        Returns:
            True if request is allowed
        """
        redis = await self._get_redis()
        key = self._make_key(identifier, action)
        
        # Get current count
        current = await redis.get(key)
        
        if current is None:
            # First request, set counter
            await redis.set(key, b"1", ttl=window_seconds)
            return True
        
        count = int(current)
        if count >= max_requests:
            return False
        
        # Increment counter
        await redis.incr(key)
        return True
    
    async def get_remaining(
        self,
        identifier: str,
        action: str,
        max_requests: int,
    ) -> int:
        """
        Get remaining requests allowed.
        
        Args:
            identifier: Unique identifier
            action: Action being rate limited
            max_requests: Maximum requests allowed
        
        Returns:
            Number of remaining requests
        """
        redis = await self._get_redis()
        key = self._make_key(identifier, action)
        
        current = await redis.get(key)
        if current is None:
            return max_requests
        
        count = int(current)
        return max(0, max_requests - count)
    
    async def reset(self, identifier: str, action: str) -> bool:
        """
        Reset rate limit counter.
        
        Args:
            identifier: Unique identifier
            action: Action being rate limited
        
        Returns:
            True if counter was reset
        """
        redis = await self._get_redis()
        key = self._make_key(identifier, action)
        return await redis.delete(key)


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

async def cache_get(key: str) -> Optional[Any]:
    """Get value from cache."""
    cache = CacheService()
    return await cache.get(key)


async def cache_set(
    key: str,
    value: Any,
    ttl: Optional[Union[int, timedelta]] = None,
) -> bool:
    """Set value in cache."""
    cache = CacheService()
    return await cache.set(key, value, ttl)


async def cache_delete(key: str) -> bool:
    """Delete value from cache."""
    cache = CacheService()
    return await cache.delete(key)
