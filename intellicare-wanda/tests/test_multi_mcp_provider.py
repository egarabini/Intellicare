"""Tests for MultiMCPToolProvider (EF-W011)."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from wanda.mcp.multi_mcp_provider import MultiMCPToolProvider
from wanda.mcp.client import WandaMCPClient
from wanda.mcp.config import MCPClientConfig


def _make_client(tools_by_module: dict) -> WandaMCPClient:
    """Create a WandaMCPClient mock that returns specific tools."""
    client = MagicMock(spec=WandaMCPClient)
    client.connect_all = AsyncMock(return_value={m: True for m in tools_by_module})

    async def list_tools():
        return {
            module: [
                {"name": t["name"], "description": t["description"], "inputSchema": {}}
                for t in tools
            ]
            for module, tools in tools_by_module.items()
        }

    client.list_tools = list_tools
    client.call_tool = AsyncMock(return_value={"result": "ok"})
    return client


class TestMultiMCPToolProviderBuild:
    @pytest.mark.asyncio
    async def test_build_single_client(self):
        client = _make_client({
            "intellicare-minerva": [
                {"name": "extract_document", "description": "Extract text"},
                {"name": "parse_lab_result", "description": "Parse lab"},
            ]
        })
        provider = MultiMCPToolProvider([client])
        await provider.build()
        assert provider.total_tools == 2

    @pytest.mark.asyncio
    async def test_build_multiple_clients(self):
        client1 = _make_client({
            "intellicare-minerva": [
                {"name": "extract_document", "description": "Extract"},
                {"name": "parse_lab_result", "description": "Parse"},
            ]
        })
        client2 = _make_client({
            "intellicare-superz": [
                {"name": "web_search", "description": "Search web"},
                {"name": "analyze_text", "description": "Analyze"},
                {"name": "check_regulatory", "description": "Check reg"},
            ]
        })
        provider = MultiMCPToolProvider([client1, client2])
        await provider.build()
        assert provider.total_tools == 5

    @pytest.mark.asyncio
    async def test_build_empty_clients(self):
        provider = MultiMCPToolProvider([])
        await provider.build()
        assert provider.total_tools == 0

    @pytest.mark.asyncio
    async def test_rebuild_clears_previous(self):
        client = _make_client({
            "intellicare-minerva": [{"name": "extract_document", "description": "Extract"}]
        })
        provider = MultiMCPToolProvider([client])
        await provider.build()
        assert provider.total_tools == 1
        await provider.build()
        assert provider.total_tools == 1


class TestMultiMCPToolProviderNameConflict:
    @pytest.mark.asyncio
    async def test_name_conflict_is_prefixed(self):
        """When two modules expose the same tool name, the second is prefixed."""
        client1 = _make_client({
            "intellicare-minerva": [{"name": "analyze_text", "description": "OCR analyze"}]
        })
        client2 = _make_client({
            "intellicare-superz": [{"name": "analyze_text", "description": "Superz analyze"}]
        })
        provider = MultiMCPToolProvider([client1, client2])
        await provider.build()
        # Both should exist: one plain, one prefixed
        assert provider.total_tools == 2
        names = {t.name for t in provider.get_all_tools()}
        assert "analyze_text" in names
        assert "intellicare-superz_analyze_text" in names

    @pytest.mark.asyncio
    async def test_no_conflict_no_prefix(self):
        client1 = _make_client({
            "intellicare-minerva": [{"name": "parse_lab_result", "description": "Parse lab"}]
        })
        client2 = _make_client({
            "intellicare-superz": [{"name": "web_search", "description": "Search"}]
        })
        provider = MultiMCPToolProvider([client1, client2])
        await provider.build()
        names = {t.name for t in provider.get_all_tools()}
        assert "parse_lab_result" in names
        assert "web_search" in names
        # No prefixed names
        assert not any("_" in n and n.startswith("intellicare") for n in names)


class TestMultiMCPToolProviderGetTool:
    @pytest.mark.asyncio
    async def test_get_tool_by_name(self):
        client = _make_client({
            "intellicare-minerva": [{"name": "extract_document", "description": "Extract"}]
        })
        provider = MultiMCPToolProvider([client])
        await provider.build()

        tool = provider.get_tool("extract_document")
        assert tool is not None
        assert tool.name == "extract_document"
        assert tool.module_name == "intellicare-minerva"
        assert tool.source_type == "mcp"

    @pytest.mark.asyncio
    async def test_get_tool_not_found(self):
        provider = MultiMCPToolProvider([])
        await provider.build()
        assert provider.get_tool("nonexistent") is None

    @pytest.mark.asyncio
    async def test_get_tools_by_module(self):
        client = _make_client({
            "intellicare-minerva": [
                {"name": "extract_document", "description": "Extract"},
                {"name": "parse_lab_result", "description": "Parse"},
            ]
        })
        provider = MultiMCPToolProvider([client])
        await provider.build()

        minerva_tools = provider.get_tools_by_module("intellicare-minerva")
        assert len(minerva_tools) == 2
        assert all(t.module_name == "intellicare-minerva" for t in minerva_tools)

    @pytest.mark.asyncio
    async def test_get_tools_by_module_empty(self):
        provider = MultiMCPToolProvider([])
        await provider.build()
        assert provider.get_tools_by_module("intellicare-nonexistent") == []

    @pytest.mark.asyncio
    async def test_get_all_tools(self):
        client = _make_client({
            "intellicare-minerva": [
                {"name": "extract_document", "description": "Extract"},
            ],
            "intellicare-superz": [
                {"name": "web_search", "description": "Search"},
            ],
        })
        provider = MultiMCPToolProvider([client])
        await provider.build()
        tools = provider.get_all_tools()
        assert len(tools) == 2


class TestMultiMCPToolProviderInvoke:
    @pytest.mark.asyncio
    async def test_invoke_calls_client_call_tool(self):
        """Tool invoker calls the correct WandaMCPClient.call_tool."""
        client = _make_client({
            "intellicare-minerva": [{"name": "parse_lab_result", "description": "Parse"}]
        })
        # Override call_tool to return something we can verify
        client.call_tool = AsyncMock(return_value={"lab": {"glucose": 95}})

        provider = MultiMCPToolProvider([client])
        await provider.build()

        tool = provider.get_tool("parse_lab_result")
        assert tool is not None
        result = await tool.invoke({"file_path": "/tmp/laudo.pdf"})
        assert result["lab"]["glucose"] == 95
        client.call_tool.assert_called_once_with(
            module_name="intellicare-minerva",
            tool_name="parse_lab_result",
            params={"file_path": "/tmp/laudo.pdf"},
            correlation_id="",
        )
