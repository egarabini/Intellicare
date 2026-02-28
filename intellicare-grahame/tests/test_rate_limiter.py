"""Tests for Rate Limiter Service."""

import pytest
import sys
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import time

# Mock redis module before importing
mock_redis_module = MagicMock()
mock_redis_module.asyncio = MagicMock()
sys.modules['redis'] = mock_redis_module
sys.modules['redis.asyncio'] = mock_redis_module.asyncio

from grahame.services.rate_limiter import RateLimiter, RateLimitExceeded


@pytest.fixture
def mock_redis():
    """Create mock Redis client."""
    redis = AsyncMock()
    
    # Mock pipeline
    pipe = AsyncMock()
    pipe.zremrangebyscore = MagicMock(return_value=pipe)
    pipe.zcard = MagicMock(return_value=pipe)
    pipe.zadd = MagicMock(return_value=pipe)
    pipe.expire = MagicMock(return_value=pipe)
    pipe.execute = AsyncMock(return_value=[None, 0, None, None])  # zcard returns 0
    
    redis.pipeline = MagicMock(return_value=pipe)
    redis.delete = AsyncMock()
    
    return redis


@pytest.fixture
def rate_limiter(mock_redis):
    """Create RateLimiter instance with mock Redis."""
    return RateLimiter(mock_redis)


@pytest.mark.asyncio
async def test_check_rate_limit_no_limit(rate_limiter):
    """Test that rate limit with limit=0 allows all requests."""
    allowed, current, limit, reset_time = await rate_limiter.check_rate_limit(
        key="test_key",
        limit=0,  # No limit
        window_seconds=60,
    )
    
    assert allowed is True
    assert current == 0
    assert limit == 0
    assert reset_time == 0


@pytest.mark.asyncio
async def test_check_rate_limit_within_limit(rate_limiter, mock_redis):
    """Test that request within limit is allowed."""
    # Mock zcard to return 5 (current count)
    pipe = mock_redis.pipeline.return_value
    pipe.execute = AsyncMock(return_value=[None, 5, None, None])
    
    allowed, current, limit, reset_time = await rate_limiter.check_rate_limit(
        key="test_key",
        limit=10,  # Limit is 10
        window_seconds=60,
    )
    
    assert allowed is True
    assert current == 5
    assert limit == 10
    assert reset_time > 0


@pytest.mark.asyncio
async def test_check_rate_limit_exceeded(rate_limiter, mock_redis):
    """Test that request exceeding limit is rejected."""
    # Mock zcard to return 10 (at limit)
    pipe = mock_redis.pipeline.return_value
    pipe.execute = AsyncMock(return_value=[None, 10, None, None])
    
    allowed, current, limit, reset_time = await rate_limiter.check_rate_limit(
        key="test_key",
        limit=10,  # Limit is 10
        window_seconds=60,
    )
    
    assert allowed is False
    assert current == 10
    assert limit == 10
    assert reset_time > 0


@pytest.mark.asyncio
async def test_get_current_usage(rate_limiter, mock_redis):
    """Test getting current usage count."""
    # Mock pipeline to return count of 7
    pipe = mock_redis.pipeline.return_value
    pipe.execute = AsyncMock(return_value=[None, 7])
    
    usage = await rate_limiter.get_current_usage(
        key="test_key",
        window_seconds=60,
    )
    
    assert usage == 7


@pytest.mark.asyncio
async def test_reset_limit(rate_limiter, mock_redis):
    """Test resetting rate limit."""
    await rate_limiter.reset_limit("test_key")
    
    mock_redis.delete.assert_called_once_with("rate_limit:test_key")


@pytest.mark.asyncio
async def test_get_remaining_unlimited(rate_limiter):
    """Test getting remaining requests with no limit."""
    remaining = await rate_limiter.get_remaining(
        key="test_key",
        limit=0,  # Unlimited
        window_seconds=60,
    )
    
    assert remaining == -1  # -1 indicates unlimited


@pytest.mark.asyncio
async def test_get_remaining_with_usage(rate_limiter, mock_redis):
    """Test getting remaining requests with current usage."""
    # Mock current usage of 3
    pipe = mock_redis.pipeline.return_value
    pipe.execute = AsyncMock(return_value=[None, 3])
    
    remaining = await rate_limiter.get_remaining(
        key="test_key",
        limit=10,
        window_seconds=60,
    )
    
    assert remaining == 7  # 10 - 3 = 7


@pytest.mark.asyncio
async def test_get_remaining_exceeded(rate_limiter, mock_redis):
    """Test getting remaining requests when limit is exceeded."""
    # Mock current usage of 12 (over limit of 10)
    pipe = mock_redis.pipeline.return_value
    pipe.execute = AsyncMock(return_value=[None, 12])
    
    remaining = await rate_limiter.get_remaining(
        key="test_key",
        limit=10,
        window_seconds=60,
    )
    
    assert remaining == 0  # Can't go negative


@pytest.mark.asyncio
async def test_rate_limit_exception():
    """Test RateLimitExceeded exception."""
    exc = RateLimitExceeded(
        key="test_key",
        current=15,
        limit=10,
        reset_time=1234567890,
    )
    
    assert exc.key == "test_key"
    assert exc.current == 15
    assert exc.limit == 10
    assert exc.reset_time == 1234567890
    assert "15/10" in str(exc)

