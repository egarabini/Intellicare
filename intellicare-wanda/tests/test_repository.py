"""Tests for ModuleRepository with mocked SQLAlchemy sessions (EF-W001)."""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from wanda.database.models import (
    MCPCallLogModel,
    MCPModuleModel,
    MCPToolModel,
    ModuleCapabilitiesHistoryModel,
    ModuleHealthEventModel,
    OrchestrationExecutionModel,
    RegisteredModuleModel,
)
from wanda.database.repository import ModuleRepository


# ── Helpers ────────────────────────────────────────────────────────────────


def make_session_factory(mock_session):
    """Wrap a mock_session as an async context manager factory."""
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=mock_session)
    cm.__aexit__ = AsyncMock(return_value=False)
    factory = MagicMock(return_value=cm)
    return factory


def make_mock_session():
    """Return a mock async SQLAlchemy session."""
    session = MagicMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.execute = AsyncMock()
    return session


def make_module(**kwargs) -> RegisteredModuleModel:
    defaults = dict(
        agent_name="intellicare-oswaldo",
        base_url="http://localhost:8001",
        port=8001,
        version="1.0.0",
        module_type="HTTP",
        status="active",
        health_status="healthy",
        capabilities=["monitoring"],
        capabilities_version=1,
        requires_patient_context=False,
        supports_ips_first=False,
        endpoints={},
        first_seen_at=datetime.now(timezone.utc),
        last_seen_at=datetime.now(timezone.utc),
        last_health_check_at=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    defaults.update(kwargs)
    m = RegisteredModuleModel(**defaults)
    return m


# ── register_or_update ─────────────────────────────────────────────────────


class TestRegisterOrUpdate:
    """ModuleRepository.register_or_update covers the new/update branches."""

    @pytest.mark.asyncio
    async def test_register_new_module(self):
        """When module not in DB, should INSERT and return the model."""
        session = make_mock_session()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        session.execute.return_value = result_mock

        new_module = make_module()
        session.refresh.side_effect = lambda obj: None

        repo = ModuleRepository(make_session_factory(session))
        module_info = {
            "agent_name": "intellicare-oswaldo",
            "module_type": "HTTP",
            "version": "1.0.0",
            "description": "Agente Oswaldo",
            "base_url": "http://localhost:8001",
            "port": 8001,
            "capabilities": ["monitoring"],
            "requires_patient_context": True,
            "supports_ips_first": False,
            "endpoints": {"/api/v1/analyze": "POST"},
        }

        # Patch refresh to assign the new module as return
        registered = None

        async def fake_refresh(obj):
            nonlocal registered
            registered = obj

        session.refresh.side_effect = fake_refresh

        await repo.register_or_update(module_info)
        session.add.assert_called_once()
        session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_update_existing_module_caps_unchanged(self):
        """Update existing module when capabilities are the same."""
        session = make_mock_session()
        existing = make_module(capabilities=["monitoring"])
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = existing
        session.execute.return_value = result_mock

        repo = ModuleRepository(make_session_factory(session))
        module_info = {
            "agent_name": "intellicare-oswaldo",
            "version": "1.1.0",
            "capabilities": ["monitoring"],  # Same caps — no version bump
            "base_url": "http://localhost:8001",
            "port": 8001,
        }
        await repo.register_or_update(module_info)

        assert existing.version == "1.1.0"
        assert existing.capabilities_version == 1  # Unchanged
        session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_update_existing_module_caps_changed(self):
        """When capabilities change, version should be bumped and history created."""
        session = make_mock_session()
        existing = make_module(capabilities=["monitoring"], capabilities_version=1)
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = existing
        session.execute.return_value = result_mock

        repo = ModuleRepository(make_session_factory(session))
        module_info = {
            "agent_name": "intellicare-oswaldo",
            "version": "2.0.0",
            "capabilities": ["monitoring", "staging"],  # New cap added
            "base_url": "http://localhost:8001",
            "port": 8001,
        }
        await repo.register_or_update(module_info)

        assert existing.capabilities_version == 2  # Bumped
        # session.add called for ModuleCapabilitiesHistoryModel
        assert session.add.call_count == 1


# ── get_active_modules ─────────────────────────────────────────────────────


class TestGetActiveModules:
    @pytest.mark.asyncio
    async def test_returns_list(self):
        session = make_mock_session()
        oswaldo = make_module(status="active", health_status="healthy")
        florence = make_module(
            agent_name="intellicare-florence",
            base_url="http://localhost:8002",
            port=8002,
            status="active",
            health_status="degraded",
        )
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = [oswaldo, florence]
        session.execute.return_value = result_mock

        repo = ModuleRepository(make_session_factory(session))
        modules = await repo.get_active_modules()
        assert len(modules) == 2

    @pytest.mark.asyncio
    async def test_returns_empty_list(self):
        session = make_mock_session()
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = []
        session.execute.return_value = result_mock

        repo = ModuleRepository(make_session_factory(session))
        modules = await repo.get_active_modules()
        assert modules == []


# ── get_all_modules ────────────────────────────────────────────────────────


class TestGetAllModules:
    @pytest.mark.asyncio
    async def test_returns_all(self):
        session = make_mock_session()
        mods = [make_module(), make_module(agent_name="intellicare-florence", base_url="http://x", port=0)]
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = mods
        session.execute.return_value = result_mock

        repo = ModuleRepository(make_session_factory(session))
        result = await repo.get_all_modules()
        assert len(result) == 2


# ── get_module ─────────────────────────────────────────────────────────────


class TestGetModule:
    @pytest.mark.asyncio
    async def test_found(self):
        session = make_mock_session()
        mod = make_module()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = mod
        session.execute.return_value = result_mock

        repo = ModuleRepository(make_session_factory(session))
        found = await repo.get_module("intellicare-oswaldo")
        assert found is mod

    @pytest.mark.asyncio
    async def test_not_found(self):
        session = make_mock_session()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        session.execute.return_value = result_mock

        repo = ModuleRepository(make_session_factory(session))
        found = await repo.get_module("non-existent")
        assert found is None


# ── get_modules_with_capability ────────────────────────────────────────────


class TestGetModulesWithCapability:
    @pytest.mark.asyncio
    async def test_filters_by_capability(self):
        session = make_mock_session()
        oswaldo = make_module(capabilities=["monitoring", "staging"])
        florence = make_module(
            agent_name="intellicare-florence",
            base_url="http://localhost:8002",
            port=8002,
            capabilities=["lab-interpretation"],
        )
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = [oswaldo, florence]
        session.execute.return_value = result_mock

        repo = ModuleRepository(make_session_factory(session))
        found = await repo.get_modules_with_capability("monitoring")
        assert len(found) == 1
        assert found[0].agent_name == "intellicare-oswaldo"

    @pytest.mark.asyncio
    async def test_no_match(self):
        session = make_mock_session()
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = []
        session.execute.return_value = result_mock

        repo = ModuleRepository(make_session_factory(session))
        found = await repo.get_modules_with_capability("unknown-cap")
        assert found == []


# ── mark_unhealthy ─────────────────────────────────────────────────────────


class TestMarkUnhealthy:
    @pytest.mark.asyncio
    async def test_marks_module_unhealthy(self):
        session = make_mock_session()
        mod = make_module(health_status="healthy")
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = mod
        session.execute.return_value = result_mock

        repo = ModuleRepository(make_session_factory(session))
        await repo.mark_unhealthy("intellicare-oswaldo", "Connection refused")

        assert mod.health_status == "unhealthy"
        session.add.assert_called_once()  # ModuleHealthEventModel added
        session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_module_not_found_noop(self):
        """If module doesn't exist, mark_unhealthy should be a no-op."""
        session = make_mock_session()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        session.execute.return_value = result_mock

        repo = ModuleRepository(make_session_factory(session))
        await repo.mark_unhealthy("non-existent", "reason")
        session.add.assert_not_called()
        session.commit.assert_not_awaited()


# ── mark_healthy ───────────────────────────────────────────────────────────


class TestMarkHealthy:
    @pytest.mark.asyncio
    async def test_restores_unhealthy_module(self):
        session = make_mock_session()
        mod = make_module(health_status="unhealthy")
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = mod
        session.execute.return_value = result_mock

        repo = ModuleRepository(make_session_factory(session))
        await repo.mark_healthy("intellicare-oswaldo")

        assert mod.health_status == "healthy"
        session.add.assert_called_once()  # ModuleHealthEventModel
        session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_already_healthy_noop(self):
        """Module already healthy should not trigger commit."""
        session = make_mock_session()
        mod = make_module(health_status="healthy")
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = mod
        session.execute.return_value = result_mock

        repo = ModuleRepository(make_session_factory(session))
        await repo.mark_healthy("intellicare-oswaldo")

        session.add.assert_not_called()
        session.commit.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_module_not_found_noop(self):
        session = make_mock_session()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        session.execute.return_value = result_mock

        repo = ModuleRepository(make_session_factory(session))
        await repo.mark_healthy("non-existent")
        session.commit.assert_not_awaited()


# ── get_health_history ─────────────────────────────────────────────────────


class TestGetHealthHistory:
    @pytest.mark.asyncio
    async def test_returns_events(self):
        session = make_mock_session()
        events = [
            ModuleHealthEventModel(
                agent_name="intellicare-oswaldo",
                event_type="went_unhealthy",
                previous_status="healthy",
                new_status="unhealthy",
            )
        ]
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = events
        session.execute.return_value = result_mock

        repo = ModuleRepository(make_session_factory(session))
        result = await repo.get_health_history("intellicare-oswaldo")
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_custom_limit(self):
        """Ensure limit parameter is passed along (no DB assertion, just no crash)."""
        session = make_mock_session()
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = []
        session.execute.return_value = result_mock

        repo = ModuleRepository(make_session_factory(session))
        result = await repo.get_health_history("intellicare-oswaldo", last_n_events=10)
        assert result == []


# ── get_capabilities_history ───────────────────────────────────────────────


class TestGetCapabilitiesHistory:
    @pytest.mark.asyncio
    async def test_returns_history(self):
        session = make_mock_session()
        history = [
            ModuleCapabilitiesHistoryModel(
                agent_name="intellicare-oswaldo",
                version=2,
                capabilities=["monitoring", "staging"],
                change_type="modified",
            )
        ]
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = history
        session.execute.return_value = result_mock

        repo = ModuleRepository(make_session_factory(session))
        result = await repo.get_capabilities_history("intellicare-oswaldo")
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_empty_history(self):
        session = make_mock_session()
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = []
        session.execute.return_value = result_mock

        repo = ModuleRepository(make_session_factory(session))
        result = await repo.get_capabilities_history("nobody")
        assert result == []


# ── log_execution ──────────────────────────────────────────────────────────


class TestLogExecution:
    @pytest.mark.asyncio
    async def test_logs_execution(self):
        session = make_mock_session()
        session.refresh = AsyncMock()

        repo = ModuleRepository(make_session_factory(session))
        execution_data = {
            "execution_id": uuid.uuid4(),
            "request_type": "analyze",
            "query": "Como está o paciente?",
            "patient_id": "P001",
            "ips_loaded": False,
            "routing_method": "keyword",
            "modules_queried": ["intellicare-oswaldo"],
            "modules_failed": [],
            "success": True,
            "total_latency_ms": 350,
        }
        await repo.log_execution(execution_data)
        session.add.assert_called_once()
        session.commit.assert_awaited_once()


# ── MCP Modules ────────────────────────────────────────────────────────────


class TestRegisterMCPModule:
    @pytest.mark.asyncio
    async def test_register_new_mcp_module(self):
        session = make_mock_session()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        session.execute.return_value = result_mock

        repo = ModuleRepository(make_session_factory(session))
        mcp_data = {
            "module_name": "intellicare-minerva",
            "agent_name": "MINERVA",
            "base_url": "http://localhost:8008",
            "mcp_endpoint": "/mcp/sse",
            "status": "healthy",
            "tools_count": 5,
        }
        await repo.register_mcp_module(mcp_data)
        session.add.assert_called_once()
        session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_update_existing_mcp_module(self):
        session = make_mock_session()
        existing = MCPModuleModel(
            module_name="intellicare-minerva",
            agent_name="MINERVA",
            base_url="http://localhost:8008",
            mcp_endpoint="/mcp/sse",
            status="healthy",
            tools_count=0,
        )
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = existing
        session.execute.return_value = result_mock

        repo = ModuleRepository(make_session_factory(session))
        mcp_data = {
            "module_name": "intellicare-minerva",
            "agent_name": "MINERVA",
            "base_url": "http://localhost:8008",
            "status": "healthy",
            "tools_count": 8,
        }
        await repo.register_mcp_module(mcp_data)

        assert existing.tools_count == 8
        session.commit.assert_awaited_once()


class TestGetMCPModules:
    @pytest.mark.asyncio
    async def test_returns_list(self):
        session = make_mock_session()
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = [
            MCPModuleModel(
                module_name="intellicare-minerva",
                agent_name="MINERVA",
                base_url="http://localhost:8008",
                mcp_endpoint="/mcp/sse",
                status="healthy",
                tools_count=3,
            )
        ]
        session.execute.return_value = result_mock

        repo = ModuleRepository(make_session_factory(session))
        modules = await repo.get_mcp_modules()
        assert len(modules) == 1

    @pytest.mark.asyncio
    async def test_get_mcp_module_by_name(self):
        session = make_mock_session()
        mod = MCPModuleModel(
            module_name="intellicare-superz",
            agent_name="PIERRE",
            base_url="http://localhost:8009",
            mcp_endpoint="/mcp/sse",
            status="healthy",
            tools_count=2,
        )
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = mod
        session.execute.return_value = result_mock

        repo = ModuleRepository(make_session_factory(session))
        found = await repo.get_mcp_module("intellicare-superz")
        assert found is mod

    @pytest.mark.asyncio
    async def test_get_mcp_module_not_found(self):
        session = make_mock_session()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        session.execute.return_value = result_mock

        repo = ModuleRepository(make_session_factory(session))
        found = await repo.get_mcp_module("non-existent")
        assert found is None


# ── MCP Tools ──────────────────────────────────────────────────────────────


class TestRegisterMCPTools:
    @pytest.mark.asyncio
    async def test_registers_tools(self):
        session = make_mock_session()
        # execute is called for DELETE then nothing else
        session.execute.return_value = MagicMock()

        repo = ModuleRepository(make_session_factory(session))
        module_id = uuid.uuid4()
        tools = [
            {"name": "parse_lab", "description": "Parse lab results", "input_schema": {}},
            {"name": "minerva_pdf", "description": "OCR a PDF", "input_schema": {}},
        ]
        result = await repo.register_mcp_tools(module_id, tools)
        # session.add called twice (one per tool)
        assert session.add.call_count == 2
        session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_registers_empty_tools(self):
        session = make_mock_session()
        session.execute.return_value = MagicMock()

        repo = ModuleRepository(make_session_factory(session))
        result = await repo.register_mcp_tools(uuid.uuid4(), [])
        session.add.assert_not_called()
        session.commit.assert_awaited_once()


class TestGetMCPTools:
    @pytest.mark.asyncio
    async def test_returns_tools(self):
        module_id = uuid.uuid4()
        session = make_mock_session()
        tools = [
            MCPToolModel(
                module_id=module_id,
                tool_name="parse_lab",
                description="Parse",
                input_schema={},
            )
        ]
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = tools
        session.execute.return_value = result_mock

        repo = ModuleRepository(make_session_factory(session))
        result = await repo.get_mcp_tools(module_id)
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_no_tools(self):
        session = make_mock_session()
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = []
        session.execute.return_value = result_mock

        repo = ModuleRepository(make_session_factory(session))
        result = await repo.get_mcp_tools(uuid.uuid4())
        assert result == []


# ── MCP Call Log ───────────────────────────────────────────────────────────


class TestLogMCPCall:
    @pytest.mark.asyncio
    async def test_logs_call(self):
        session = make_mock_session()

        repo = ModuleRepository(make_session_factory(session))
        call_data = {
            "correlation_id": "corr-abc-123",
            "module_name": "intellicare-minerva",
            "tool_name": "parse_lab_result",
            "input_summary": "exame_abc.pdf",
            "status": "success",
            "error_message": None,
            "duration_ms": 450,
        }
        await repo.log_mcp_call(call_data)
        session.add.assert_called_once()
        session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_logs_failed_call(self):
        session = make_mock_session()

        repo = ModuleRepository(make_session_factory(session))
        call_data = {
            "correlation_id": "corr-fail-999",
            "module_name": "intellicare-minerva",
            "tool_name": "parse_lab_result",
            "input_summary": None,
            "status": "error",
            "error_message": "Timeout after 30s",
            "duration_ms": 30000,
        }
        await repo.log_mcp_call(call_data)
        session.add.assert_called_once()
        session.commit.assert_awaited_once()
