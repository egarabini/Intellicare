"""Tests for IPSManager with mocked Redis (EF-W002)."""

import json
import pytest
import time
import httpx
import respx
from unittest.mock import AsyncMock, MagicMock

from wanda.ips.manager import IPSManager, IPS_KEY, IPS_STALE_KEY


def _florence_ips():
    return {
        "patient_name": "João Silva",
        "conditions": [{"code": "E11", "display": "DM2"}],
        "medications": [{"code": "A10"}],
        "allergies": [],
        "observations": [],
        "immunizations": [],
    }


@pytest.fixture
def mock_redis():
    """Async Redis mock."""
    r = MagicMock()
    r.get = AsyncMock(return_value=None)
    r.set = AsyncMock()
    r.delete = AsyncMock()
    return r


@pytest.fixture
def manager_with_redis(mock_redis):
    return IPSManager(
        florence_url="http://localhost:8002",
        redis_client=mock_redis,
        ips_ttl=3600,
        stale_ttl=86400,
    )


class TestRedisEnabled:
    def test_has_redis(self, manager_with_redis):
        assert manager_with_redis.has_redis is True

    @pytest.mark.asyncio
    async def test_stats_with_redis(self, manager_with_redis):
        stats = await manager_with_redis.get_stats()
        assert stats["has_redis"] is True


class TestRedisCacheMiss:
    @pytest.mark.asyncio
    @respx.mock
    async def test_fetches_florence_on_miss(self, manager_with_redis, mock_redis):
        respx.get("http://localhost:8002/api/v1/ips/P001").mock(
            return_value=httpx.Response(200, json=_florence_ips())
        )

        ips = await manager_with_redis.get("P001")
        assert ips.patient_id == "P001"
        assert ips.source == "florence"

        # Should store in Redis (two calls: fresh key + stale key)
        assert mock_redis.set.await_count == 2


class TestRedisCacheHit:
    @pytest.mark.asyncio
    async def test_returns_from_redis(self, manager_with_redis, mock_redis):
        cached = json.dumps({
            "patient_id": "P001",
            "patient_name": "João",
            "conditions": [{"code": "E11"}],
            "medications": [],
            "allergies": [],
            "observations": [],
            "immunizations": [],
            "source": "florence",
            "is_stale": False,
            "is_degraded": False,
            "_cached_at": time.time(),
        })
        mock_redis.get = AsyncMock(return_value=cached)

        ips = await manager_with_redis.get("P001")
        assert ips.patient_id == "P001"
        # No Florence call needed
        assert mock_redis.get.await_count >= 1


class TestRedisStaleCache:
    @pytest.mark.asyncio
    @respx.mock
    async def test_florence_down_uses_stale_redis(self, manager_with_redis, mock_redis):
        # Fresh cache miss, stale cache hit
        stale_data = json.dumps({
            "patient_id": "P001",
            "patient_name": "João",
            "conditions": [],
            "medications": [],
            "allergies": [],
            "observations": [],
            "immunizations": [],
            "source": "florence",
            "is_stale": False,
            "is_degraded": False,
            "_cached_at": time.time() - 7200,
        })
        # First call for fresh key returns None, second for stale key returns data
        mock_redis.get = AsyncMock(side_effect=[None, stale_data])

        respx.get("http://localhost:8002/api/v1/ips/P001").mock(
            side_effect=httpx.ConnectError("down")
        )

        ips = await manager_with_redis.get("P001")
        assert ips.patient_id == "P001"
        assert ips.is_stale is True


class TestRedisInvalidate:
    @pytest.mark.asyncio
    async def test_invalidate_deletes_redis_key(self, manager_with_redis, mock_redis):
        await manager_with_redis.invalidate("P001")
        mock_redis.delete.assert_awaited_once()


class TestRedisErrors:
    @pytest.mark.asyncio
    @respx.mock
    async def test_redis_error_falls_back_to_memory(self, mock_redis):
        mock_redis.get = AsyncMock(side_effect=Exception("Redis down"))
        mock_redis.set = AsyncMock(side_effect=Exception("Redis down"))

        mgr = IPSManager(
            florence_url="http://localhost:8002",
            redis_client=mock_redis,
        )

        respx.get("http://localhost:8002/api/v1/ips/P001").mock(
            return_value=httpx.Response(200, json=_florence_ips())
        )

        # Should still work via Florence + memory cache fallback
        ips = await mgr.get("P001")
        assert ips.patient_id == "P001"
        assert ips.source == "florence"

    @pytest.mark.asyncio
    async def test_redis_invalidate_error_graceful(self, mock_redis):
        mock_redis.delete = AsyncMock(side_effect=Exception("Redis down"))
        mgr = IPSManager(
            florence_url="http://localhost:8002",
            redis_client=mock_redis,
        )
        # Should NOT raise
        await mgr.invalidate("P001")
