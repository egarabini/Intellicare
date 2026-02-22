"""Tests for IPSManager (EF-W002)."""

import pytest
import time
import httpx
import respx

from wanda.ips.models import IPSBundle, ValidationResult
from wanda.ips.manager import IPSManager


@pytest.fixture
def manager():
    """IPSManager without Redis — in-memory fallback."""
    return IPSManager(
        florence_url="http://localhost:8002",
        redis_client=None,
        ips_ttl=3600,
        stale_ttl=86400,
        fetch_timeout=5,
    )


def _florence_ips_response(patient_id="P001"):
    return {
        "patient_name": "João Silva",
        "conditions": [{"code": "E11", "display": "DM2"}],
        "medications": [{"code": "A10", "display": "Metformin"}],
        "allergies": [{"code": "Z88.0", "display": "Penicillin"}],
        "observations": [
            {"category": "laboratory", "code": "HbA1c", "value": "7.2%"}
        ],
        "immunizations": [],
    }


class TestIPSManagerBasic:
    def test_no_redis(self, manager):
        assert not manager.has_redis

    @pytest.mark.asyncio
    async def test_stats(self, manager):
        stats = await manager.get_stats()
        assert stats["has_redis"] is False
        assert stats["memory_cache_size"] == 0
        assert stats["ips_ttl"] == 3600


class TestIPSFetchFromFlorence:
    @pytest.mark.asyncio
    @respx.mock
    async def test_fetch_success(self, manager):
        respx.get("http://localhost:8002/api/v1/ips/P001").mock(
            return_value=httpx.Response(200, json=_florence_ips_response())
        )

        ips = await manager.get("P001")
        assert ips.patient_id == "P001"
        assert ips.patient_name == "João Silva"
        assert ips.source == "florence"
        assert len(ips.conditions) == 1
        assert len(ips.medications) == 1

    @pytest.mark.asyncio
    @respx.mock
    async def test_fetch_caches_in_memory(self, manager):
        respx.get("http://localhost:8002/api/v1/ips/P001").mock(
            return_value=httpx.Response(200, json=_florence_ips_response())
        )

        # First call: fetches
        ips1 = await manager.get("P001")
        assert ips1.source == "florence"

        # Second call: should hit memory cache
        ips2 = await manager.get("P001")
        assert ips2.patient_id == "P001"
        # Should have only one HTTP call (respx counts)
        assert respx.calls.call_count == 1

    @pytest.mark.asyncio
    @respx.mock
    async def test_force_refresh_bypasses_cache(self, manager):
        respx.get("http://localhost:8002/api/v1/ips/P001").mock(
            return_value=httpx.Response(200, json=_florence_ips_response())
        )

        await manager.get("P001")
        await manager.get("P001", force_refresh=True)
        assert respx.calls.call_count == 2


class TestIPSFlorenceUnavailable:
    @pytest.mark.asyncio
    @respx.mock
    async def test_florence_down_returns_empty(self, manager):
        respx.get("http://localhost:8002/api/v1/ips/P001").mock(
            side_effect=httpx.ConnectError("Connection refused")
        )

        ips = await manager.get("P001")
        assert ips.patient_id == "P001"
        assert ips.source == "empty"
        assert ips.is_degraded is True

    @pytest.mark.asyncio
    @respx.mock
    async def test_florence_500_returns_empty(self, manager):
        respx.get("http://localhost:8002/api/v1/ips/P001").mock(
            return_value=httpx.Response(500, text="Internal Server Error")
        )

        ips = await manager.get("P001")
        assert ips.source == "empty"
        assert ips.is_degraded is True

    @pytest.mark.asyncio
    @respx.mock
    async def test_florence_down_uses_stale_cache(self, manager):
        # First, populate cache
        respx.get("http://localhost:8002/api/v1/ips/P001").mock(
            return_value=httpx.Response(200, json=_florence_ips_response())
        )
        await manager.get("P001")

        # Make the cache stale by modifying its timestamp
        ips_cached, _ = manager._memory_cache["P001"]
        manager._memory_cache["P001"] = (ips_cached, time.time() - 7200)  # 2h old

        # Now Florence is down but stale cache is returned
        ips = await manager.get("P001")
        assert ips.patient_id == "P001"
        # Will return stale from memory, which is marked accordingly
        assert ips.is_stale is True


class TestIPSInvalidate:
    @pytest.mark.asyncio
    @respx.mock
    async def test_invalidate_clears_memory(self, manager):
        respx.get("http://localhost:8002/api/v1/ips/P001").mock(
            return_value=httpx.Response(200, json=_florence_ips_response())
        )

        await manager.get("P001")
        assert "P001" in manager._memory_cache

        await manager.invalidate("P001")
        assert "P001" not in manager._memory_cache


class TestIPSValidation:
    def test_validate_valid_ips(self, manager):
        ips = IPSBundle(
            patient_id="P001",
            conditions=[{"code": "E11", "display": "DM2"}],
            medications=[{"code": "A10", "display": "Metformin"}],
            allergies=[{"code": "Z88.0"}],
            observations=[{"category": "laboratory", "code": "HbA1c"}],
        )
        result = manager.validate(ips)
        assert result.is_valid
        assert len(result.errors) == 0

    def test_validate_empty_ips(self, manager):
        ips = IPSBundle.empty("P001")
        result = manager.validate(ips)
        # empty → degraded warning + no conditions/med/allergy warnings
        assert result.is_valid  # Still valid (only warnings, no required field missing)
        assert len(result.warnings) > 0

    def test_validate_missing_patient_id(self, manager):
        ips = IPSBundle(patient_id="")
        result = manager.validate(ips)
        assert not result.is_valid
        assert "patient_id is required" in result.errors

    def test_validate_stale_ips(self, manager):
        ips = IPSBundle(patient_id="P001", is_stale=True)
        result = manager.validate(ips)
        assert any("stale" in w.lower() for w in result.warnings)

    def test_validate_old_ips(self, manager):
        ips = IPSBundle(patient_id="P001", age_seconds=8000000)  # > 90 days
        result = manager.validate(ips)
        assert any("90 days" in w for w in result.warnings)


class TestIPSBatch:
    @pytest.mark.asyncio
    @respx.mock
    async def test_batch_fetch(self, manager):
        for pid in ["P001", "P002"]:
            respx.get(f"http://localhost:8002/api/v1/ips/{pid}").mock(
                return_value=httpx.Response(200, json=_florence_ips_response(pid))
            )

        results = await manager.get_batch(["P001", "P002"])
        assert len(results) == 2
        assert "P001" in results
        assert "P002" in results
