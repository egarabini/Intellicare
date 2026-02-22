"""Testes para chatbot endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from nise.api.app import app
from nise.services.flowise_client import ChatResponse

client = TestClient(app)


@pytest.fixture
def mock_chat_response():
    """Fixture com resposta mock do chatbot."""
    return ChatResponse(
        text="O paciente pac-123 possui diagnóstico de Diabetes Tipo 2, classificação A1.",
        session_id="session-test-123",
        chatflow_id="dr-nise-default",
        metadata={"source": "oswaldo"}
    )


@pytest.mark.asyncio
async def test_chat_endpoint_success(mock_chat_response):
    """Testa endpoint de chat com sucesso."""
    
    with patch("nise.api.endpoints.chatbot.FlowiseClient") as MockClient:
        # Setup mock
        mock_instance = MockClient.return_value
        mock_instance.chat = AsyncMock(return_value=mock_chat_response)
        mock_instance.close = AsyncMock()
        
        # Execute
        response = client.post(
            "/api/v1/chatbot/chat",
            json={
                "question": "Qual o diagnóstico de diabetes do paciente pac-123?",
                "chatflow_id": "dr-nise-default"
            }
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "text" in data
        assert "session_id" in data
        assert data["chatflow_id"] == "dr-nise-default"


@pytest.mark.asyncio
async def test_chat_endpoint_with_session():
    """Testa endpoint de chat com session_id."""
    
    mock_response = ChatResponse(
        text="Resposta do chatbot",
        session_id="session-abc-123",
        chatflow_id="dr-nise-default"
    )
    
    with patch("nise.api.endpoints.chatbot.FlowiseClient") as MockClient:
        mock_instance = MockClient.return_value
        mock_instance.chat = AsyncMock(return_value=mock_response)
        mock_instance.close = AsyncMock()
        
        response = client.post(
            "/api/v1/chatbot/chat",
            json={
                "question": "Teste",
                "chatflow_id": "dr-nise-default",
                "session_id": "session-abc-123"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "session-abc-123"


@pytest.mark.asyncio
async def test_list_chatflows_endpoint():
    """Testa endpoint de listagem de chatflows."""
    
    mock_chatflows = [
        {
            "id": "dr-nise-default",
            "name": "Dr. Nise - Assistente Médico",
            "description": "Chatbot padrão"
        },
        {
            "id": "dr-nise-advanced",
            "name": "Dr. Nise - Avançado",
            "description": "Chatbot com RAG"
        }
    ]
    
    with patch("nise.api.endpoints.chatbot.FlowiseClient") as MockClient:
        mock_instance = MockClient.return_value
        mock_instance.get_chatflows = AsyncMock(return_value=mock_chatflows)
        mock_instance.close = AsyncMock()
        
        response = client.get("/api/v1/chatbot/chatflows")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["chatflows"]) == 2


@pytest.mark.asyncio
async def test_get_chatflow_endpoint():
    """Testa endpoint de detalhes do chatflow."""
    
    mock_chatflow = {
        "id": "dr-nise-default",
        "name": "Dr. Nise - Assistente Médico",
        "description": "Chatbot padrão",
        "config": {"model": "llama2:7b"}
    }
    
    with patch("nise.api.endpoints.chatbot.FlowiseClient") as MockClient:
        mock_instance = MockClient.return_value
        mock_instance.get_chatflow = AsyncMock(return_value=mock_chatflow)
        mock_instance.close = AsyncMock()
        
        response = client.get("/api/v1/chatbot/chatflows/dr-nise-default")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "dr-nise-default"
        assert data["name"] == "Dr. Nise - Assistente Médico"


@pytest.mark.asyncio
async def test_chatbot_health_endpoint():
    """Testa endpoint de health check do chatbot."""
    
    with patch("nise.api.endpoints.chatbot.FlowiseClient") as MockClient:
        mock_instance = MockClient.return_value
        mock_instance.health_check = AsyncMock(return_value=True)
        mock_instance.close = AsyncMock()
        
        response = client.get("/api/v1/chatbot/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["flowise_available"] is True


@pytest.mark.asyncio
async def test_chatbot_health_endpoint_unhealthy():
    """Testa endpoint de health check quando Flowise está indisponível."""
    
    with patch("nise.api.endpoints.chatbot.FlowiseClient") as MockClient:
        mock_instance = MockClient.return_value
        mock_instance.health_check = AsyncMock(return_value=False)
        mock_instance.close = AsyncMock()
        
        response = client.get("/api/v1/chatbot/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["flowise_available"] is False


@pytest.mark.asyncio
async def test_test_chatbot_endpoint(mock_chat_response):
    """Testa endpoint de teste do chatbot."""
    
    with patch("nise.api.endpoints.chatbot.FlowiseClient") as MockClient:
        mock_instance = MockClient.return_value
        mock_instance.chat = AsyncMock(return_value=mock_chat_response)
        mock_instance.close = AsyncMock()
        
        response = client.post("/api/v1/chatbot/test?paciente_id=pac-123")
        
        assert response.status_code == 200
        data = response.json()
        assert data["paciente_id"] == "pac-123"
        assert data["total_perguntas"] == 3
        assert len(data["resultados"]) == 3

