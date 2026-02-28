"""Rate Limiter Service using Redis.

Implementa rate limiting usando Redis com sliding window algorithm.
"""

import logging
import time
from typing import Any, Optional, Tuple

try:
    import redis.asyncio as aioredis
except ImportError:  # pragma: no cover - optional dependency in lightweight test envs
    aioredis = None

logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiter using Redis sliding window algorithm.
    
    O algoritmo sliding window mantém um contador de requisições
    dentro de uma janela de tempo deslizante, permitindo rate limiting
    mais preciso do que fixed window.
    """
    
    def __init__(self, redis_client: Any):
        """Initialize rate limiter.
        
        Args:
            redis_client: Redis client instance
        """
        self.redis = redis_client
    
    async def check_rate_limit(
        self,
        key: str,
        limit: int,
        window_seconds: int = 60,
    ) -> Tuple[bool, int, int, int]:
        """Check if request is within rate limit.
        
        Args:
            key: Unique identifier (ex: "api_key:123")
            limit: Maximum requests allowed in window
            window_seconds: Time window in seconds (default: 60)
        
        Returns:
            Tuple of (allowed, current_count, limit, reset_time):
                - allowed: True if request is allowed
                - current_count: Current number of requests in window
                - limit: Maximum requests allowed
                - reset_time: Unix timestamp when window resets
        """
        if limit <= 0:
            # No limit (0 = unlimited)
            return True, 0, 0, 0
        
        now = time.time()
        window_start = now - window_seconds
        
        # Redis key for this rate limit
        redis_key = f"rate_limit:{key}"
        
        # Use Redis pipeline for atomic operations
        pipe = self.redis.pipeline()
        
        # Remove old entries outside the window
        pipe.zremrangebyscore(redis_key, 0, window_start)
        
        # Count current requests in window
        pipe.zcard(redis_key)
        
        # Add current request with timestamp as score
        pipe.zadd(redis_key, {str(now): now})
        
        # Set expiration to window size + 1 second
        pipe.expire(redis_key, window_seconds + 1)
        
        # Execute pipeline
        results = await pipe.execute()
        
        # Get count (result of zcard)
        current_count = results[1]
        
        # Check if within limit
        allowed = current_count < limit
        
        # Calculate reset time (end of current window)
        reset_time = int(now + window_seconds)
        
        if not allowed:
            logger.warning(
                f"Rate limit exceeded for {key}: {current_count}/{limit} "
                f"in {window_seconds}s window"
            )
        
        return allowed, current_count, limit, reset_time
    
    async def get_current_usage(
        self,
        key: str,
        window_seconds: int = 60,
    ) -> int:
        """Get current usage count for a key.
        
        Args:
            key: Unique identifier
            window_seconds: Time window in seconds
        
        Returns:
            int: Current number of requests in window
        """
        now = time.time()
        window_start = now - window_seconds
        
        redis_key = f"rate_limit:{key}"
        
        # Remove old entries and count
        pipe = self.redis.pipeline()
        pipe.zremrangebyscore(redis_key, 0, window_start)
        pipe.zcard(redis_key)
        results = await pipe.execute()
        
        return results[1]
    
    async def reset_limit(self, key: str) -> None:
        """Reset rate limit for a key.
        
        Args:
            key: Unique identifier
        """
        redis_key = f"rate_limit:{key}"
        await self.redis.delete(redis_key)
        logger.info(f"Rate limit reset for {key}")
    
    async def get_remaining(
        self,
        key: str,
        limit: int,
        window_seconds: int = 60,
    ) -> int:
        """Get remaining requests allowed.
        
        Args:
            key: Unique identifier
            limit: Maximum requests allowed
            window_seconds: Time window in seconds
        
        Returns:
            int: Number of requests remaining (0 if limit exceeded)
        """
        if limit <= 0:
            return -1  # Unlimited
        
        current = await self.get_current_usage(key, window_seconds)
        remaining = max(0, limit - current)
        return remaining


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded."""
    
    def __init__(
        self,
        key: str,
        current: int,
        limit: int,
        reset_time: int,
    ):
        """Initialize exception.
        
        Args:
            key: Rate limit key
            current: Current request count
            limit: Maximum requests allowed
            reset_time: Unix timestamp when limit resets
        """
        self.key = key
        self.current = current
        self.limit = limit
        self.reset_time = reset_time
        
        super().__init__(
            f"Rate limit exceeded for {key}: {current}/{limit}. "
            f"Resets at {reset_time}"
        )
