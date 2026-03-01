"""Tests for MCP config, models, and exceptions (EF-W011)."""

import pytest
from datetime import datetime

from wanda.mcp.config import MCPClientConfig
from wanda.mcp.models import MCPToolInfo, MCPModuleRecord, MCPCallRecord
from wanda.mcp.exceptions import (
    MCPError,
    MCPModuleUnavailableError,
    MCPToolNotFoundError,
    MCPCallTimeoutError,
    MCPCallError,
)


class TestMCPClientConfig:
    def test_defaults(self):
        cfg = MCPClientConfig()
        assert "intellicare-ocr" in cfg.mcp_servers
        assert cfg.ocr_timeout_seconds == 30
        assert cfg.max_retries == 2

    def test_timeout_for_ocr(self):
        cfg = MCPClientConfig()
        assert cfg.get_timeout_for_tool("intellicare-ocr", "anything") == 30

    def test_timeout_for_search_tool(self):
        cfg = MCPClientConfig()
        assert cfg.get_timeout_for_tool("intellicare-superz", "web_search") == 15

    def test_timeout_for_analysis_tool(self):
        cfg = MCPClientConfig()
        assert cfg.get_timeout_for_tool("intellicare-superz", "analyze_text") == 60

    def test_timeout_for_default(self):
        cfg = MCPClientConfig()
        assert cfg.get_timeout_for_tool("unknown", "unknown") == 30


class TestMCPToolInfo:
    def test_to_dict(self):
        t = MCPToolInfo(
            name="web_search",
            description="Search the web",
            input_schema={"type": "object"},
            module_name="pierre",
            last_validated=datetime(2025, 1, 1),
        )
        d = t.to_dict()
        assert d["name"] == "web_search"
        assert d["module_name"] == "pierre"
        assert d["last_validated"] == "2025-01-01T00:00:00"


class TestMCPModuleRecord:
    def test_tools_count(self):
        r = MCPModuleRecord(
            module_name="ocr",
            agent_name="MINERVA",
            base_url="http://localhost:8008",
            available_tools=[
                MCPToolInfo(name="t1", description=""),
                MCPToolInfo(name="t2", description=""),
            ],
        )
        assert r.tools_count == 2

    def test_to_dict(self):
        r = MCPModuleRecord(
            module_name="pierre",
            agent_name="PIERRE",
            base_url="http://localhost:8009",
        )
        d = r.to_dict()
        assert d["module_name"] == "pierre"
        assert d["agent_name"] == "PIERRE"
        assert d["tools_count"] == 0


class TestMCPCallRecord:
    def test_creation(self):
        r = MCPCallRecord(
            correlation_id="abc-123",
            module_name="pierre",
            tool_name="web_search",
            status="success",
            duration_ms=150,
        )
        assert r.correlation_id == "abc-123"
        assert r.duration_ms == 150

    def test_to_dict(self):
        r = MCPCallRecord(
            correlation_id="abc-123",
            module_name="intellicare-superz",
            tool_name="web_search",
            status="success",
            duration_ms=250,
            error_message="",
        )
        d = r.to_dict()
        assert d["correlation_id"] == "abc-123"
        assert d["module_name"] == "intellicare-superz"
        assert d["tool_name"] == "web_search"
        assert d["status"] == "success"
        assert d["duration_ms"] == 250
        assert "called_at" in d


class TestMCPExceptions:
    def test_module_unavailable(self):
        e = MCPModuleUnavailableError("ocr", "down")
        assert "ocr" in str(e)

    def test_tool_not_found(self):
        e = MCPToolNotFoundError("pierre", "bad_tool")
        assert "bad_tool" in str(e)

    def test_call_timeout(self):
        e = MCPCallTimeoutError("ocr", "extract_document", 30)
        assert "30" in str(e)

    def test_call_error(self):
        e = MCPCallError("ocr", "extract_document", "Internal error")
        assert "Internal error" in str(e)

    def test_hierarchy(self):
        assert issubclass(MCPModuleUnavailableError, MCPError)
        assert issubclass(MCPToolNotFoundError, MCPError)
        assert issubclass(MCPCallTimeoutError, MCPError)
        assert issubclass(MCPCallError, MCPError)
