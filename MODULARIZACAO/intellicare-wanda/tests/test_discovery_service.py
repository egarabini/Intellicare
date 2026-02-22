"""Tests for DiscoveryService (EF-W001)."""

import pytest
import httpx
import respx

from wanda.discovery.models import ModuleInfo, ModuleStatus
from wanda.registry.persistent_registry import PersistentModuleRegistry
from wanda.registry.discovery_service import DiscoveryService, DiscoveryResult


@pytest.fixture
def module_urls():
    return {
        "intellicare-oswaldo": "http://localhost:8001",
        "intellicare-florence": "http://localhost:8002",
    }


@pytest.fixture
def registry(module_urls):
    return PersistentModuleRegistry(
        module_urls=module_urls,
        db_repository=None,
        timeout_seconds=2,
    )


@pytest.fixture
def discovery(registry, module_urls):
    return DiscoveryService(
        registry=registry,
        known_hosts=module_urls,
        timeout_seconds=2,
        health_check_interval=60,
    )


class TestDiscoveryResult:
    def test_empty_result(self):
        r = DiscoveryResult()
        assert r.success_count == 0
        assert r.failure_count == 0
        d = r.to_dict()
        assert d["discovered"] == []
        assert d["failed"] == []

    def test_mixed_result(self):
        r = DiscoveryResult()
        r.discovered = ["a", "b"]
        r.failed = ["c"]
        r.total_time_ms = 123.456
        assert r.success_count == 2
        assert r.failure_count == 1
        d = r.to_dict()
        assert d["total_time_ms"] == 123.5


class TestDiscoverAll:
    @pytest.mark.asyncio
    @respx.mock
    async def test_discover_all_success(self, discovery, registry):
        respx.get("http://localhost:8001/api/v1/info").mock(
            return_value=httpx.Response(200, json={
                "version": "1.0.0",
                "description": "Oswaldo",
                "capabilities": ["chronic-disease-monitoring"],
            })
        )
        respx.get("http://localhost:8001/api/v1/health").mock(
            return_value=httpx.Response(200, json={"status": "healthy"})
        )
        respx.get("http://localhost:8002/api/v1/info").mock(
            return_value=httpx.Response(200, json={
                "version": "2.0.0",
                "description": "Florence",
                "capabilities": ["lab-interpretation"],
            })
        )
        respx.get("http://localhost:8002/api/v1/health").mock(
            return_value=httpx.Response(200, json={"status": "healthy"})
        )

        result = await discovery.discover_all()
        assert result.success_count == 2
        assert result.failure_count == 0
        assert registry.total_modules == 2
        assert registry.online_count == 2

    @pytest.mark.asyncio
    @respx.mock
    async def test_discover_all_partial_failure(self, discovery, registry):
        respx.get("http://localhost:8001/api/v1/info").mock(
            return_value=httpx.Response(200, json={
                "version": "1.0.0",
                "capabilities": ["monitoring"],
            })
        )
        respx.get("http://localhost:8001/api/v1/health").mock(
            return_value=httpx.Response(200, json={"status": "healthy"})
        )
        respx.get("http://localhost:8002/api/v1/info").mock(
            side_effect=httpx.ConnectError("Connection refused")
        )

        result = await discovery.discover_all()
        assert result.success_count == 1
        assert result.failure_count == 1
        assert registry.total_modules == 2
        assert registry.online_count == 1

    @pytest.mark.asyncio
    @respx.mock
    async def test_discover_all_degraded(self, discovery, registry):
        respx.get("http://localhost:8001/api/v1/info").mock(
            return_value=httpx.Response(200, json={
                "version": "1.0.0",
                "capabilities": [],
            })
        )
        respx.get("http://localhost:8001/api/v1/health").mock(
            return_value=httpx.Response(200, json={"status": "degraded"})
        )
        respx.get("http://localhost:8002/api/v1/info").mock(
            return_value=httpx.Response(500)
        )

        result = await discovery.discover_all()
        # Oswaldo: info=200 but health=degraded → DEGRADED (still success)
        # Florence: info=500 → OFFLINE → probe returns False → failed
        assert result.success_count == 1
        assert result.failure_count == 1

        m = registry.get_module("intellicare-oswaldo")
        assert m is not None
        assert m.status == ModuleStatus.DEGRADED


class TestDiscoverSingle:
    @pytest.mark.asyncio
    @respx.mock
    async def test_discover_single_success(self, discovery, registry):
        respx.get("http://localhost:8001/api/v1/info").mock(
            return_value=httpx.Response(200, json={
                "version": "1.0.0",
                "description": "Oswaldo agent",
                "capabilities": ["monitoring"],
            })
        )
        respx.get("http://localhost:8001/api/v1/health").mock(
            return_value=httpx.Response(200, json={"status": "healthy"})
        )

        m = await discovery.discover_single("intellicare-oswaldo")
        assert m is not None
        assert m.name == "intellicare-oswaldo"
        assert m.version == "1.0.0"
        assert m.status == ModuleStatus.ONLINE

    @pytest.mark.asyncio
    async def test_discover_single_unknown_agent(self, discovery):
        m = await discovery.discover_single("nonexistent")
        assert m is None


class TestRoutingTable:
    @pytest.mark.asyncio
    async def test_routing_table_from_discovery(self, discovery, registry):
        # Manually add modules to registry
        await registry.register_or_update(ModuleInfo(
            name="intellicare-oswaldo",
            base_url="http://localhost:8001",
            capabilities=["monitoring", "staging"],
            status=ModuleStatus.ONLINE,
        ))
        table = await discovery.get_routing_table()
        assert "routing" in table
        assert "monitoring" in table["routing"]
        assert "staging" in table["routing"]


class TestPeriodicChecks:
    @pytest.mark.asyncio
    async def test_start_stop_periodic_checks(self, discovery):
        await discovery.start_periodic_checks()
        assert discovery._running
        assert discovery._task is not None

        await discovery.stop_periodic_checks()
        assert not discovery._running
        assert discovery._task is None

    @pytest.mark.asyncio
    async def test_double_start_is_idempotent(self, discovery):
        await discovery.start_periodic_checks()
        task1 = discovery._task
        await discovery.start_periodic_checks()
        task2 = discovery._task
        assert task1 is task2
        await discovery.stop_periodic_checks()
