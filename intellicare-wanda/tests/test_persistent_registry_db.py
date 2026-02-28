"""Tests for PersistentModuleRegistry with mocked DB (EF-W001)."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from wanda.discovery.models import ModuleInfo, ModuleStatus
from wanda.registry.persistent_registry import PersistentModuleRegistry


class FakeDBModule:
    """Fake DB module row returned by repository."""

    def __init__(self, name, url, version="1.0.0", description="", capabilities=None,
                 health_status="healthy", last_seen_at=None):
        self.agent_name = name
        self.base_url = url
        self.version = version
        self.description = description
        self.capabilities = capabilities or []
        self.health_status = health_status
        self.last_seen_at = last_seen_at or datetime.now()


class FakeHealthEvent:
    """Fake health event row."""

    def __init__(self, agent_name, event_type, reason=""):
        self.agent_name = agent_name
        self.event_type = event_type
        self.previous_status = "healthy"
        self.new_status = "unhealthy"
        self.reason = reason
        self.response_time_ms = 123
        self.occurred_at = datetime.now()


class FakeCapHistory:
    """Fake capabilities history row."""

    def __init__(self, agent_name, version, capabilities):
        self.agent_name = agent_name
        self.version = version
        self.capabilities = capabilities
        self.changed_at = datetime.now()
        self.change_type = "update"


@pytest.fixture
def mock_repo():
    repo = MagicMock()
    repo.register_or_update = AsyncMock()
    repo.mark_unhealthy = AsyncMock()
    repo.mark_healthy = AsyncMock()
    repo.get_health_history = AsyncMock(return_value=[
        FakeHealthEvent("intellicare-oswaldo", "unhealthy", "timeout")
    ])
    repo.get_capabilities_history = AsyncMock(return_value=[
        FakeCapHistory("intellicare-oswaldo", "1.0.0", ["monitoring"])
    ])
    repo.get_all_modules = AsyncMock(return_value=[
        FakeDBModule("intellicare-oswaldo", "http://localhost:8001", capabilities=["monitoring"]),
        FakeDBModule("intellicare-florence", "http://localhost:8002", health_status="unhealthy"),
    ])
    return repo


@pytest.fixture
def registry_with_db(mock_repo):
    return PersistentModuleRegistry(
        module_urls={"intellicare-oswaldo": "http://localhost:8001"},
        db_repository=mock_repo,
        timeout_seconds=2,
    )


class TestPersistenceEnabled:
    def test_has_persistence(self, registry_with_db):
        assert registry_with_db.has_persistence is True

    @pytest.mark.asyncio
    async def test_register_persists_to_db(self, registry_with_db, mock_repo):
        module = ModuleInfo(
            name="intellicare-oswaldo",
            base_url="http://localhost:8001",
            version="1.0.0",
            capabilities=["monitoring"],
            status=ModuleStatus.ONLINE,
        )
        await registry_with_db.register_or_update(module)

        # In-memory updated
        assert registry_with_db.get_module("intellicare-oswaldo") is not None
        # DB persisted
        mock_repo.register_or_update.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_mark_unhealthy_persists(self, registry_with_db, mock_repo):
        # Register first
        module = ModuleInfo(
            name="intellicare-oswaldo",
            base_url="http://localhost:8001",
            status=ModuleStatus.ONLINE,
        )
        await registry_with_db.register_or_update(module)
        await registry_with_db.mark_unhealthy("intellicare-oswaldo", "timeout")

        mock_repo.mark_unhealthy.assert_awaited_once_with("intellicare-oswaldo", "timeout")
        m = registry_with_db.get_module("intellicare-oswaldo")
        assert m.status == ModuleStatus.OFFLINE

    @pytest.mark.asyncio
    async def test_mark_healthy_persists(self, registry_with_db, mock_repo):
        module = ModuleInfo(
            name="intellicare-oswaldo",
            base_url="http://localhost:8001",
            status=ModuleStatus.OFFLINE,
        )
        await registry_with_db.register_or_update(module)
        await registry_with_db.mark_healthy("intellicare-oswaldo")

        mock_repo.mark_healthy.assert_awaited_once_with("intellicare-oswaldo")
        m = registry_with_db.get_module("intellicare-oswaldo")
        assert m.status == ModuleStatus.ONLINE

    @pytest.mark.asyncio
    async def test_get_health_history(self, registry_with_db, mock_repo):
        history = await registry_with_db.get_health_history("intellicare-oswaldo")
        assert len(history) == 1
        assert history[0]["event_type"] == "unhealthy"
        mock_repo.get_health_history.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_capabilities_history(self, registry_with_db, mock_repo):
        history = await registry_with_db.get_capabilities_history("intellicare-oswaldo")
        assert len(history) == 1
        assert history[0]["version"] == "1.0.0"
        mock_repo.get_capabilities_history.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_load_from_db(self, registry_with_db, mock_repo):
        count = await registry_with_db.load_from_db()
        assert count == 2
        assert registry_with_db.total_modules == 2
        # Check status mapping
        oswaldo = registry_with_db.get_module("intellicare-oswaldo")
        assert oswaldo.status == ModuleStatus.ONLINE  # healthy → ONLINE
        florence = registry_with_db.get_module("intellicare-florence")
        assert florence.status == ModuleStatus.OFFLINE  # unhealthy → OFFLINE


class TestDBGracefulDegradation:
    @pytest.mark.asyncio
    async def test_db_error_on_register(self, mock_repo):
        mock_repo.register_or_update = AsyncMock(side_effect=Exception("DB down"))
        reg = PersistentModuleRegistry(
            module_urls={},
            db_repository=mock_repo,
        )
        module = ModuleInfo(
            name="test",
            base_url="http://localhost:9999",
            status=ModuleStatus.ONLINE,
        )
        # Should NOT raise — falls back to in-memory
        await reg.register_or_update(module)
        assert reg.get_module("test") is not None

    @pytest.mark.asyncio
    async def test_db_error_on_mark_unhealthy(self, mock_repo):
        mock_repo.mark_unhealthy = AsyncMock(side_effect=Exception("DB down"))
        reg = PersistentModuleRegistry(
            module_urls={},
            db_repository=mock_repo,
        )
        module = ModuleInfo(name="test", base_url="http://x", status=ModuleStatus.ONLINE)
        await reg.register_or_update(module)
        # Should NOT raise
        await reg.mark_unhealthy("test", "timeout")
        assert reg.get_module("test").status == ModuleStatus.OFFLINE

    @pytest.mark.asyncio
    async def test_db_error_on_mark_healthy(self, mock_repo):
        mock_repo.mark_healthy = AsyncMock(side_effect=Exception("DB down"))
        reg = PersistentModuleRegistry(
            module_urls={},
            db_repository=mock_repo,
        )
        module = ModuleInfo(name="test", base_url="http://x", status=ModuleStatus.OFFLINE)
        await reg.register_or_update(module)
        await reg.mark_healthy("test")
        assert reg.get_module("test").status == ModuleStatus.ONLINE

    @pytest.mark.asyncio
    async def test_db_error_on_health_history(self, mock_repo):
        mock_repo.get_health_history = AsyncMock(side_effect=Exception("DB down"))
        reg = PersistentModuleRegistry(
            module_urls={},
            db_repository=mock_repo,
        )
        history = await reg.get_health_history("test")
        assert history == []

    @pytest.mark.asyncio
    async def test_db_error_on_load_from_db(self, mock_repo):
        mock_repo.get_all_modules = AsyncMock(side_effect=Exception("DB down"))
        reg = PersistentModuleRegistry(
            module_urls={},
            db_repository=mock_repo,
        )
        count = await reg.load_from_db()
        assert count == 0

    @pytest.mark.asyncio
    async def test_db_error_on_capabilities_history(self, mock_repo):
        mock_repo.get_capabilities_history = AsyncMock(side_effect=Exception("DB down"))
        reg = PersistentModuleRegistry(
            module_urls={},
            db_repository=mock_repo,
        )
        history = await reg.get_capabilities_history("test")
        assert history == []

    @pytest.mark.asyncio
    async def test_port_extraction(self, mock_repo):
        """Test port extraction from URL during register."""
        reg = PersistentModuleRegistry(
            module_urls={},
            db_repository=mock_repo,
        )
        module = ModuleInfo(
            name="test",
            base_url="http://localhost:8001",
            version="1.0.0",
            status=ModuleStatus.ONLINE,
        )
        await reg.register_or_update(module)
        # Verify the port was extracted in the call
        call_args = mock_repo.register_or_update.call_args[0][0]
        assert call_args["port"] == 8001
