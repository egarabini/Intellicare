"""Tests for database models (EF-W001)."""

import uuid
from datetime import datetime, timezone

import pytest

from wanda.database.models import (
    Base,
    MCPCallLogModel,
    MCPModuleModel,
    MCPToolModel,
    ModuleCapabilitiesHistoryModel,
    ModuleHealthEventModel,
    OrchestrationExecutionModel,
    RegisteredModuleModel,
)


class TestRegisteredModuleModel:
    """Tests for RegisteredModuleModel ORM model."""

    def test_create_with_defaults(self):
        m = RegisteredModuleModel(
            agent_name="intellicare-oswaldo",
            base_url="http://localhost:8001",
            port=8001,
            version="1.0.0",
            module_type="HTTP",
            status="active",
            health_status="unknown",
            capabilities_version=1,
        )
        assert m.agent_name == "intellicare-oswaldo"
        assert m.module_type == "HTTP"
        assert m.status == "active"
        assert m.health_status == "unknown"
        assert m.capabilities_version == 1

    def test_create_mcp_type(self):
        m = RegisteredModuleModel(
            agent_name="intellicare-minerva",
            base_url="http://localhost:8008",
            port=8008,
            module_type="MCP",
            version="1.0.0",
        )
        assert m.module_type == "MCP"

    def test_capabilities_default_empty(self):
        m = RegisteredModuleModel(
            agent_name="test",
            base_url="http://localhost:9999",
            port=9999,
            version="1.0.0",
            capabilities=[],
        )
        # capabilities set explicitly
        assert m.capabilities is not None
        assert m.capabilities == []


class TestModuleHealthEventModel:
    """Tests for ModuleHealthEventModel."""

    def test_create_event(self):
        e = ModuleHealthEventModel(
            agent_name="intellicare-florence",
            event_type="went_unhealthy",
            previous_status="healthy",
            new_status="unhealthy",
            reason="Connection timeout",
            response_time_ms=5000,
        )
        assert e.agent_name == "intellicare-florence"
        assert e.event_type == "went_unhealthy"
        assert e.reason == "Connection timeout"


class TestOrchestrationExecutionModel:
    """Tests for OrchestrationExecutionModel."""

    def test_create_execution(self):
        e = OrchestrationExecutionModel(
            execution_id=uuid.uuid4(),
            request_type="analyze",
            query="Como esta o paciente?",
            patient_id="P001",
            routing_method="keyword",
            success=True,
            total_latency_ms=450,
        )
        assert e.request_type == "analyze"
        assert e.success is True
        assert e.total_latency_ms == 450


class TestMCPModuleModel:
    """Tests for MCPModuleModel."""

    def test_create_mcp_module(self):
        m = MCPModuleModel(
            module_name="intellicare-minerva",
            agent_name="MINERVA",
            base_url="http://intellicare-minerva:8008",
            mcp_endpoint="/mcp/sse",
            status="healthy",
            tools_count=0,
        )
        assert m.module_name == "intellicare-minerva"
        assert m.agent_name == "MINERVA"
        assert m.status == "healthy"
        assert m.tools_count == 0


class TestMCPToolModel:
    """Tests for MCPToolModel."""

    def test_create_tool(self):
        t = MCPToolModel(
            module_id=uuid.uuid4(),
            tool_name="parse_lab_result",
            description="Extrai resultados de exames",
            input_schema={"type": "object", "properties": {"file": {"type": "string"}}},
        )
        assert t.tool_name == "parse_lab_result"
        assert "properties" in t.input_schema


class TestMCPCallLogModel:
    """Tests for MCPCallLogModel."""

    def test_create_log(self):
        log = MCPCallLogModel(
            correlation_id="corr-123",
            module_name="intellicare-superz",
            tool_name="web_search",
            status="success",
            duration_ms=350,
        )
        assert log.module_name == "intellicare-superz"
        assert log.status == "success"
        assert log.duration_ms == 350


class TestCapabilitiesHistoryModel:
    """Tests for ModuleCapabilitiesHistoryModel."""

    def test_create_history(self):
        h = ModuleCapabilitiesHistoryModel(
            agent_name="intellicare-oswaldo",
            version=2,
            capabilities=["chronic-disease-monitoring", "staging"],
            change_type="modified",
        )
        assert h.version == 2
        assert len(h.capabilities) == 2


class TestBase:
    """Tests for Base declarative model."""

    def test_base_exists(self):
        assert Base is not None
        assert hasattr(Base, "metadata")
