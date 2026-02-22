"""Tests for IPSManager metrics wiring without external HTTP mocking libs."""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from wanda.ips.manager import IPSManager
from wanda.ips.models import IPSBundle


@pytest.mark.asyncio
async def test_ips_manager_records_cache_metrics_with_in_memory_path() -> None:
    metrics = MagicMock()
    manager = IPSManager(
        florence_url="http://unused",
        redis_client=None,
        ips_ttl=3600,
        stale_ttl=86400,
        fetch_timeout=5,
        metrics_registry=metrics,
    )

    async def _fake_fetch(patient_id: str):
        return IPSBundle(
            patient_id=patient_id,
            patient_name="Paciente Teste",
            conditions=[{"code": "E11"}],
            source="florence",
        )

    manager._fetch_from_florence = _fake_fetch  # type: ignore[method-assign]

    first = await manager.get("P100")
    assert first.patient_id == "P100"
    second = await manager.get("P100")
    assert second.patient_id == "P100"
    assert metrics.record_ips_cache_miss.called
    assert metrics.record_ips_cache_hit.called
    assert metrics.record_ips_load.called

