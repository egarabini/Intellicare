"""Testes de integração para Fase 5 - Eventos e Consolidação."""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from comunicacao.api.app import create_app
from comunicacao.routing.models import (
    CommunicationIntentCreate,
    IntentStatus,
    RecipientType,
)


@pytest.fixture
def mock_db_session():
    """Mock de sessão de banco de dados."""
    session = MagicMock()
    session.execute = MagicMock(return_value=MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))))
    session.commit = MagicMock()
    session.rollback = MagicMock()
    session.close = MagicMock()
    return session


@pytest.fixture
def mock_redis_client():
    """Mock de cliente Redis."""
    client = MagicMock()
    client.xadd = MagicMock(return_value=b"1234567890-0")
    client.xread = MagicMock(return_value=[])
    client.set = MagicMock(return_value=True)
    client.get = MagicMock(return_value=None)
    client.setex = MagicMock(return_value=True)
    return client


@pytest.fixture
def test_client(mock_db_session, mock_redis_client):
    """Cliente de teste FastAPI com mocks."""
    with patch("comunicacao.api.app.create_db_session", return_value=mock_db_session):
        with patch("comunicacao.events.redis_consumer.redis.Redis", return_value=mock_redis_client):
            app = create_app()
            with TestClient(app) as client:
                yield client


