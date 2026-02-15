"""
Rate limiting middleware for the Agri-Analytics platform.

This module provides:
- FastAPI middleware for rate limiting
- Decorator-based rate limiting for specific endpoints
- IP-based and user-based rate limiting
"""
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

from fastapi import FastAPI, Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

from app.config import settings
from app.core.cache import RateLimiter, get_redis


logger = logging.getLogger(__name__)


# ============================================================================
# RATE LIMIT CONFIGURATION
# ============================================================================

class RateLimitScope(str, Enum):
    """Rate limit scope types."""
    IP = "ip"
    USER = "user"
    API_KEY = "api_key"
    GLOBAL = "global"


@dataclass
class RateLimitRule:
    """
    Rate limit rule configuration.
    
    Attributes:
        requests: Maximum requests allowed
        window_seconds: Time window in seconds
        scope: Scope for rate limiting (ip, user, api_key)
        block_duration: Duration to block after limit exceeded (seconds)
        exempt_paths: Paths exempt from rate limiting
    """
    requests: int
    window_seconds: int
    scope: RateLimitScope = RateLimitScope.IP
    block_duration: Optional[int] = None
    exempt_paths: List[str] = field(default_factory=list)
    
    @property
    def requests_per_minute(self) -> float:
        """Calculate requests per minute."""
        return self.requests / (self.window_seconds / 60)


# Default rate limit rules
DEFAULT_RULES: Dict[str, RateLimitRule] = {
    "default": RateLimitRule(
        requests=100,
        window_seconds=60,
        scope=RateLimitScope.IP,
    ),
    "auth": RateLimitRule(
        requests=10,
        window_seconds=60,
        scope=RateLimitScope.IP,
        block_duration=300,  # Block for 5 minutes
    ),
    "api": RateLimitRule(
        requests=60,
        window_seconds=60,
        scope=RateLimitScope.USER,
    ),
    "whatsapp": RateLimitRule(
        requests=30,
        window_seconds=60,
        scope=RateLimitScope.IP,
    ),
    "voice": RateLimitRule(
        requests=20,
        window_seconds=60,
        scope=RateLimitScope.IP,
    ),
    "forecast": RateLimitRule(
        requests=30,
        window_seconds=60,
        scope=RateLimitScope.USER,
    ),
}


