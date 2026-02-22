"""Tests for PersistentModuleRegistry (EF-W001)."""

import pytest
from datetime import datetime

from wanda.discovery.models import ModuleInfo, ModuleStatus
from wanda.registry.persistent_registry import PersistentModuleRegistry


@pytest.fixture
def module_urls():
    return {
        "intellicare-oswaldo": "http://localhost:8001",
        "intellicare-florence": "http://localhost:8002",
    }


@pytest.fixture
def registry(module_urls):
    """PersistentModuleRegistry without DB (in-memory only)."""
    return PersistentModuleRegistry(
        module_urls=module_urls,
        db_repository=None,
        timeout_seconds=2,
    )


@pytest.fixture
def sample_module():
    return ModuleInfo(
        name="intellicare-oswaldo",
        base_url="http://localhost:8001",
        version="1.0.0",
        description="Chronic disease monitoring",
        capabilities=["chronic-disease-monitoring"],
        status=ModuleStatus.ONLINE,
        last_check=datetime.now(),
    )


class TestPersistentRegistryInMemory:
    """Test PersistentModuleRegistry in-memory mode (no DB)."""

    def test_initial_state(self, registry):
        assert registry.total_modules == 0
        assert registry.online_count == 0
        assert not registry.has_persistence
        assert registry.last_discovery is None

    @pytest.mark.asyncio
    async def test_register_or_update(self, registry, sample_module):
        await registry.register_or_update(sample_module)
        assert registry.total_modules == 1
        assert registry.online_count == 1

    @pytest.mark.asyncio
    async def test_get_module(self, registry, sample_module):
        await registry.register_or_update(sample_module)
        m = registry.get_module("intellicare-oswaldo")
        assert m is not None
        assert m.name == "intellicare-oswaldo"
        assert m.version == "1.0.0"

    @pytest.mark.asyncio
    async def test_get_module_not_found(self, registry):
        m = registry.get_module("nonexistent")
        assert m is None

    @pytest.mark.asyncio
    async def test_get_online_modules(self, registry, sample_module):
        await registry.register_or_update(sample_module)

        offline = ModuleInfo(
            name="intellicare-florence",
            base_url="http://localhost:8002",
            status=ModuleStatus.OFFLINE,
        )
        await registry.register_or_update(offline)

        online = registry.get_online_modules()
        assert len(online) == 1
        assert online[0].name == "intellicare-oswaldo"

    @pytest.mark.asyncio
    async def test_get_modules_with_capability(self, registry, sample_module):
        await registry.register_or_update(sample_module)
        found = registry.get_modules_with_capability("chronic-disease-monitoring")
        assert len(found) == 1

        not_found = registry.get_modules_with_capability("nonexistent")
        assert len(not_found) == 0

    @pytest.mark.asyncio
    async def test_mark_unhealthy(self, registry, sample_module):
        await registry.register_or_update(sample_module)
        await registry.mark_unhealthy("intellicare-oswaldo", "timeout")
        m = registry.get_module("intellicare-oswaldo")
        assert m.status == ModuleStatus.OFFLINE

    @pytest.mark.asyncio
    async def test_mark_healthy(self, registry, sample_module):
        await registry.register_or_update(sample_module)
        await registry.mark_unhealthy("intellicare-oswaldo", "timeout")
        await registry.mark_healthy("intellicare-oswaldo")
        m = registry.get_module("intellicare-oswaldo")
        assert m.status == ModuleStatus.ONLINE

    @pytest.mark.asyncio
    async def test_routing_table(self, registry, sample_module):
        await registry.register_or_update(sample_module)
        table = await registry.get_routing_table()
        assert "routing" in table
        assert "chronic-disease-monitoring" in table["routing"]
        assert "intellicare-oswaldo" in table["routing"]["chronic-disease-monitoring"]

    @pytest.mark.asyncio
    async def test_get_all_modules_dict(self, registry, sample_module):
        await registry.register_or_update(sample_module)
        modules = await registry.get_all_modules_dict()
        assert len(modules) == 1
        assert modules[0]["name"] == "intellicare-oswaldo"

    @pytest.mark.asyncio
    async def test_health_history_empty_without_db(self, registry):
        history = await registry.get_health_history("intellicare-oswaldo")
        assert history == []

    @pytest.mark.asyncio
    async def test_capabilities_history_empty_without_db(self, registry):
        history = await registry.get_capabilities_history("intellicare-oswaldo")
        assert history == []

    @pytest.mark.asyncio
    async def test_load_from_db_returns_zero_without_db(self, registry):
        count = await registry.load_from_db()
        assert count == 0

    @pytest.mark.asyncio
    async def test_update_existing_module(self, registry, sample_module):
        await registry.register_or_update(sample_module)

        updated = ModuleInfo(
            name="intellicare-oswaldo",
            base_url="http://localhost:8001",
            version="1.1.0",
            capabilities=["chronic-disease-monitoring", "staging"],
            status=ModuleStatus.ONLINE,
        )
        await registry.register_or_update(updated)

        m = registry.get_module("intellicare-oswaldo")
        assert m.version == "1.1.0"
        assert len(m.capabilities) == 2
        assert registry.total_modules == 1  # Not duplicated
