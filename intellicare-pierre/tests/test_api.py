"""Testes da API FastAPI — 3 testes."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from pierre.api.app import app


@pytest.fixture
def client():
    """TestClient com server mockado."""
    return TestClient(app)


def test_api_info(client):
    """GET /api/v1/info retorna metadata do modulo."""
    response = client.get("/api/v1/info")
    assert response.status_code == 200
    data = response.json()
    assert data["module"] == "intellicare-pierre"
    assert data["agent"] == "PIERRE (Pierre Curie)"
    assert data["tools_count"] == 6
    assert "web_search" in data["tools"]
    assert "search_medical_literature" in data["tools"]


def test_api_health_no_server(client):
    """GET /api/v1/health sem server retorna 503."""
    # Em test mode, _mcp_server pode nao estar inicializado
    # O lifespan nao roda no TestClient por padrao
    from pierre.api import app as app_module
    original = app_module._mcp_server
    app_module._mcp_server = None
    try:
        response = client.get("/api/v1/health")
        assert response.status_code == 503
    finally:
        app_module._mcp_server = original


def test_api_call_tool_no_name(client):
    """POST /api/v1/mcp/call sem name retorna 400."""
    from pierre.api import app as app_module
    from unittest.mock import MagicMock
    # Configurar um servidor mock para evitar 503
    mock_server = MagicMock()
    original = app_module._mcp_server
    app_module._mcp_server = mock_server
    try:
        response = client.post("/api/v1/mcp/call", json={"arguments": {}})
        assert response.status_code == 400
        assert "name" in response.json()["error"].lower()
    finally:
        app_module._mcp_server = original