# ============================================================================
# RATE LIMIT MIDDLEWARE
# ============================================================================

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for rate limiting requests.
    
    Supports:
    - IP-based rate limiting
    - User-based rate limiting
    - Path-specific rules
    - Configurable block duration
    """
    
    def __init__(
        self,
        app: ASGIApp,
        rules: Optional[Dict[str, RateLimitRule]] = None,
        default_rule: str = "default",
        exempt_paths: Optional[List[str]] = None,
    ):
        """
        Initialize rate limit middleware.
        
        Args:
            app: ASGI application
            rules: Dictionary of rate limit rules
            default_rule: Default rule to use
            exempt_paths: Paths exempt from rate limiting
        """
        super().__init__(app)
        self.rules = rules or DEFAULT_RULES
        self.default_rule = default_rule
        self.exempt_paths = exempt_paths or ["/health", "/docs", "/openapi.json"]
        self._rate_limiter: Optional[RateLimiter] = None
    
    async def get_rate_limiter(self) -> RateLimiter:
        """Get or create rate limiter."""
        if self._rate_limiter is None:
            redis = await get_redis()
            self._rate_limiter = RateLimiter(redis)
        return self._rate_limiter
    
    def get_identifier(self, request: Request, scope: RateLimitScope) -> str:
        """
        Get rate limit identifier based on scope.
        
        Args:
            request: FastAPI request
            scope: Rate limit scope
        
        Returns:
            Unique identifier for rate limiting
        """
        if scope == RateLimitScope.IP:
            # Get client IP (handle proxies)
            forwarded = request.headers.get("X-Forwarded-For")
            if forwarded:
                return forwarded.split(",")[0].strip()
            return request.client.host if request.client else "unknown"
        
        elif scope == RateLimitScope.USER:
            # Get user ID from JWT if authenticated
            user_id = getattr(request.state, "user_id", None)
            if user_id:
                return f"user:{user_id}"
            # Fall back to IP
            return self.get_identifier(request, RateLimitScope.IP)
        
        elif scope == RateLimitScope.API_KEY:
            # Get API key from header
            api_key = request.headers.get("X-API-Key")
            if api_key:
                return f"apikey:{api_key}"
            return self.get_identifier(request, RateLimitScope.IP)
        
        elif scope == RateLimitScope.GLOBAL:
            return "global"
        
        return "unknown"
    
    def get_rule_for_path(self, path: str) -> RateLimitRule:
        """
        Get rate limit rule for a path.
        
        Args:
            path: Request path
        
        Returns:
            RateLimitRule to apply
        """
        # Check for specific path rules
        if path.startswith("/api/v1/auth"):
            return self.rules.get("auth", self.rules[self.default_rule])
        elif path.startswith("/webhooks/whatsapp"):
            return self.rules.get("whatsapp", self.rules[self.default_rule])
        elif path.startswith("/webhooks/voice"):
            return self.rules.get("voice", self.rules[self.default_rule])
        elif path.startswith("/api/v1/forecasts"):
            return self.rules.get("forecast", self.rules[self.default_rule])
        elif path.startswith("/api/"):
            return self.rules.get("api", self.rules[self.default_rule])
        
        return self.rules[self.default_rule]
    
    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """
        Process request with rate limiting.
        
        Args:
            request: FastAPI request
            call_next: Next middleware/route handler
        
        Returns:
            Response
        """
        path = request.url.path
        
        # Check exempt paths
        for exempt_path in self.exempt_paths:
            if path.startswith(exempt_path) or path == exempt_path:
                return await call_next(request)
        
        # Get rule for this path
        rule = self.get_rule_for_path(path)
        
        # Get identifier
        identifier = self.get_identifier(request, rule.scope)
        
        # Check rate limit
        rate_limiter = await self.get_rate_limiter()
        action = f"path:{path}"
        
        is_allowed = await rate_limiter.is_allowed(
            identifier=identifier,
            action=action,
            max_requests=rule.requests,
            window_seconds=rule.window_seconds,
        )
        
        # Get remaining requests
        remaining = await rate_limiter.get_remaining(
            identifier=identifier,
            action=action,
            max_requests=rule.requests,
        )
        
        # Add rate limit headers
        headers = {
            "X-RateLimit-Limit": str(rule.requests),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(rule.window_seconds),
        }
        
        if not is_allowed:
            logger.warning(
                f"Rate limit exceeded: identifier={identifier}, path={path}"
            )
            
            # Return 429 Too Many Requests
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Rate limit exceeded. Please try again later.",
                    "retry_after": rule.window_seconds,
                },
                headers={
                    **headers,
                    "Retry-After": str(rule.window_seconds),
                },
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers to response
        for key, value in headers.items():
            response.headers[key] = value
        
        return response


# ============================================================================
# RATE LIMIT DECORATOR
# ============================================================================

def rate_limit(
    requests: int = 60,
    window_seconds: int = 60,
    scope: RateLimitScope = RateLimitScope.IP,
    key_builder: Optional[Callable[[Request], str]] = None,
):
    """
    Decorator for rate limiting specific endpoints.
    
    Args:
        requests: Maximum requests allowed
        window_seconds: Time window in seconds
        scope: Rate limit scope
        key_builder: Custom function to build rate limit key
    
    Example:
        @router.get("/expensive")
        @rate_limit(requests=10, window_seconds=60)
        async def expensive_operation(request: Request):
            ...
    """
    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            # Find request in args/kwargs
            request: Optional[Request] = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if request is None:
                request = kwargs.get("request")
            
            if request is None:
                # No request found, skip rate limiting
                return await func(*args, **kwargs)
            
            # Get rate limiter
            rate_limiter = RateLimiter()
            
            # Build identifier
            if key_builder:
                identifier = key_builder(request)
            else:
                if scope == RateLimitScope.IP:
                    forwarded = request.headers.get("X-Forwarded-For")
                    if forwarded:
                        identifier = forwarded.split(",")[0].strip()
                    else:
                        identifier = request.client.host if request.client else "unknown"
                elif scope == RateLimitScope.USER:
                    user_id = getattr(request.state, "user_id", None)
                    identifier = f"user:{user_id}" if user_id else request.client.host
                else:
                    identifier = "global"
            
            # Check rate limit
            is_allowed = await rate_limiter.is_allowed(
                identifier=identifier,
                action=f"endpoint:{func.__name__}",
                max_requests=requests,
                window_seconds=window_seconds,
            )
            
            if not is_allowed:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded. Please try again later.",
                    headers={"Retry-After": str(window_seconds)},
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator


# ============================================================================
# IN-MEMORY RATE LIMITER (Fallback)
# ============================================================================

class InMemoryRateLimiter:
    """
    In-memory rate limiter for when Redis is not available.
    
    Uses sliding window algorithm with in-memory storage.
    """
    
    def __init__(self):
        """Initialize in-memory rate limiter."""
        self._windows: Dict[str, List[float]] = {}
    
    def is_allowed(
        self,
        identifier: str,
        action: str,
        max_requests: int,
        window_seconds: int,
    ) -> bool:
        """
        Check if request is allowed.
        
        Args:
            identifier: Unique identifier
            action: Action being rate limited
            max_requests: Maximum requests allowed
            window_seconds: Time window in seconds
        
        Returns:
            True if request is allowed
        """
        key = f"{action}:{identifier}"
        now = time.time()
        window_start = now - window_seconds
        
        # Get or create window
        if key not in self._windows:
            self._windows[key] = []
        
        # Remove old entries
        self._windows[key] = [
            ts for ts in self._windows[key] if ts > window_start
        ]
        
        # Check limit
        if len(self._windows[key]) >= max_requests:
            return False
        
        # Add current request
        self._windows[key].append(now)
        return True
    
    def get_remaining(
        self,
        identifier: str,
        action: str,
        max_requests: int,
        window_seconds: int,
    ) -> int:
        """
        Get remaining requests.
        
        Args:
            identifier: Unique identifier
            action: Action being rate limited
            max_requests: Maximum requests allowed
            window_seconds: Time window in seconds
        
        Returns:
            Number of remaining requests
        """
        key = f"{action}:{identifier}"
        now = time.time()
        window_start = now - window_seconds
        
        if key not in self._windows:
            return max_requests
        
        # Count valid entries
        count = sum(1 for ts in self._windows[key] if ts > window_start)
        return max(0, max_requests - count)


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def setup_rate_limiting(
    app: FastAPI,
    rules: Optional[Dict[str, RateLimitRule]] = None,
    exempt_paths: Optional[List[str]] = None,
) -> None:
    """
    Set up rate limiting middleware for FastAPI app.
    
    Args:
        app: FastAPI application
        rules: Custom rate limit rules
        exempt_paths: Paths exempt from rate limiting
    """
    app.add_middleware(
        RateLimitMiddleware,
        rules=rules or DEFAULT_RULES,
        exempt_paths=exempt_paths,
    )
    logger.info("Rate limiting middleware configured")


def create_rate_limit_response(
    retry_after: int,
    limit: int,
    remaining: int,
) -> JSONResponse:
    """
    Create a rate limit exceeded response.
    
    Args:
        retry_after: Seconds until retry
        limit: Rate limit
        remaining: Remaining requests
    
    Returns:
        JSONResponse with 429 status
    """
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "detail": "Rate limit exceeded. Please try again later.",
            "retry_after": retry_after,
        },
        headers={
            "Retry-After": str(retry_after),
            "X-RateLimit-Limit": str(limit),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(retry_after),
        },
    )