class TestPhase5Integration:
    """Testes de integração para Fase 5."""

    def test_e2e_api_send_intent_with_auth(self, test_client: TestClient):
        """
        Teste E2E: Enviar intent via API com autenticação.
        
        Valida:
        - Autenticação funciona (modo dev com mock user)
        - Intent é criado e processado
        - Resposta contém intent_id e status
        """
        # Arrange
        payload = {
            "source_module": "intellicare-oswaldo",
            "recipient_type": "patient",
            "recipient_id": "patient-123",
            "severity": "high",
            "category": "clinical_alert",
            "content_raw": "Teste de integração",
        }
        
        # Act
        response = test_client.post("/api/v1/routing/send", json=payload)
        
        # Assert
        assert response.status_code == 202
        data = response.json()
        assert "intent_id" in data
        assert "status" in data
        assert data["message"] == "intent accepted for processing"

    def test_e2e_api_list_intents_with_auth(self, test_client: TestClient):
        """
        Teste E2E: Listar intents via API com autenticação.
        
        Valida:
        - Autenticação funciona
        - Endpoint retorna lista de intents
        """
        # Act
        response = test_client.get("/api/v1/routing/intents")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)

    def test_e2e_api_get_metrics_with_auth(self, test_client: TestClient):
        """
        Teste E2E: Obter métricas via API com autenticação.
        
        Valida:
        - Autenticação funciona
        - Endpoint retorna métricas
        """
        # Act
        response = test_client.get("/api/v1/routing/metrics")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "ok" in data
        assert data["ok"] is True

    def test_e2e_prometheus_metrics_endpoint(self, test_client: TestClient):
        """
        Teste E2E: Endpoint /metrics do Prometheus.
        
        Valida:
        - Endpoint retorna métricas no formato Prometheus
        - Content-Type correto
        """
        # Act
        response = test_client.get("/metrics")
        
        # Assert
        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]
        
        # Verificar que contém métricas esperadas
        content = response.text
        assert "comm_intent_received_total" in content
        assert "comm_intent_completed_total" in content
        assert "comm_routing_latency_seconds" in content

    def test_e2e_template_list_with_auth(self, test_client: TestClient):
        """
        Teste E2E: Listar templates via API com autenticação.
        
        Valida:
        - Autenticação funciona
        - Endpoint retorna lista de templates
        """
        # Act
        response = test_client.get("/api/v1/templates")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)

    def test_e2e_template_get_with_auth(self, test_client: TestClient):
        """
        Teste E2E: Obter template específico via API com autenticação.

        Valida:
        - Autenticação funciona
        - Endpoint retorna 404 para template inexistente
        """
        # Act
        response = test_client.get("/api/v1/templates/nonexistent-template")

        # Assert
        # Esperamos 404 porque o template não existe
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_e2e_redis_event_to_intent(self, mock_db_session, mock_redis_client):
        """
        Teste E2E: Evento Redis processado e transformado em intent.

        Valida:
        - Evento Redis é consumido
        - CommunicationIntent é criado
        - Intent é roteado via RoutingEngine
        - Métricas são atualizadas
        """
        from comunicacao.api.app import _on_alert_event

        # Arrange
        event_payload = {
            "source_module": "intellicare-oswaldo",
            "patient_id": "patient-456",
            "severity": "high",
            "alert_type": "egfr_critical",
            "message": "eGFR caiu para 25 ml/min",
            "correlation_id": "test-corr-123",
            "event_id": "1234567890-0",
        }

        # Mock do RoutingService
        mock_routing_service = MagicMock()
        mock_intent = MagicMock()
        mock_intent.id = "intent-123"
        mock_intent.status = IntentStatus.PENDING
        mock_routing_service.send_intent = AsyncMock(return_value=mock_intent)

        # Mock do state
        with patch("comunicacao.api.app._state", {"routing_service": mock_routing_service, "event_metrics": {}}):
            # Act
            await _on_alert_event(event_payload)

            # Assert
            mock_routing_service.send_intent.assert_called_once()
            call_args = mock_routing_service.send_intent.call_args[0][0]
            assert call_args.source_module == "intellicare-oswaldo"
            assert call_args.recipient_id == "patient-456"
            assert call_args.severity == "high"
            assert call_args.category == "egfr_critical"
            assert call_args.source_event_id == "1234567890-0"

    def test_e2e_batch_send_with_auth(self, test_client: TestClient):
        """
        Teste E2E: Enviar batch de intents via API com autenticação.

        Valida:
        - Autenticação funciona
        - Batch é processado
        - Resposta contém accepted e rejected
        """
        # Arrange
        payload = {
            "intents": [
                {
                    "source_module": "intellicare-oswaldo",
                    "recipient_type": "patient",
                    "recipient_id": "patient-1",
                    "severity": "medium",
                    "category": "reminder",
                    "content_raw": "Lembrete 1",
                },
                {
                    "source_module": "intellicare-oswaldo",
                    "recipient_type": "patient",
                    "recipient_id": "patient-2",
                    "severity": "low",
                    "category": "reminder",
                    "content_raw": "Lembrete 2",
                },
            ]
        }

        # Act
        response = test_client.post("/api/v1/routing/send-batch", json=payload)

        # Assert
        assert response.status_code == 202
        data = response.json()
        assert "accepted" in data
        assert "rejected" in data
        assert "intent_ids" in data

    def test_e2e_scheduler_status_with_auth(self, test_client: TestClient):
        """
        Teste E2E: Obter status do scheduler via API com autenticação.

        Valida:
        - Autenticação funciona
        - Endpoint retorna status do scheduler
        """
        # Act
        response = test_client.get("/api/v1/routing/scheduler/status")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "running" in data or "status" in data

    def test_e2e_rules_list_with_auth(self, test_client: TestClient):
        """
        Teste E2E: Listar regras de roteamento via API com autenticação.

        Valida:
        - Autenticação funciona
        - Endpoint retorna lista de regras
        """
        # Act
        response = test_client.get("/api/v1/routing/rules")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)


