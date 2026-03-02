"""Tests for WandaMCPClient (EF-W011)."""

import pytest
import httpx
import respx

from wanda.mcp.client import WandaMCPClient, DEGRADATION_POLICY
from wanda.mcp.config import MCPClientConfig
from wanda.mcp.exceptions import (
    MCPCallError,
    MCPCallTimeoutError,
    MCPModuleUnavailableError,
    MCPToolNotFoundError,
)
from wanda.mcp.models import MCPToolInfo


# ── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture
def config():
    return MCPClientConfig(
        mcp_servers={
            "intellicare-minerva": "http://localhost:8008",
            "intellicare-superz": "http://localhost:8009",
        },
        mcp_agent_names={
            "intellicare-minerva": "MINERVA",
            "intellicare-superz": "PIERRE",
        },
        max_retries=0,  # Faster tests
        retry_delay_seconds=0.01,
        connection_timeout_seconds=3,
    )


@pytest.fixture
def client(config):
    return WandaMCPClient(config=config, db_repository=None)


def _minerva_tools_response():
    """MINERVA tool list — raw list format."""
    return [
        {
            "name": "extract_document",
            "description": "Extract text from medical documents",
            "inputSchema": {"type": "object", "properties": {"file_path": {"type": "string"}}},
        },
        {
            "name": "parse_lab_result",
            "description": "Parse lab results from PDF",
            "inputSchema": {"type": "object", "properties": {"file_path": {"type": "string"}}},
        },
    ]


def _superz_tools_response():
    """PIERRE tool list — wrapped in {'tools': [...]} format."""
    return {
        "tools": [
            {
                "name": "web_search",
                "description": "Search the web",
                "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}}},
            },
            {
                "name": "analyze_text",
                "description": "Analyze text with LLM",
                "inputSchema": {"type": "object", "properties": {"text": {"type": "string"}}},
            },
        ],
        "count": 2,
    }


# ── Init ─────────────────────────────────────────────────────────────────────

class TestMCPClientInit:
    def test_default_state(self, client):
        assert client.connected_modules == []
        assert client._call_log == []

    def test_config_defaults(self):
        cfg = MCPClientConfig()
        assert "intellicare-minerva" in cfg.mcp_servers
        assert "intellicare-superz" in cfg.mcp_servers
        assert cfg.max_retries == 2

    def test_config_per_module_paths(self):
        cfg = MCPClientConfig()
        # MINERVA paths
        assert cfg.mcp_tool_list_paths["intellicare-minerva"] == "/mcp/tools"
        assert cfg.mcp_tool_call_style["intellicare-minerva"] == "path_params"
        # PIERRE paths
        assert cfg.mcp_tool_list_paths["intellicare-superz"] == "/api/v1/mcp/tools"
        assert cfg.mcp_tool_call_style["intellicare-superz"] == "body_named"

    def test_config_get_list_url(self):
        cfg = MCPClientConfig()
        assert cfg.get_list_url("intellicare-minerva", "http://localhost:8008") == \
               "http://localhost:8008/mcp/tools"
        assert cfg.get_list_url("intellicare-superz", "http://localhost:8009") == \
               "http://localhost:8009/api/v1/mcp/tools"

    def test_config_get_call_url_and_body_minerva(self):
        cfg = MCPClientConfig()
        url, body = cfg.get_call_url_and_body(
            "intellicare-minerva", "http://localhost:8008", "parse_lab_result", {"file_path": "/tmp/x.pdf"}
        )
        assert url == "http://localhost:8008/mcp/tools/parse_lab_result"
        assert body == {"file_path": "/tmp/x.pdf"}

    def test_config_get_call_url_and_body_pierre(self):
        cfg = MCPClientConfig()
        url, body = cfg.get_call_url_and_body(
            "intellicare-superz", "http://localhost:8009", "web_search", {"query": "DM2"}
        )
        assert url == "http://localhost:8009/api/v1/mcp/call"
        assert body == {"name": "web_search", "arguments": {"query": "DM2"}}


# ── connect_all ──────────────────────────────────────────────────────────────

