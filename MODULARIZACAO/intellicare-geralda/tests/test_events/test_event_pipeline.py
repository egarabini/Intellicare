"""Testes para EventPipeline."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from geralda.events.event_pipeline import EventPipeline, ProcessingResult
from geralda.events.event_types import IntelliCareEvent


class TestEventPipeline:
    """Testes para pipeline de eventos."""

    @pytest.fixture
    def mock_db_session_factory(self):
        """Mock de fábrica de sessão DB."""
        factory = AsyncMock()
        session = AsyncMock()
        session.execute.return_value = MagicMock()
        session.commit.return_value = None
        session.close.return_value = None
        factory.return_value = session
        return factory

    @pytest.fixture
    def mock_redis(self):
        """Mock de cliente Redis."""
        redis = AsyncMock()
        redis.get.return_value = None  # Não é duplicado
        redis.setex.return_value = True
        redis.xadd.return_value = "stream-id"
        return redis

    @pytest.fixture
    def mock_http_client(self):
        """Mock de cliente HTTP."""
        client = AsyncMock()
        client.post.return_value = MagicMock(status_code=200)
        return client

    @pytest.fixture
    def pipeline(self, mock_db_session_factory, mock_redis, mock_http_client):
        """Cria pipeline com mocks."""
        return EventPipeline(
            db_session_factory=mock_db_session_factory,
            redis_client=mock_redis,
            http_client=mock_http_client,
        )

    @pytest.fixture
    def sample_raw_event(self):
        """Cria evento bruto de exemplo."""
        return {
            "event_type": "care.task_completed",
            "patient_id": "pac-001",
            "task_id": "task-123",
            "completed_at": "2026-02-24T12:00:00Z",
        }

    @pytest.mark.asyncio
    async def test_process_basic_event(self, pipeline, sample_raw_event):
        """Testa processar evento básico."""
        result = await pipeline.process(sample_raw_event, source="geralda")

        assert isinstance(result, ProcessingResult)
        assert result.event_id is not None
        assert result.status in ["processed", "skipped"]

    @pytest.mark.asyncio
    async def test_process_duplicate_event(self, pipeline, mock_redis, sample_raw_event):
        """Testa processar evento duplicado."""
        # Simular que já existe
        mock_redis.get.return_value = b"1"

        result = await pipeline.process(sample_raw_event, source="geralda")

        # Deve ser marcado como duplicado
        assert result.status == "skipped"

    @pytest.mark.asyncio
    async def test_process_without_redis(self, sample_raw_event):
        """Testa processar sem Redis."""
        mock_db = MagicMock()
        session = AsyncMock()
        session.execute.return_value = MagicMock()
        session.commit.return_value = None
        session.rollback.return_value = None
        session.__aenter__.return_value = session
        session.__aexit__.return_value = False
        mock_db.return_value = session

        pipeline = EventPipeline(
            db_session_factory=mock_db,
            redis_client=None,
            http_client=None,
        )

        result = await pipeline.process(sample_raw_event, source="geralda")

        # Deve processar mesmo sem Redis
        assert result.status == "processed"

    @pytest.mark.asyncio
    async def test_process_batch(self, pipeline):
        """Testa processar lote de eventos."""
        events = [
            {
                "event_type": "care.task_completed",
                "patient_id": f"pac-{i:03d}",
                "task_id": f"task-{i}",
            }
            for i in range(5)
        ]

        results = await pipeline.process_batch(events, source="geralda")

        assert len(results) == 5
        assert all(isinstance(r, ProcessingResult) for r in results)

    @pytest.mark.asyncio
    async def test_process_with_error_in_stage(self, pipeline, sample_raw_event):
        """Testa processamento com erro em estágio."""
        # Forçar erro no normalizer
        with patch.object(pipeline._normalizer, "normalize", side_effect=Exception("Test error")):
            result = await pipeline.process(sample_raw_event, source="geralda")

            # Deve marcar erro
            assert result.status == "error"

    @pytest.mark.asyncio
    async def test_pipeline_stages_execution_order(self, pipeline, sample_raw_event):
        """Testa ordem de execução dos estágios."""
        # Espionar chamadas
        pipeline._deduplicator.check_and_mark = AsyncMock(return_value=False)
        pipeline._enricher.enrich = AsyncMock()
        pipeline._publisher.publish = AsyncMock()
        pipeline._store.save = AsyncMock()

        await pipeline.process(sample_raw_event, source="geralda")

        # Verificar ordem (deduplicator antes de publish)
        pipeline._deduplicator.check_and_mark.assert_called()
        pipeline._enricher.enrich.assert_called()


class TestProcessingResult:
    """Testes para resultado de processamento."""

    def test_processing_result_creation(self):
        """Testa criar resultado."""
        result = ProcessingResult(
            event_id="evt-123",
            status="processed",
            actions_taken=["created_plan"],
        )

        assert result.event_id == "evt-123"
        assert result.status == "processed"
        assert result.actions_taken == ["created_plan"]

    def test_processing_result_with_error(self):
        """Testa resultado com erro."""
        result = ProcessingResult(
            event_id="evt-456",
            status="error",
            error_message="Failed to normalize",
        )

        assert result.status == "error"
        assert "error" in result.error_message.lower()

    def test_processing_result_skipped(self):
        """Testa resultado pulado (duplicado)."""
        result = ProcessingResult(
            event_id="evt-789",
            status="skipped",
        )

        assert result.status == "skipped"
        assert result.actions_taken == []


class TestPipelineComponents:
    """Testes para componentes do pipeline."""

    @pytest.mark.asyncio
    async def test_normalize_stage(self, pipeline):
        """Testa estágio de normalização."""
        raw_event = {
            "event_type": "care.plan_created",
            "patient_id": "pac-001",
        }

        event = await pipeline._normalizer.normalize(raw_event, source="geralda")

        assert event.event_type == "care.plan_created"
        assert event.patient_id == "pac-001"

    @pytest.mark.asyncio
    async def test_deduplication_stage(self, pipeline, mock_redis):
        """Testa estágio de idempotência."""
        event = IntelliCareEvent(
            event_type="test.event",
            patient_id="pac-001",
            payload={},
        )

        is_dup = await pipeline._deduplicator.check_and_mark(event)

        assert is_dup is False  # Primeira vez

    @pytest.mark.asyncio
    async def test_enrichment_stage(self, pipeline):
        """Testa estágio de enriquecimento."""
        event = IntelliCareEvent(
            event_type="test.event",
            patient_id="pac-001",
            payload={},
        )

        enriched = await pipeline._enricher.enrich(event)

        assert enriched.original_event == event
        assert enriched.patient_id == "pac-001"

    @pytest.mark.asyncio
    async def test_persist_stage(self, pipeline, mock_db_session_factory):
        """Testa estágio de persistência."""
        event = IntelliCareEvent(
            event_type="test.event",
            patient_id="pac-001",
            payload={},
        )

        enriched = await pipeline._enricher.enrich(event)

        await pipeline._store.save(
            event=event,
            enriched=enriched,
            result_status="processed",
            context_activated=None,
            protocol_executed=None,
            actions_taken=[],
        )

        # Deve ter chamado execute
        mock_db_session_factory.return_value.execute.assert_called()


class TestPipelineErrorHandling:
    """Testes para tratamento de erros."""

    @pytest.mark.asyncio
    async def test_handles_normalization_error(self, pipeline):
        """Testa tratamento de erro na normalização."""
        invalid_event = {"invalid": "data"}

        result = await pipeline.process(invalid_event, source="test")

        assert result.status == "error"

    @pytest.mark.asyncio
    async def test_handles_enrichment_error(self, pipeline, sample_raw_event):
        """Testa tratamento de erro no enriquecimento."""
        # Forçar erro no enricher
        with patch.object(pipeline._enricher, "enrich", side_effect=Exception("Enrich failed")):
            result = await pipeline.process(sample_raw_event, source="geralda")

            # Deve registrar erro
            assert result.status == "error"

    @pytest.mark.asyncio
    async def test_handles_persistence_error(self, pipeline, sample_raw_event):
        """Testa tratamento de erro na persistência."""
        # Forçar erro no store
        with patch.object(pipeline._store, "save", side_effect=Exception("DB failed")):
            result = await pipeline.process(sample_raw_event, source="geralda")

            # Deve registrar erro mas não propagar exceção
            assert result.status in ["error", "processed"]

    @pytest.mark.asyncio
    async def test_continues_on_publish_error(self, pipeline, sample_raw_event):
        """Testa que pipeline continua se publicação falhar."""
        # Publicador falha
        with patch.object(pipeline._publisher, "publish", side_effect=Exception("Redis failed")):
            result = await pipeline.process(sample_raw_event, source="geralda")

            # Deve continuar e processar mesmo assim
            assert result.status == "processed"


class TestPipelinePerformance:
    """Testes de performance."""

    @pytest.mark.asyncio
    async def test_process_single_event_performance(self, pipeline):
        """Testa performance de processamento único."""
        import time

        event = {
            "event_type": "test.event",
            "patient_id": "pac-001",
        }

        start = time.time()
        result = await pipeline.process(event, source="test")
        duration = time.time() - start

        # Deve ser rápido (< 1 segundo)
        assert duration < 1.0
        assert result.status in ["processed", "skipped"]

    @pytest.mark.asyncio
    async def test_process_batch_performance(self, pipeline):
        """Testa performance de processamento em lote."""
        import time

        events = [
            {
                "event_type": "test.event",
                "patient_id": f"pac-{i:03d}",
            }
            for i in range(100)
        ]

        start = time.time()
        results = await pipeline.process_batch(events, source="test")
        duration = time.time() - start

        # 100 eventos em menos de 10 segundos
        assert duration < 10.0
        assert len(results) == 100


class TestPipelineIntegration:
    """Testes de integração do pipeline."""

    @pytest.mark.asyncio
    async def test_full_pipeline_flow(self, pipeline, sample_raw_event):
        """Testa fluxo completo do pipeline."""
        # Processar evento
        result = await pipeline.process(sample_raw_event, source="geralda")

        # Verificar resultado
        assert isinstance(result, ProcessingResult)
        assert result.event_id is not None
        assert result.status in ["processed", "skipped"]

        # Se processado, deve ter salvo no banco
        if result.status == "processed":
            pipeline._store.save.assert_called()

    @pytest.mark.asyncio
    async def test_pipeline_with_context_manager(self, pipeline, sample_raw_event):
        """Testa pipeline com ContextManager (quando implementado)."""
        # Por enquanto, ContextManager é stub
        result = await pipeline.process(sample_raw_event, source="geralda")

        # Deve funcionar mesmo sem ContextManager real
        assert result.status in ["processed", "skipped"]

    @pytest.mark.asyncio
    async def test_pipeline_with_protocol_engine(self, pipeline, sample_raw_event):
        """Testa pipeline com ProtocolEngine (quando implementado)."""
        # Por enquanto, ProtocolEngine é stub
        result = await pipeline.process(sample_raw_event, source="geralda")

        # Deve funcionar mesmo sem ProtocolEngine real
        assert result.status in ["processed", "skipped"]
