"""Tests for MCP API routes (EF-W011)."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, PropertyMock

from fastapi.testclient import TestClient
from fastapi import FastAPI

from wanda.api.mcp_routes import router, init_mcp_routes
from wanda.mcp.models import MCPModuleRecord, MCPToolInfo


@pytest.fixture
def mock_mcp_client():
    client = MagicMock()

    # connected_modules property
    type(client).connected_modules = PropertyMock(return_value=["intellicare-superz"])

    record = MCPModuleRecord(
        module_name="intellicare-superz",
        agent_name="PIERRE",
        base_url="http://localhost:8009",
        status="healthy",
        available_tools=[
            MCPToolInfo(name="web_search", description="Search"),
            MCPToolInfo(name="analyze_text", description="Analyze"),
        ],
    )
    client.get_all_module_records.return_value = [record]
    client.get_module_record.return_value = record

    client.list_tools = AsyncMock(return_value={
        "intellicare-superz": [
            {"name": "web_search", "description": "Search"},
            {"name": "analyze_text", "description": "Analyze"},
        ]
    })

    client.refresh_tools = AsyncMock(return_value=[
        MCPToolInfo(name="web_search", description="Search", last_validated=datetime.now()),
    ])

    client.call_tool = AsyncMock(return_value={
        "results": ["result1", "result2"],
    })

    return client


@pytest.fixture
def app(mock_mcp_client):
    test_app = FastAPI()
    test_app.include_router(router)
    init_mcp_routes(mock_mcp_client, tool_registry=None)
    return test_app


@pytest.fixture
def client(app):
    return TestClient(app)


class TestListMCPModules:
    def test_list_modules(self, client):
        resp = client.get("/api/v1/mcp/modules")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["total"] == 1
        assert data["data"]["connected"] == 1


class TestListModuleTools:
    def test_list_tools(self, client):
        resp = client.get("/api/v1/mcp/modules/intellicare-superz/tools")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["count"] == 2


class TestRefreshModuleTools:
    def test_refresh(self, client, mock_mcp_client):
        resp = client.post("/api/v1/mcp/modules/intellicare-superz/refresh")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        mock_mcp_client.refresh_tools.assert_awaited_once()


class TestCallMCPTool:
    def test_call_tool(self, client, mock_mcp_client):
        resp = client.post(
            "/api/v1/mcp/tools/intellicare-superz/web_search",
            json={"params": {"query": "DM2 guidelines"}}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["result"]["results"] == ["result1", "result2"]
        mock_mcp_client.call_tool.assert_awaited_once()


class TestListAllTools:
    def test_list_all(self, client):
        resp = client.get("/api/v1/mcp/tools")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["total"] == 2
        # Each tool should have module_name injected
        for tool in data["data"]["tools"]:
            assert "module_name" in tool


class TestMCPNotInitialized:
    def test_503_when_no_client(self):
        test_app = FastAPI()
        test_app.include_router(router)
        init_mcp_routes(None, None)
        c = TestClient(test_app)
        resp = c.get("/api/v1/mcp/modules")
        assert resp.status_code == 503
