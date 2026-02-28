"""Testes para OswaldoClient."""

import pytest
from unittest.mock import AsyncMock, patch
import httpx

from nise.services.oswaldo_client import (
    OswaldoClient,
    DiagnosticoResponse,
    AlertaResponse,
    PlanoCuidadoResponse
)


@pytest.fixture
def oswaldo_client():
    """Fixture para OswaldoClient."""
    return OswaldoClient(base_url="http://localhost:8002")


@pytest.mark.asyncio
async def test_get_diagnosticos_success(oswaldo_client):
    """Testa busca de diagnósticos com sucesso."""
    
    # Mock response
    mock_data = [
        {
            "paciente_id": "pac-123",
            "condicao": "diabetes",
            "classificacao": "tipo_2",
            "estadiamento": "A1",
            "data_diagnostico": "2024-01-15",
            "plano_cuidado_id": "plano-456"
        }
    ]
    
    with patch.object(oswaldo_client.client, 'get') as mock_get:
        mock_response = AsyncMock()
        mock_response.json.return_value = mock_data
        mock_response.raise_for_status = AsyncMock()
        mock_get.return_value = mock_response
        
        # Execute
        result = await oswaldo_client.get_diagnosticos("pac-123")
        
        # Assert
        assert len(result) == 1
        assert isinstance(result[0], DiagnosticoResponse)
        assert result[0].paciente_id == "pac-123"
        assert result[0].condicao == "diabetes"
        assert result[0].classificacao == "tipo_2"


@pytest.mark.asyncio
async def test_get_diagnosticos_empty(oswaldo_client):
    """Testa busca de diagnósticos sem resultados."""
    
    with patch.object(oswaldo_client.client, 'get') as mock_get:
        mock_response = AsyncMock()
        mock_response.json.return_value = []
        mock_response.raise_for_status = AsyncMock()
        mock_get.return_value = mock_response
        
        result = await oswaldo_client.get_diagnosticos("pac-999")
        
        assert len(result) == 0


@pytest.mark.asyncio
async def test_get_alertas_success(oswaldo_client):
    """Testa busca de alertas com sucesso."""
    
    mock_data = [
        {
            "alerta_id": "alerta-1",
            "tipo": "critico",
            "mensagem": "HbA1c muito elevada",
            "data_criacao": "2024-02-15",
            "status": "ativo",
            "paciente_id": "pac-123"
        }
    ]
    
    with patch.object(oswaldo_client.client, 'get') as mock_get:
        mock_response = AsyncMock()
        mock_response.json.return_value = mock_data
        mock_response.raise_for_status = AsyncMock()
        mock_get.return_value = mock_response
        
        result = await oswaldo_client.get_alertas("pac-123", status="ativo")
        
        assert len(result) == 1
        assert isinstance(result[0], AlertaResponse)
        assert result[0].tipo == "critico"
        assert result[0].status == "ativo"


@pytest.mark.asyncio
async def test_get_plano_cuidado_success(oswaldo_client):
    """Testa busca de plano de cuidado com sucesso."""
    
    mock_data = {
        "plano_id": "plano-456",
        "paciente_id": "pac-123",
        "condicao": "diabetes",
        "objetivos": ["Controlar glicemia", "Reduzir HbA1c"],
        "intervencoes": [{"tipo": "medicacao", "descricao": "Metformina 850mg"}],
        "metas": [{"parametro": "HbA1c", "valor_alvo": 7.0}],
        "data_criacao": "2024-01-15",
        "status": "ativo"
    }
    
    with patch.object(oswaldo_client.client, 'get') as mock_get:
        mock_response = AsyncMock()
        mock_response.json.return_value = mock_data
        mock_response.raise_for_status = AsyncMock()
        mock_get.return_value = mock_response
        
        result = await oswaldo_client.get_plano_cuidado("plano-456")
        
        assert isinstance(result, PlanoCuidadoResponse)
        assert result.plano_id == "plano-456"
        assert result.condicao == "diabetes"
        assert len(result.objetivos) == 2


@pytest.mark.asyncio
async def test_get_diagnosticos_http_error(oswaldo_client):
    """Testa erro HTTP ao buscar diagnósticos."""
    
    with patch.object(oswaldo_client.client, 'get') as mock_get:
        mock_response = AsyncMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "404 Not Found",
            request=AsyncMock(),
            response=AsyncMock()
        )
        mock_get.return_value = mock_response
        
        with pytest.raises(httpx.HTTPStatusError):
            await oswaldo_client.get_diagnosticos("pac-999")


@pytest.mark.asyncio
async def test_close_client(oswaldo_client):
    """Testa fechamento do cliente."""
    
    with patch.object(oswaldo_client.client, 'aclose') as mock_close:
        await oswaldo_client.close()
        mock_close.assert_called_once()


@pytest.mark.asyncio
async def test_client_initialization():
    """Testa inicialização do cliente com parâmetros customizados."""
    
    client = OswaldoClient(
        base_url="http://custom:9000",
        timeout=20.0
    )
    
    assert client.base_url == "http://custom:9000"
    assert client.timeout == 20.0