class TestMCPClientConnectAll:
    @pytest.mark.asyncio
    @respx.mock
    async def test_connect_all_success(self, client):
        # MINERVA: health + /mcp/tools
        respx.get("http://localhost:8008/api/v1/health").mock(
            return_value=httpx.Response(200, json={"status": "healthy"})
        )
        respx.get("http://localhost:8008/mcp/tools").mock(
            return_value=httpx.Response(200, json=_minerva_tools_response())
        )
        # PIERRE: health + /api/v1/mcp/tools
        respx.get("http://localhost:8009/api/v1/health").mock(
            return_value=httpx.Response(200, json={"status": "healthy"})
        )
        respx.get("http://localhost:8009/api/v1/mcp/tools").mock(
            return_value=httpx.Response(200, json=_superz_tools_response())
        )

        results = await client.connect_all()
        assert results["intellicare-minerva"] is True
        assert results["intellicare-superz"] is True
        assert len(client.connected_modules) == 2

    @pytest.mark.asyncio
    @respx.mock
    async def test_connect_partial_failure(self, client):
        respx.get("http://localhost:8008/api/v1/health").mock(
            side_effect=httpx.ConnectError("down")
        )
        respx.get("http://localhost:8009/api/v1/health").mock(
            return_value=httpx.Response(200, json={"status": "healthy"})
        )
        respx.get("http://localhost:8009/api/v1/mcp/tools").mock(
            return_value=httpx.Response(200, json=_superz_tools_response())
        )

        results = await client.connect_all()
        assert results["intellicare-minerva"] is False
        assert results["intellicare-superz"] is True
        assert len(client.connected_modules) == 1

    @pytest.mark.asyncio
    @respx.mock
    async def test_connect_all_both_down(self, client):
        respx.get("http://localhost:8008/api/v1/health").mock(
            side_effect=httpx.ConnectError("down")
        )
        respx.get("http://localhost:8009/api/v1/health").mock(
            side_effect=httpx.ConnectError("down")
        )

        results = await client.connect_all()
        assert results["intellicare-minerva"] is False
        assert results["intellicare-superz"] is False
        assert client.connected_modules == []


# ── call_tool ────────────────────────────────────────────────────────────────

class TestMCPCallTool:
    @pytest.mark.asyncio
    @respx.mock
    async def test_call_pierre_tool_success(self, client):
        """PIERRE uses body_named style: POST /api/v1/mcp/call with {"name":..., "arguments":...}."""
        respx.get("http://localhost:8009/api/v1/health").mock(
            return_value=httpx.Response(200, json={"status": "healthy"})
        )
        respx.get("http://localhost:8009/api/v1/mcp/tools").mock(
            return_value=httpx.Response(200, json=_superz_tools_response())
        )
        respx.get("http://localhost:8008/api/v1/health").mock(
            side_effect=httpx.ConnectError("down")
        )
        await client.connect_all()

        respx.post("http://localhost:8009/api/v1/mcp/call").mock(
            return_value=httpx.Response(200, json={"results": ["result1"]})
        )

        result = await client.call_tool(
            "intellicare-superz", "web_search", {"query": "DM2 guidelines"}
        )
        assert result["results"] == ["result1"]
        assert len(client._call_log) == 1
        assert client._call_log[0].status == "success"

    @pytest.mark.asyncio
    @respx.mock
    async def test_call_minerva_tool_success(self, client):
        """MINERVA uses path_params style: POST /mcp/tools/{tool_name} with params as body."""
        respx.get("http://localhost:8008/api/v1/health").mock(
            return_value=httpx.Response(200, json={"status": "healthy"})
        )
        respx.get("http://localhost:8008/mcp/tools").mock(
            return_value=httpx.Response(200, json=_minerva_tools_response())
        )
        respx.get("http://localhost:8009/api/v1/health").mock(
            side_effect=httpx.ConnectError("down")
        )
        await client.connect_all()

        respx.post("http://localhost:8008/mcp/tools/parse_lab_result").mock(
            return_value=httpx.Response(200, json={"lab_data": {"glucose": 95}})
        )

        result = await client.call_tool(
            "intellicare-minerva", "parse_lab_result", {"file_path": "/tmp/laudo.pdf"}
        )
        assert result["lab_data"]["glucose"] == 95
        assert client._call_log[0].status == "success"

    @pytest.mark.asyncio
    async def test_call_tool_module_not_connected(self, client):
        with pytest.raises(MCPModuleUnavailableError):
            await client.call_tool("intellicare-minerva", "some_tool", {})

    @pytest.mark.asyncio
    @respx.mock
    async def test_call_tool_not_found(self, client):
        respx.get("http://localhost:8009/api/v1/health").mock(
            return_value=httpx.Response(200)
        )
        respx.get("http://localhost:8009/api/v1/mcp/tools").mock(
            return_value=httpx.Response(200, json=_superz_tools_response())
        )
        respx.get("http://localhost:8008/api/v1/health").mock(
            side_effect=httpx.ConnectError("down")
        )
        await client.connect_all()

        with pytest.raises(MCPToolNotFoundError):
            await client.call_tool("intellicare-superz", "nonexistent_tool", {})

    @pytest.mark.asyncio
    @respx.mock
    async def test_call_pierre_tool_server_error(self, client):
        respx.get("http://localhost:8009/api/v1/health").mock(
            return_value=httpx.Response(200)
        )
        respx.get("http://localhost:8009/api/v1/mcp/tools").mock(
            return_value=httpx.Response(200, json=_superz_tools_response())
        )
        respx.get("http://localhost:8008/api/v1/health").mock(
            side_effect=httpx.ConnectError("down")
        )
        await client.connect_all()

        respx.post("http://localhost:8009/api/v1/mcp/call").mock(
            return_value=httpx.Response(500, text="Internal error")
        )

        with pytest.raises(MCPCallError):
            await client.call_tool(
                "intellicare-superz", "web_search", {"query": "test"}
            )

    @pytest.mark.asyncio
    @respx.mock
    async def test_call_pierre_tool_timeout(self, client):
        respx.get("http://localhost:8009/api/v1/health").mock(
            return_value=httpx.Response(200)
        )
        respx.get("http://localhost:8009/api/v1/mcp/tools").mock(
            return_value=httpx.Response(200, json=_superz_tools_response())
        )
        respx.get("http://localhost:8008/api/v1/health").mock(
            side_effect=httpx.ConnectError("down")
        )
        await client.connect_all()

        respx.post("http://localhost:8009/api/v1/mcp/call").mock(
            side_effect=httpx.TimeoutException("timeout")
        )

        with pytest.raises(MCPCallTimeoutError):
            await client.call_tool(
                "intellicare-superz", "web_search", {"query": "test"}
            )


