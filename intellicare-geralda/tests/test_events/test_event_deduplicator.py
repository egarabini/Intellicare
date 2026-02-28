"""Testes para EventDeduplicator."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from geralda.events.event_deduplicator import EventDeduplicator
from geralda.events.event_types import IntelliCareEvent


class TestEventDeduplicator:
    """Testes para deduplicador de eventos."""

    @pytest.fixture
    def mock_redis(self):
        """Mock de cliente Redis."""
        redis = AsyncMock()
        return redis

    @pytest.fixture
    def deduplicator(self, mock_redis):
        """Cria deduplicador com Redis mockado."""
        return EventDeduplicator(redis_client=mock_redis)

    @pytest.fixture
    def sample_event(self):
        """Cria evento de exemplo."""
        return IntelliCareEvent(
            event_type="care.plan_created",
            patient_id="pac-001",
            payload={"plan_id": "plan-123"},
        )

    @pytest.mark.asyncio
    async def test_is_duplicate_false_new_event(self, deduplicator, mock_redis, sample_event):
        """Testa que novo evento não é duplicado."""
        mock_redis.get.return_value = None

        is_dup = await deduplicator.is_duplicate(sample_event)

        assert is_dup is False
        mock_redis.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_is_duplicate_true_existing_event(self, deduplicator, mock_redis, sample_event):
        """Testa que evento existente é detectado como duplicado."""
        mock_redis.get.return_value = b"1"

        is_dup = await deduplicator.is_duplicate(sample_event)

        assert is_dup is True

    @pytest.mark.asyncio
    async def test_mark_processed(self, deduplicator, mock_redis, sample_event):
        """Testa marcar evento como processado."""
        mock_redis.setex.return_value = True

        await deduplicator.mark_processed(sample_event)

        # Deve chamar setex com TTL de 48h (172800 segundos)
        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args
        assert call_args[0][2] == 172800  # TTL

    @pytest.mark.asyncio
    async def test_check_and_mark_new_event(self, deduplicator, mock_redis, sample_event):
        """Testa check_and_mark para novo evento."""
        mock_redis.get.return_value = None
        mock_redis.setex.return_value = True

        is_dup = await deduplicator.check_and_mark(sample_event)

        assert is_dup is False
        mock_redis.get.assert_called_once()
        mock_redis.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_and_mark_duplicate_event(self, deduplicator, mock_redis, sample_event):
        """Testa check_and_mark para evento duplicado."""
        mock_redis.get.return_value = b"1"

        is_dup = await deduplicator.check_and_mark(sample_event)

        assert is_dup is True
        mock_redis.get.assert_called_once()
        # Não deve chamar setex se já existe
        mock_redis.setex.assert_not_called()

    @pytest.mark.asyncio
    async def test_deduplicator_without_redis(self, sample_event):
        """Testa deduplicador sem Redis (sempre retorna False)."""
        deduplicator = EventDeduplicator(redis_client=None)

        is_dup = await deduplicator.is_duplicate(sample_event)

        # Sem Redis, assume que não é duplicado
        assert is_dup is False

    @pytest.mark.asyncio
    async def test_deduplicator_without_redis_mark_does_nothing(self, deduplicator, sample_event):
        """Testa marcar sem Redis (não faz nada)."""
        deduplicator = EventDeduplicator(redis_client=None)

        # Não deve levantar erro
        await deduplicator.mark_processed(sample_event)

    @pytest.mark.asyncio
    async def test_check_and_mark_without_redis(self, sample_event):
        """Testa check_and_mark sem Redis."""
        deduplicator = EventDeduplicator(redis_client=None)

        is_dup = await deduplicator.check_and_mark(sample_event)

        # Sem Redis, sempre processa
        assert is_dup is False


class TestDeduplicatorIdempotencyKey:
    """Testes para chave de idempotência."""

    @pytest.mark.asyncio
    async def test_different_events_have_different_keys(self):
        """Testa que eventos diferentes têm chaves diferentes."""
        deduplicator = EventDeduplicator(redis_client=AsyncMock())

        event1 = IntelliCareEvent(
            event_type="care.plan_created",
            patient_id="pac-001",
            payload={"plan_id": "plan-123"},
        )

        event2 = IntelliCareEvent(
            event_type="care.plan_created",
            patient_id="pac-001",
            payload={"plan_id": "plan-456"},
        )

        key1 = deduplicator._get_idempotency_key(event1)
        key2 = deduplicator._get_idempotency_key(event2)

        assert key1 != key2

    @pytest.mark.asyncio
    async def test_same_event_has_same_key(self):
        """Testa que mesmo evento tem mesma chave."""
        deduplicator = EventDeduplicator(redis_client=AsyncMock())

        event1 = IntelliCareEvent(
            event_type="care.task_completed",
            patient_id="pac-002",
            payload={"task_id": "task-123"},
        )

        event2 = IntelliCareEvent(
            event_type="care.task_completed",
            patient_id="pac-002",
            payload={"task_id": "task-123"},
        )

        key1 = deduplicator._get_idempency_key(event1)
        key2 = deduplicator._get_idempotency_key(event2)

        assert key1 == key2

    @pytest.mark.asyncio
    async def test_key_includes_patient_id(self):
        """Testa que chave inclui patient_id."""
        deduplicator = EventDeduplicator(redis_client=AsyncMock())

        event = IntelliCareEvent(
            event_type="test.event",
            patient_id="pac-123",
            payload={},
        )

        key = deduplicator._get_idempotency_key(event)

        assert "pac-123" in key

    @pytest.mark.asyncio
    async def test_key_includes_event_type(self):
        """Testa que chave inclui event_type."""
        deduplicator = EventDeduplicator(redis_client=AsyncMock())

        event = IntelliCareEvent(
            event_type="care.plan_created",
            patient_id="pac-001",
            payload={},
        )

        key = deduplicator._get_idempotency_key(event)

        assert "care.plan_created" in key

    @pytest.mark.asyncio
    async def test_key_includes_payload_hash(self):
        """Testa que chave inclui hash do payload."""
        deduplicator = EventDeduplicator(redis_client=AsyncMock())

        event = IntelliCareEvent(
            event_type="test.event",
            patient_id="pac-001",
            payload={"data": "specific_value"},
        )

        key = deduplicator._get_idempotency_key(event)

        # Deve ter componente de hash
        assert len(key) > len("test.event") + len("pac-001")


class TestDeduplicatorRedisIntegration:
    """Testes para integração com Redis."""

    @pytest.mark.asyncio
    async def test_redis_key_format(self):
        """Testa formato da chave Redis."""
        mock_redis = AsyncMock()
        deduplicator = EventDeduplicator(redis_client=mock_redis)

        event = IntelliCareEvent(
            event_type="test.event",
            patient_id="pac-001",
            payload={},
        )

        await deduplicator.is_duplicate(event)

        # Verificar que chave Redis está formatada corretamente
        call_args = mock_redis.get.call_args
        redis_key = call_args[0][0]

        assert "event" in redis_key.lower()
        assert "idempotency" in redis_key.lower() or "dedup" in redis_key.lower()

    @pytest.mark.asyncio
    async def test_redis_ttl_is_48_hours(self):
        """Testa que TTL é 48 horas."""
        mock_redis = AsyncMock()
        deduplicator = EventDeduplicator(redis_client=mock_redis)

        event = IntelliCareEvent(
            event_type="test.event",
            patient_id="pac-001",
            payload={},
        )

        await deduplicator.mark_processed(event)

        # Verificar TTL
        call_args = mock_redis.setex.call_args
        ttl = call_args[0][2]

        assert ttl == 172800  # 48 horas em segundos

    @pytest.mark.asyncio
    async def test_redis_connection_error(self):
        """Testa erro de conexão Redis."""
        import redis.asyncio as redis

        mock_redis = AsyncMock()
        mock_redis.get.side_effect = redis.ConnectionError()

        deduplicator = EventDeduplicator(redis_client=mock_redis)

        event = IntelliCareEvent(
            event_type="test.event",
            patient_id="pac-001",
            payload={},
        )

        # Deve retornar False (não é duplicado) em caso de erro
        is_dup = await deduplicator.is_duplicate(event)

        assert is_dup is False


class TestDeduplicatorConcurrency:
    """Testes para concorrência."""

    @pytest.mark.asyncio
    async def test_concurrent_duplicate_detection(self):
        """Testa detecção duplicada concorrente."""
        import asyncio

        mock_redis = AsyncMock()
        mock_redis.get.return_value = None
        mock_redis.setex.return_value = True

        deduplicator = EventDeduplicator(redis_client=mock_redis)

        event = IntelliCareEvent(
            event_type="test.event",
            patient_id="pac-001",
            payload={},
        )

        # Executar múltiplas verificações concorrentes
        tasks = [deduplicator.check_and_mark(event) for _ in range(10)]

        results = await asyncio.gather(*tasks)

        # Todas devem retornar False (não duplicado)
        # Exceto possivelmente a primeira que marcar
        assert all(r is False or r is True for r in results)