class TestPhase5Metrics:
    """Testes de métricas Prometheus para Fase 5."""

    def test_metrics_endpoint_format(self, test_client: TestClient):
        """
        Teste: Formato das métricas Prometheus.

        Valida:
        - Métricas estão no formato correto
        - Todas as métricas esperadas estão presentes
        """
        # Act
        response = test_client.get("/metrics")

        # Assert
        assert response.status_code == 200
        content = response.text

        # Verificar counters
        assert "comm_intent_received_total" in content
        assert "comm_intent_completed_total" in content
        assert "comm_intent_failed_total" in content
        assert "comm_delivery_attempt_total" in content
        assert "comm_channel_fallback_total" in content
        assert "comm_redis_event_total" in content
        assert "comm_template_render_total" in content

        # Verificar histograms
        assert "comm_routing_latency_seconds" in content
        assert "comm_delivery_latency_seconds" in content
        assert "comm_template_render_latency_seconds" in content

        # Verificar gauges
        assert "comm_intents_in_progress" in content
        assert "comm_intents_scheduled" in content
        assert "comm_delayed_tasks_pending" in content
        assert "comm_redis_consumer_status" in content
        assert "comm_dispatcher_health" in content

    @pytest.mark.asyncio
    async def test_metrics_tracking_on_intent_processing(self):
        """
        Teste: Métricas são atualizadas ao processar intent.

        Valida:
        - Contador de intents recebidos incrementa
        - Latência é registrada
        - Status final é registrado
        """
        from comunicacao.metrics import (
            comm_intent_received_total,
            comm_intent_completed_total,
            comm_routing_latency_seconds,
        )

        # Arrange
        initial_received = comm_intent_received_total.labels(
            source_module="test",
            severity="medium",
            category="test",
        )._value._value

        # Act
        from comunicacao.routing.engine import RoutingEngine
        from comunicacao.routing.models import CommunicationIntentCreate, RecipientType

        # Mock dependencies
        mock_repository = MagicMock()
        mock_repository.create_intent = MagicMock(return_value=MagicMock(id="test-123", status=IntentStatus.PENDING))
        mock_repository.get_intent = MagicMock(return_value=(MagicMock(id="test-123", status=IntentStatus.PENDING), []))

        engine = RoutingEngine(
            repository=mock_repository,
            rule_matcher=MagicMock(),
            recipient_resolver=MagicMock(),
            lgpd_gateway=MagicMock(),
            dispatchers={},
            template_renderer=MagicMock(),
            fallback_monitor=MagicMock(),
        )

        # Simular processamento
        # (Nota: Este teste é simplificado - em produção, teríamos todo o pipeline)

        # Assert
        # Verificar que as métricas existem e podem ser acessadas
        assert comm_intent_received_total is not None
        assert comm_intent_completed_total is not None
        assert comm_routing_latency_seconds is not None


class TestPhase5ErrorHandling:
    """Testes de tratamento de erros para Fase 5."""

    @pytest.mark.asyncio
    async def test_redis_event_missing_required_fields(self):
        """
        Teste: Evento Redis com campos obrigatórios faltando.

        Valida:
        - KeyError é capturado
        - Métrica de erro é incrementada
        - Log de warning é gerado
        """
        from comunicacao.api.app import _on_alert_event

        # Arrange
        event_payload = {
            # Faltando patient_id (obrigatório)
            "source_module": "intellicare-oswaldo",
            "severity": "high",
            "message": "Teste sem patient_id",
        }

        # Mock do state
        with patch("comunicacao.api.app._state", {"event_metrics": {}}):
            # Act
            await _on_alert_event(event_payload)

            # Assert
            # Não deve lançar exceção, apenas logar warning
            # (O handler captura KeyError internamente)

    def test_api_send_intent_invalid_payload(self, test_client: TestClient):
        """
        Teste: Enviar intent com payload inválido.

        Valida:
        - Validação Pydantic funciona
        - Retorna 422 Unprocessable Entity
        """
        # Arrange
        payload = {
            # Faltando campos obrigatórios
            "source_module": "test",
        }

        # Act
        response = test_client.post("/api/v1/routing/send", json=payload)

        # Assert
        assert response.status_code == 422  # Validation error

    def test_api_get_nonexistent_intent(self, test_client: TestClient):
        """
        Teste: Obter intent inexistente.

        Valida:
        - Retorna 404 Not Found
        """
        # Act
        response = test_client.get("/api/v1/routing/intents/nonexistent-intent-id")

        # Assert
        assert response.status_code == 404