# ── list_tools ───────────────────────────────────────────────────────────────

class TestMCPListTools:
    @pytest.mark.asyncio
    @respx.mock
    async def test_list_tools_pierre(self, client):
        respx.get("http://localhost:8009/api/v1/health").mock(
            return_value=httpx.Response(200)
        )
        respx.get("http://localhost:8009/api/v1/mcp/tools").mock(
            return_value=httpx.Response(200, json=_superz_tools_response())
        )
        respx.get("http://localhost:8008/api/v1/health").mock(
            side_effect=httpx.ConnectError("down")
        )
        await client.connect_all()

        tools = await client.list_tools("intellicare-superz")
        assert "intellicare-superz" in tools
        assert len(tools["intellicare-superz"]) == 2

    @pytest.mark.asyncio
    @respx.mock
    async def test_list_tools_minerva(self, client):
        respx.get("http://localhost:8008/api/v1/health").mock(
            return_value=httpx.Response(200)
        )
        respx.get("http://localhost:8008/mcp/tools").mock(
            return_value=httpx.Response(200, json=_minerva_tools_response())
        )
        respx.get("http://localhost:8009/api/v1/health").mock(
            side_effect=httpx.ConnectError("down")
        )
        await client.connect_all()

        tools = await client.list_tools("intellicare-minerva")
        assert "intellicare-minerva" in tools
        assert len(tools["intellicare-minerva"]) == 2

    @pytest.mark.asyncio
    async def test_list_tools_empty(self, client):
        tools = await client.list_tools()
        assert tools == {}


# ── health_check ─────────────────────────────────────────────────────────────

class TestMCPHealthCheck:
    @pytest.mark.asyncio
    @respx.mock
    async def test_health_check_healthy(self, client):
        respx.get("http://localhost:8009/api/v1/health").mock(
            return_value=httpx.Response(200)
        )
        assert await client.health_check("intellicare-superz") is True

    @pytest.mark.asyncio
    @respx.mock
    async def test_health_check_down(self, client):
        respx.get("http://localhost:8009/api/v1/health").mock(
            side_effect=httpx.ConnectError("down")
        )
        assert await client.health_check("intellicare-superz") is False

    @pytest.mark.asyncio
    async def test_health_check_unknown_module(self, client):
        assert await client.health_check("nonexistent") is False


# ── degradation ──────────────────────────────────────────────────────────────

