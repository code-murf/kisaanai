"""
Core module for the Agri-Analytics platform.

This module provides:
- Security utilities (JWT, password hashing)
- Configuration management
- Caching layer
- Rate limiting
"""
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    verify_token,
    generate_otp,
)
from app.core.cache import (
    RedisClient,
    CacheService,
    SessionStorage,
    RateLimiter,
    cached,
    get_redis,
    close_redis,
    cache_get,
    cache_set,
    cache_delete,
)
from app.core.rate_limit import (
    RateLimitMiddleware,
    RateLimitRule,
    RateLimitScope,
    rate_limit,
    setup_rate_limiting,
    InMemoryRateLimiter,
)

__all__ = [
    # Security
    "verify_password",
    "get_password_hash",
    "create_access_token",
    "create_refresh_token",
    "verify_token",
    "generate_otp",
    # Cache
    "RedisClient",
    "CacheService",
    "SessionStorage",
    "RateLimiter",
    "cached",
    "get_redis",
    "close_redis",
    "cache_get",
    "cache_set",
    "cache_delete",
    # Rate Limiting
    "RateLimitMiddleware",
    "RateLimitRule",
    "RateLimitScope",
    "rate_limit",
    "setup_rate_limiting",
    "InMemoryRateLimiter",
]
