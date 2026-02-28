"""Testes para endpoints Oswaldo."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from nise.api.app import app
from nise.services.oswaldo_client import DiagnosticoResponse, AlertaResponse

client = TestClient(app)


@pytest.fixture
def mock_diagnosticos():
    """Fixture com diagnósticos mock."""
    return [
        DiagnosticoResponse(
            paciente_id="pac-123",
            condicao="diabetes",
            classificacao="tipo_2",
            estadiamento="A1",
            data_diagnostico="2024-01-15",
            plano_cuidado_id="plano-456"
        )
    ]


@pytest.fixture
def mock_alertas():
    """Fixture com alertas mock."""
    return [
        AlertaResponse(
            alerta_id="alerta-1",
            tipo="critico",
            mensagem="HbA1c muito elevada",
            data_criacao="2024-02-15",
            status="ativo",
            paciente_id="pac-123"
        )
    ]


def test_health_endpoint():
    """Testa endpoint de health check."""
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "intellicare-nise"


def test_info_endpoint():
    """Testa endpoint de informações do módulo."""
    response = client.get("/api/v1/info")
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "intellicare-nise"
    assert "oswaldo-integration" in data["capabilities"]
    assert "chatbot" in data["capabilities"]


@pytest.mark.asyncio
async def test_get_resumo_paciente_success(mock_diagnosticos, mock_alertas):
    """Testa endpoint de resumo do paciente com sucesso."""
    
    with patch("nise.api.endpoints.oswaldo.OswaldoClient") as MockClient:
        # Setup mock
        mock_instance = MockClient.return_value
        mock_instance.get_diagnosticos = AsyncMock(return_value=mock_diagnosticos)
        mock_instance.get_alertas = AsyncMock(return_value=mock_alertas)
        mock_instance.close = AsyncMock()
        
        with patch("nise.api.endpoints.oswaldo.CacheService") as MockCache:
            mock_cache = MockCache.return_value
            mock_cache.get = AsyncMock(return_value=None)
            mock_cache.set = AsyncMock(return_value=True)
            mock_cache.close = AsyncMock()
            
            # Execute
            response = client.get("/api/v1/oswaldo/paciente/pac-123/resumo")
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["paciente_id"] == "pac-123"
            assert len(data["diagnosticos"]) == 1
            assert data["total_alertas"] == 1


@pytest.mark.asyncio
async def test_get_resumo_paciente_with_cache():
    """Testa endpoint de resumo com cache hit."""
    
    cached_data = {
        "paciente_id": "pac-123",
        "diagnosticos": [],
        "alertas_criticos": [],
        "total_alertas": 0,
        "plano_cuidado_atual": None,
        "risco_framingham": None
    }
    
    with patch("nise.api.endpoints.oswaldo.CacheService") as MockCache:
        mock_cache = MockCache.return_value
        mock_cache.get = AsyncMock(return_value=cached_data)
        mock_cache.close = AsyncMock()
        
        response = client.get("/api/v1/oswaldo/paciente/pac-123/resumo")
        
        assert response.status_code == 200
        data = response.json()
        assert data["paciente_id"] == "pac-123"


@pytest.mark.asyncio
async def test_get_diagnosticos_endpoint(mock_diagnosticos):
    """Testa endpoint de diagnósticos."""
    
    with patch("nise.api.endpoints.oswaldo.OswaldoClient") as MockClient:
        mock_instance = MockClient.return_value
        mock_instance.get_diagnosticos = AsyncMock(return_value=mock_diagnosticos)
        mock_instance.close = AsyncMock()
        
        response = client.get("/api/v1/oswaldo/paciente/pac-123/diagnosticos")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["condicao"] == "diabetes"


@pytest.mark.asyncio
async def test_get_alertas_endpoint(mock_alertas):
    """Testa endpoint de alertas."""
    
    with patch("nise.api.endpoints.oswaldo.OswaldoClient") as MockClient:
        mock_instance = MockClient.return_value
        mock_instance.get_alertas = AsyncMock(return_value=mock_alertas)
        mock_instance.close = AsyncMock()
        
        response = client.get("/api/v1/oswaldo/paciente/pac-123/alertas?status=ativo")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["tipo"] == "critico"