class TestMCPDegradation:
    def test_degradation_message_minerva(self, client):
        msg = client.get_degradation_message("intellicare-minerva")
        assert "MINERVA" in msg

    def test_degradation_message_pierre(self, client):
        msg = client.get_degradation_message("intellicare-superz")
        assert "PIERRE" in msg

    def test_can_continue_without(self, client):
        assert client.can_continue_without("intellicare-minerva") is True
        assert client.can_continue_without("intellicare-superz") is True
        assert client.can_continue_without("unknown-module") is True

    def test_degradation_policy_structure(self):
        assert "intellicare-minerva" in DEGRADATION_POLICY
        assert "intellicare-superz" in DEGRADATION_POLICY
        for policy in DEGRADATION_POLICY.values():
            assert "fallback_message" in policy
            assert "can_continue_without" in policy
            assert "tools_affected" in policy

    def test_minerva_tools_in_policy(self):
        policy = DEGRADATION_POLICY["intellicare-minerva"]
        assert "extract_document" in policy["tools_affected"]
        assert "parse_lab_result" in policy["tools_affected"]

    def test_pierre_tools_in_policy(self):
        policy = DEGRADATION_POLICY["intellicare-superz"]
        assert "web_search" in policy["tools_affected"]
        assert "search_medical_literature" in policy["tools_affected"]


# ── module records ───────────────────────────────────────────────────────────

class TestMCPModuleRecords:
    @pytest.mark.asyncio
    @respx.mock
    async def test_records_populated_after_connect(self, client):
        respx.get("http://localhost:8009/api/v1/health").mock(
            return_value=httpx.Response(200)
        )
        respx.get("http://localhost:8009/api/v1/mcp/tools").mock(
            return_value=httpx.Response(200, json=_superz_tools_response())
        )
        respx.get("http://localhost:8008/api/v1/health").mock(
            side_effect=httpx.ConnectError("down")
        )
        await client.connect_all()

        records = client.get_all_module_records()
        assert len(records) == 1
        assert records[0].module_name == "intellicare-superz"
        assert records[0].agent_name == "PIERRE"
        assert records[0].tools_count == 2

    @pytest.mark.asyncio
    @respx.mock
    async def test_module_record_dict(self, client):
        respx.get("http://localhost:8009/api/v1/health").mock(
            return_value=httpx.Response(200)
        )
        respx.get("http://localhost:8009/api/v1/mcp/tools").mock(
            return_value=httpx.Response(200, json=_superz_tools_response())
        )
        respx.get("http://localhost:8008/api/v1/health").mock(
            side_effect=httpx.ConnectError("down")
        )
        await client.connect_all()

        record = client.get_module_record("intellicare-superz")
        assert record is not None
        d = record.to_dict()
        assert d["module_name"] == "intellicare-superz"
        assert d["tools_count"] == 2
        assert d["agent_name"] == "PIERRE"

    @pytest.mark.asyncio
    @respx.mock
    async def test_both_modules_in_records(self, client):
        respx.get("http://localhost:8008/api/v1/health").mock(
            return_value=httpx.Response(200)
        )
        respx.get("http://localhost:8008/mcp/tools").mock(
            return_value=httpx.Response(200, json=_minerva_tools_response())
        )
        respx.get("http://localhost:8009/api/v1/health").mock(
            return_value=httpx.Response(200)
        )
        respx.get("http://localhost:8009/api/v1/mcp/tools").mock(
            return_value=httpx.Response(200, json=_superz_tools_response())
        )
        await client.connect_all()

        records = client.get_all_module_records()
        assert len(records) == 2
        names = {r.module_name for r in records}
        assert "intellicare-minerva" in names
        assert "intellicare-superz" in names


# ── sanitize params ──────────────────────────────────────────────────────────

class TestMCPSanitizeParams:
    def test_sanitize_sensitive(self, client):
        params = {
            "query": "test",
            "base64_image": "aGVsbG8=",
            "file_content": "lots of text...",
            "password": "secret",
        }
        sanitized = client._sanitize_params(params)
        assert sanitized["query"] == "test"
        assert "<" in sanitized["base64_image"]
        assert "<" in sanitized["file_content"]
        assert "<" in sanitized["password"]

    def test_sanitize_non_sensitive(self, client):
        params = {"query": "dm2", "max_results": 5}
        sanitized = client._sanitize_params(params)
        assert sanitized == params
