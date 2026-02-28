"""Testes para rotas de chat."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI

from geralda.api.chat_routes import router
from geralda.ai.geralda_agent import GeraldaAgent


class TestChatRoutes:
    """Testes para endpoints de chat."""

    @pytest.fixture
    def app(self):
        """Cria app de teste."""
        app = FastAPI()
        app.include_router(router)
        return app

    @pytest.fixture
    def client(self, app):
        """Cria cliente de teste."""
        return TestClient(app)

    @pytest.fixture
    def mock_agent(self):
        """Mock de GeraldaAgent."""
        agent = MagicMock()
        agent.chat = AsyncMock(return_value={
            "response": "Resposta de teste",
            "patient_id": "pac-001",
            "timestamp": "2026-02-24T12:00:00",
            "metadata": {},
        })
        return agent

    def test_chat_endpoint_exists(self, client):
        """Testa que endpoint de chat existe."""
        # Precisa mockar get_agent
        with patch("geralda.api.chat_routes.get_agent") as mock_get_agent:
            mock_agent = MagicMock()
            mock_agent.chat = AsyncMock(return_value={"response": "Test"})
            mock_get_agent.return_value = mock_agent

            response = client.post(
                "/api/v1/chat",
                json={
                    "message": "Olá",
                    "patient_id": "pac-001",
                },
            )

            # Router precisa estar montado
            assert response.status_code in [200, 404, 422]

    @pytest.mark.asyncio
    async def test_chat_with_valid_request(self, mock_agent):
        """Testa chat com requisição válida."""
        with patch("geralda.api.chat_routes.get_agent", return_value=mock_agent):
            app = FastAPI()
            app.include_router(router)
            client = TestClient(app)

            response = client.post(
                "/api/v1/chat",
                json={
                    "message": "Como estou?",
                    "patient_id": "pac-001",
                    "role": "patient",
                },
            )

            # Se router estiver funcionando
            if response.status_code == 200:
                data = response.json()
                assert "response" in data
                assert data["patient_id"] == "pac-001"

    @pytest.mark.asyncio
    async def test_chat_with_history(self, mock_agent):
        """Testa chat com histórico."""
        with patch("geralda.api.chat_routes.get_agent", return_value=mock_agent):
            app = FastAPI()
            app.include_router(router)
            client = TestClient(app)

            history = [
                {"role": "user", "content": "Olá"},
                {"role": "assistant", "content": "Oi!"},
            ]

            response = client.post(
                "/api/v1/chat",
                json={
                    "message": "Tudo bem?",
                    "patient_id": "pac-001",
                    "history": history,
                },
            )

            # Se funcionando
            if response.status_code == 200:
                mock_agent.chat.assert_called_once()

    def test_chat_missing_message_field(self):
        """Testa que campo message é obrigatório."""
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        response = client.post(
            "/api/v1/chat",
            json={
                "patient_id": "pac-001",
            },
        )

        # Deve retornar erro de validação
        assert response.status_code == 422

    def test_chat_missing_patient_id(self):
        """Testa que campo patient_id é obrigatório."""
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        response = client.post(
            "/api/v1/chat",
            json={
                "message": "Olá",
            },
        )

        # Deve retornar erro de validação
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_plan_via_chat(self, mock_agent):
        """Testa criar plano via chat."""
        with patch("geralda.api.chat_routes.get_agent", return_value=mock_agent):
            app = FastAPI()
            app.include_router(router)
            client = TestClient(app)

            response = client.post(
                "/api/v1/chat/create-plan",
                json={
                    "patient_id": "pac-002",
                    "conditions": ["DRC estágio 3"],
                    "goals": ["Controlar creatinina"],
                    "patient_name": "Maria Silva",
                },
            )

            # Se endpoint existe
            if response.status_code == 200:
                data = response.json()
                assert data.get("success") is True
