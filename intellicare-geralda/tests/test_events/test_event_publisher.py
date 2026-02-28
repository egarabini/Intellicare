"""Testes para EventPublisher."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from geralda.events.event_publisher import EventPublisher
from geralda.events.event_types import IntelliCareEvent


class TestEventPublisher:
    """Testes para publicador de eventos."""

    @pytest.fixture
    def mock_redis(self):
        """Mock de cliente Redis."""
        redis = AsyncMock()
        redis.xadd.return_value = "stream-id-123"
        return redis

    @pytest.fixture
    def mock_http_client(self):
        """Mock de cliente HTTP."""
        client = AsyncMock()
        client.post.return_value = MagicMock(status_code=200)
        return client

    @pytest.fixture
    def publisher(self, mock_redis, mock_http_client):
        """Cria publicador com mocks."""
        return EventPublisher(
            redis_client=mock_redis,
            http_client=mock_http_client,
        )

    @pytest.fixture
    def sample_event(self):
        """Cria evento de exemplo."""
        return IntelliCareEvent(
            event_type="care.plan_created",
            patient_id="pac-001",
            payload={"plan_id": "plan-123"},
        )

    @pytest.mark.asyncio
    async def test_publish_to_redis(self, publisher, mock_redis, sample_event):
        """Testa publicar no Redis."""
        await publisher.publish(sample_event)

        # Deve chamar xadd do Redis
        mock_redis.xadd.assert_called_once()

        # Verificar nome do stream
        call_args = mock_redis.xadd.call_args
        stream_name = call_args[0][0]

        assert "care" in stream_name  # Stream por categoria

    @pytest.mark.asyncio
    async def test_publish_clinical_event(self, publisher, mock_redis):
        """Testa publicar evento clínico."""
        event = IntelliCareEvent(
            event_type="clinical.condition_diagnosed",
            patient_id="pac-002",
            payload={"condition": "N18.3"},
        )

        await publisher.publish(event)

        # Deve publicar em stream clínico
        call_args = mock_redis.xadd.call_args
        stream_name = call_args[0][0]

        assert "clinical" in stream_name

    @pytest.mark.asyncio
    async def test_publish_digital_event(self, publisher, mock_redis):
        """Testa publicar evento digital."""
        event = IntelliCareEvent(
            event_type="digital.message_received",
            patient_id="pac-003",
            payload={"message": "Olá"},
        )

        await publisher.publish(event)

        call_args = mock_redis.xadd.call_args
        stream_name = call_args[0][0]

        assert "digital" in stream_name

    @pytest.mark.asyncio
    async def test_publish_without_redis(self, sample_event):
        """Testa publicar sem Redis."""
        publisher = EventPublisher(redis_client=None, http_client=None)

        # Não deve levantar erro
        await publisher.publish(sample_event)

    @pytest.mark.asyncio
    async def test_publish_to_wanda_important_event(self, publisher, mock_http_client):
        """Testa notificar Wanda para evento importante."""
        event = IntelliCareEvent(
            event_type="clinical.condition_worsened",
            patient_id="pac-004",
            payload={"severity": "high"},
        )

        wanda_url = "http://wanda:8004/api/v1/events"

        await publisher.publish_to_wanda(event, wanda_url=wanda_url)

        # Deve fazer POST para Wanda
        mock_http_client.post.assert_called_once()

        # Verificar URL
        call_args = mock_http_client.post.call_args
        assert wanda_url in call_args[0][0]

    @pytest.mark.asyncio
    async def test_publish_to_wanda_skips_low_priority(self, publisher, mock_http_client):
        """Testa que eventos de baixa prioridade não notificam Wanda."""
        event = IntelliCareEvent(
            event_type="care.reminder_sent",
            patient_id="pac-005",
            payload={"reminder_id": "rem-123"},
        )

        wanda_url = "http://wanda:8004/api/v1/events"

        await publisher.publish_to_wanda(event, wanda_url=wanda_url)

        # Não deve notificar Wanda
        mock_http_client.post.assert_not_called()

    @pytest.mark.asyncio
    async def test_publish_to_wanda_without_http_client(self, sample_event):
        """Testa notificar Wanda sem cliente HTTP."""
        publisher = EventPublisher(redis_client=None, http_client=None)

        # Não deve levantar erro
        await publisher.publish_to_wanda(sample_event, wanda_url="http://wanda/events")

    @pytest.mark.asyncio
    async def test_publish_to_wanda_handles_error(self, publisher, mock_http_client):
        """Testa tratamento de erro ao notificar Wanda."""
        event = IntelliCareEvent(
            event_type="clinical.condition_worsened",
            patient_id="pac-006",
            payload={},
        )

        mock_http_client.post.side_effect = Exception("Connection error")

        # Não deve levantar erro
        await publisher.publish_to_wanda(event, wanda_url="http://wanda/events")


class TestEventPublisherStreams:
    """Testes para streams do Redis."""

    @pytest.mark.asyncio
    async def test_determines_stream_from_event_type(self):
        """Testa determinar stream a partir do tipo de evento."""
        publisher = EventPublisher(redis_client=AsyncMock(), http_client=None)

        mappings = {
            "care.plan_created": "intellicare:events:care",
            "clinical.exam_result": "intellicare:events:clinical",
            "digital.message_sent": "intellicare:events:digital",
            "operational.consultation_scheduled": "intellicare:events:operational",
        }

        for event_type, expected_stream in mappings.items():
            event = IntelliCareEvent(
                event_type=event_type,
                patient_id="pac-001",
                payload={},
            )

            stream = publisher._get_stream_name(event)
            assert stream == expected_stream

    @pytest.mark.asyncio
    async def test_unknown_event_type_uses_default_stream(self):
        """Testa que tipo desconhecido usa stream padrão."""
        publisher = EventPublisher(redis_client=AsyncMock(), http_client=None)

        event = IntelliCareEvent(
            event_type="unknown.event",
            patient_id="pac-001",
            payload={},
        )

        stream = publisher._get_stream_name(event)

        # Deve usar stream padrão
        assert "events" in stream


class TestEventPublisherPayloadFormat:
    """Testes para formato do payload."""

    @pytest.mark.asyncio
    async def test_publish_serializes_event_correctly(self):
        """Testa que evento é serializado corretamente."""
        mock_redis = AsyncMock()
        publisher = EventPublisher(redis_client=mock_redis, http_client=None)

        event = IntelliCareEvent(
            event_type="test.event",
            patient_id="pac-001",
            payload={"key": "value"},
            timestamp=datetime(2026, 2, 24, 12, 0, 0, tzinfo=timezone.utc),
        )

        await publisher.publish(event)

        # Verificar dados enviados ao Redis
        call_args = mock_redis.xadd.call_args
        event_data = call_args[0][1]

        assert "event_type" in event_data
        assert "patient_id" in event_data
        assert "timestamp" in event_data


class TestEventPublisherWandaIntegration:
    """Testes para integração com Wanda."""

    @pytest.mark.asyncio
    async def test_wanda_payload_format(self):
        """Testa formato do payload enviado ao Wanda."""
        mock_http = AsyncMock()
        mock_http.post.return_value = MagicMock(status_code=200)

        publisher = EventPublisher(redis_client=None, http_client=mock_http)

        event = IntelliCareEvent(
            event_type="clinical.condition_diagnosed",
            patient_id="pac-001",
            payload={"condition": "N18.3"},
        )

        await publisher.publish_to_wanda(event, wanda_url="http://wanda/events")

        # Verificar payload enviado
        call_args = mock_http.post.call_args
        sent_data = call_args[1]["json"]  # payload json

        assert "event_type" in sent_data
        assert "patient_id" in sent_data
        assert sent_data["patient_id"] == "pac-001"

    @pytest.mark.asyncio
    async def test_wanda_timeout(self):
        """Testa timeout ao notificar Wanda."""
        import asyncio

        mock_http = AsyncMock()
        mock_http.post.side_effect = asyncio.TimeoutError()

        publisher = EventPublisher(redis_client=None, http_client=mock_http)

        event = IntelliCareEvent(
            event_type="clinical.condition_diagnosed",
            patient_id="pac-001",
            payload={},
        )

        # Não deve levantar erro
        await publisher.publish_to_wanda(event, wanda_url="http://wanda/events")

    @pytest.mark.asyncio
    async def test_wanda_retry_on_failure(self):
        """Testa retry em caso de falha."""
        mock_http = AsyncMock()
        mock_http.post.side_effect = [Exception("Fail"), MagicMock(status_code=200)]

        publisher = EventPublisher(
            redis_client=None,
            http_client=mock_http,
            wanda_max_retries=2,
        )

        event = IntelliCareEvent(
            event_type="clinical.condition_diagnosed",
            patient_id="pac-001",
            payload={},
        )

        # Deve tentar novamente
        await publisher.publish_to_wanda(event, wanda_url="http://wanda/events")

        assert mock_http.post.call_count >= 1


class TestEventPublisherEdgeCases:
    """Testes de casos extremos."""

    @pytest.mark.asyncio
    async def test_publish_event_with_large_payload(self):
        """Testa publicar evento com payload grande."""
        mock_redis = AsyncMock()
        publisher = EventPublisher(redis_client=mock_redis, http_client=None)

        large_payload = {"data": "x" * 10000}

        event = IntelliCareEvent(
            event_type="test.event",
            patient_id="pac-001",
            payload=large_payload,
        )

        await publisher.publish(event)

        # Deve publicar mesmo assim
        mock_redis.xadd.assert_called_once()

    @pytest.mark.asyncio
    async def test_publish_event_with_special_characters(self):
        """Testa publicar evento com caracteres especiais."""
        mock_redis = AsyncMock()
        publisher = EventPublisher(redis_client=mock_redis, http_client=None)

        event = IntelliCareEvent(
            event_type="test.event",
            patient_id="pac-001",
            payload={"message": "Texto com @#$% e emojis 😊"},
        )

        # Não deve levantar erro
        await publisher.publish(event)

    @pytest.mark.asyncio
    async def test_concurrent_publish(self):
        """Testa publicação concorrente."""
        import asyncio

        mock_redis = AsyncMock()
        publisher = EventPublisher(redis_client=mock_redis, http_client=None)

        events = [
            IntelliCareEvent(
                event_type="test.event",
                patient_id=f"pac-{i:03d}",
                payload={},
            )
            for i in range(10)
        ]

        # Publicar em paralelo
        tasks = [publisher.publish(event) for event in events]

        await asyncio.gather(*tasks)

        # Todas devem ter sido publicadas
        assert mock_redis.xadd.call_count == 10
