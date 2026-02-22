"""Tests for IPSFallbackStrategy (EF-W002)."""

import pytest
import httpx
import respx

from wanda.ips.models import IPSBundle
from wanda.ips.fallback import IPSFallbackStrategy


@pytest.fixture
def fallback():
    return IPSFallbackStrategy(
        oswaldo_url="http://localhost:8001",
        geralda_url="http://localhost:8006",
        timeout=3,
    )


class TestFallbackPriority:
    @pytest.mark.asyncio
    async def test_stale_ips_preferred(self, fallback):
        stale = IPSBundle(
            patient_id="P001",
            patient_name="João Silva",
            conditions=[{"code": "E11"}],
            source="florence",
        )
        result = await fallback.get_minimal_ips("P001", stale_ips=stale)
        assert result.patient_id == "P001"
        assert result.is_degraded is True
        assert result.source == "stale"

    @pytest.mark.asyncio
    @respx.mock
    async def test_oswaldo_fallback(self, fallback):
        respx.get("http://localhost:8001/api/v1/patient/P001/basic").mock(
            return_value=httpx.Response(200, json={
                "patient_name": "João",
                "conditions": [{"code": "I10"}],
            })
        )

        result = await fallback.get_minimal_ips("P001")
        assert result.patient_id == "P001"
        assert result.source == "oswaldo-fallback"
        assert result.is_degraded is True
        assert len(result.conditions) == 1

    @pytest.mark.asyncio
    @respx.mock
    async def test_geralda_fallback(self, fallback):
        respx.get("http://localhost:8001/api/v1/patient/P001/basic").mock(
            side_effect=httpx.ConnectError("down")
        )
        respx.get("http://localhost:8006/api/v1/patient/P001/basic").mock(
            return_value=httpx.Response(200, json={
                "patient_name": "João",
                "conditions": [],
                "medications": [{"code": "A10"}],
            })
        )

        result = await fallback.get_minimal_ips("P001")
        assert result.source == "geralda-fallback"
        assert result.is_degraded is True

    @pytest.mark.asyncio
    @respx.mock
    async def test_all_fail_returns_empty(self, fallback):
        respx.get("http://localhost:8001/api/v1/patient/P001/basic").mock(
            side_effect=httpx.ConnectError("down")
        )
        respx.get("http://localhost:8006/api/v1/patient/P001/basic").mock(
            side_effect=httpx.ConnectError("down")
        )

        result = await fallback.get_minimal_ips("P001")
        assert result.source == "empty"
        assert result.is_degraded is True
        assert result.conditions == []


class TestBuildEmptyIPS:
    def test_build_empty(self, fallback):
        ips = fallback.build_empty_ips("P001")
        assert ips.patient_id == "P001"
        assert ips.source == "empty"
        assert ips.is_degraded is True
