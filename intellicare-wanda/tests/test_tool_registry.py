"""Tests for WandaToolRegistry (EF-W011)."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from wanda.mcp.tool_registry import (
    WandaToolRegistry,
    ToolDefinition,
    MCP_TOOL_DESCRIPTIONS,
)


@pytest.fixture
def mock_mcp_client():
    client = MagicMock()
    client.list_tools = AsyncMock(return_value={
        "intellicare-superz": [
            {"name": "web_search", "description": "Search"},
            {"name": "analyze_text", "description": "Analyze"},
        ],
        "intellicare-ocr": [
            {"name": "parse_lab_result", "description": "Parse labs"},
        ],
    })
    client.call_tool = AsyncMock(return_value={"result": "ok"})
    return client


class TestToolDefinition:
    def test_to_dict(self):
        td = ToolDefinition(
            name="web_search",
            description="Search the web",
            source_type="mcp",
            module_name="superz",
            invoke=lambda p: None,
        )
        d = td.to_dict()
        assert d["name"] == "web_search"
        assert d["source_type"] == "mcp"
        assert d["module_name"] == "superz"
        assert "invoke" not in d


class TestMCPToolDescriptions:
    def test_all_tools_have_descriptions(self):
        expected_tools = [
            "parse_lab_result", "extract_document", "ocr_image",
            "parse_discharge_summary", "search_documents", "index_document",
            "web_search", "search_medical_literature", "check_regulatory",
            "analyze_text", "summarize_document", "translate_to_portuguese",
        ]
        for tool in expected_tools:
            assert tool in MCP_TOOL_DESCRIPTIONS
            assert len(MCP_TOOL_DESCRIPTIONS[tool]) > 10

    def test_descriptions_are_portuguese(self):
        # All descriptions should contain Portuguese text
        for desc in MCP_TOOL_DESCRIPTIONS.values():
            # Check for common Portuguese words
            assert any(
                w in desc.lower()
                for w in ["use", "para", "de", "ou", "do", "no"]
            )


class TestWandaToolRegistry:
    @pytest.mark.asyncio
    async def test_build_from_mcp(self, mock_mcp_client):
        reg = WandaToolRegistry(mcp_client=mock_mcp_client)
        await reg.build()
        assert reg.total_tools == 3

    @pytest.mark.asyncio
    async def test_get_all_tools(self, mock_mcp_client):
        reg = WandaToolRegistry(mcp_client=mock_mcp_client)
        await reg.build()
        tools = reg.get_all_tools()
        assert len(tools) == 3
        names = {t.name for t in tools}
        assert "web_search" in names
        assert "analyze_text" in names
        assert "parse_lab_result" in names

    @pytest.mark.asyncio
    async def test_get_tool(self, mock_mcp_client):
        reg = WandaToolRegistry(mcp_client=mock_mcp_client)
        await reg.build()
        t = reg.get_tool("web_search")
        assert t is not None
        assert t.source_type == "mcp"
        assert t.module_name == "intellicare-superz"

    @pytest.mark.asyncio
    async def test_get_tool_not_found(self, mock_mcp_client):
        reg = WandaToolRegistry(mcp_client=mock_mcp_client)
        await reg.build()
        assert reg.get_tool("nonexistent") is None

    @pytest.mark.asyncio
    async def test_get_tools_by_module(self, mock_mcp_client):
        reg = WandaToolRegistry(mcp_client=mock_mcp_client)
        await reg.build()
        superz_tools = reg.get_tools_by_module("intellicare-superz")
        assert len(superz_tools) == 2
        ocr_tools = reg.get_tools_by_module("intellicare-ocr")
        assert len(ocr_tools) == 1

    @pytest.mark.asyncio
    async def test_get_tool_descriptions(self, mock_mcp_client):
        reg = WandaToolRegistry(mcp_client=mock_mcp_client)
        await reg.build()
        descs = reg.get_tool_descriptions()
        assert len(descs) == 3
        for d in descs:
            assert "name" in d
            assert "description" in d

    @pytest.mark.asyncio
    async def test_uses_mcp_descriptions(self, mock_mcp_client):
        reg = WandaToolRegistry(mcp_client=mock_mcp_client)
        await reg.build()
        t = reg.get_tool("web_search")
        # Should use MCP_TOOL_DESCRIPTIONS, not the simple "Search"
        assert "Tavily" in t.description

    @pytest.mark.asyncio
    async def test_build_without_mcp(self):
        reg = WandaToolRegistry(mcp_client=None)
        await reg.build()
        assert reg.total_tools == 0

    @pytest.mark.asyncio
    async def test_invoke_calls_mcp_client(self, mock_mcp_client):
        reg = WandaToolRegistry(mcp_client=mock_mcp_client)
        await reg.build()
        t = reg.get_tool("web_search")
        result = await t.invoke({"query": "test"}, correlation_id="abc")
        assert result == {"result": "ok"}

    @pytest.mark.asyncio
    async def test_rebuild_clears(self, mock_mcp_client):
        reg = WandaToolRegistry(mcp_client=mock_mcp_client)
        await reg.build()
        assert reg.total_tools == 3
        # Second build should clear and rebuild
        mock_mcp_client.list_tools = AsyncMock(return_value={})
        await reg.build()
        assert reg.total_tools == 0
