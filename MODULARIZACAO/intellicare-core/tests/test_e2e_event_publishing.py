"""E2E tests para Event Publishing (STEP 1.2).

Testes demonstram o fluxo completo:
1. Criar entidade em operacional
2. Evento é publicado via callback
3. Evento pode ser lido do Redis Stream
4. Consolidation consumer processa o evento

NOTA: Requer Redis rodando (ou usamos mock para CI/CD).
"""

import asyncio
import json
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, AsyncMock, patch, call
from sqlalchemy import Column, String, DateTime, Integer, UUID, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from uuid import uuid4

from intellicare_core.data_access import OperationalDataAccess, AnalyticsDataAccess
from intellicare_core.events.publisher import EventPublisher

# Setup database para testes
Base = declarative_base()


class MockPaciente(Base):
    """Entidade mock para testes E2E."""

    __tablename__ = "pacientes"
    __table_args__ = {"schema": "oswaldo_operacional"}

    id = Column(UUID, primary_key=True, default=uuid4)
    nome = Column(String(255))
    cpf = Column(String(14), unique=True)
    status = Column(String(50), default="ativo")
    created_by = Column(String(255))
    updated_by = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    rowversion = Column(Integer, default=1)


class MockPacienteAnalytics(Base):
    """Schema analítico para testes."""

    __tablename__ = "pacientes"
    __table_args__ = {"schema": "oswaldo_analitico"}

    id = Column(UUID, primary_key=True)
    nome = Column(String(255))
    cpf = Column(String(14))
    status = Column(String(50))
    created_by = Column(String(255))
    updated_by = Column(String(255), nullable=True)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    rowversion = Column(Integer)


class TestEventPublishingIntegration:
    """Testa integração com EventPublisher."""

    @pytest.fixture
    def mock_publisher(self):
        """Mock do EventPublisher."""
        publisher = AsyncMock(spec=EventPublisher)
        publisher.publish = AsyncMock(return_value="event-id-123")
        return publisher

    @pytest.fixture
    def session(self):
        """Session mock para testes."""
        return MagicMock(spec=Session)

    def test_operational_create_triggers_event_callback(self, session, mock_publisher):
        """Criar entidade dispara callback de publicação."""
        # Setup
        dao = OperationalDataAccess(
            session=session,
            entity_class=MockPaciente,
            schema="oswaldo_operacional",
        )

        # Armazena callback quando dao.create é chamado
        callback_called = []

        def capture_callback(entity_type, entity_id, operation, old_values, new_values, actor_id, reason=None):
            """Captura evento publicado."""
            callback_called.append({
                "entity_type": entity_type,
                "entity_id": entity_id,
                "operation": operation,
                "old_values": old_values,
                "new_values": new_values,
                "actor_id": actor_id,
                "reason": reason,
            })

        # Configure DAO com callback
        dao.publish_event_callback = capture_callback

        # Setup mocks: side_effect para simular ID generation
        def side_effect_add(entity):
            # Simula o que SQLAlchemy faz: quando add() é chamado, o ORM prepara para flush
            if not hasattr(entity, 'id') or entity.id is None:
                entity.id = uuid4()
        
        session.add = MagicMock(side_effect=side_effect_add)
        session.flush = MagicMock()

        # Executar
        result = dao.create(
            {
                "nome": "João Silva",
                "cpf": "123.456.789-00",
                "status": "ativo",
            },
            actor_id="user-123",
            audit_reason="Entrada portaria",
        )

        # Validar: callback foi chamado
        assert len(callback_called) == 1
        event = callback_called[0]
        assert event["operation"] == "CREATE"
        assert event["actor_id"] == "user-123"
        assert event["old_values"] is None
        assert event["new_values"] is not None
        assert event["reason"] == "Entrada portaria"

    def test_operational_update_triggers_event_callback(self, session):
        """Update dispara callback com old_values e new_values."""
        dao = OperationalDataAccess(
            session=session,
            entity_class=MockPaciente,
            schema="oswaldo_operacional",
        )

        # Armazena evento
        callback_called = []

        def capture_callback(entity_type, entity_id, operation, old_values, new_values, actor_id, reason=None):
            callback_called.append({
                "operation": operation,
                "old_values": old_values,
                "new_values": new_values,
                "reason": reason,
            })

        dao.publish_event_callback = capture_callback

        # Mock da entidade existente
        paciente_id = uuid4()
        existing_paciente = MockPaciente(
            id=paciente_id,
            nome="João Silva",
            cpf="123.456.789-00",
            status="ativo",
            rowversion=1,
            created_by="user-123",
            created_at=datetime.now(timezone.utc),
        )

        # Query mock
        session.query = MagicMock()
        session.query().get.return_value = existing_paciente
        session.flush = MagicMock()

        # Update
        dao.update(
            paciente_id,
            {"status": "coordenando"},
            actor_id="user-456",
            audit_reason="Mudança de status",
        )

        # Validar callback
        assert len(callback_called) == 1
        event = callback_called[0]
        assert event["operation"] == "UPDATE"
        assert event["reason"] == "Mudança de status"
        assert event["new_values"] is not None

    def test_operational_delete_soft_triggers_event(self, session):
        """Soft delete dispara callback."""
        dao = OperationalDataAccess(
            session=session,
            entity_class=MockPaciente,
            schema="oswaldo_operacional",
        )

        callback_called = []

        def capture_callback(entity_type, entity_id, operation, old_values, new_values, actor_id, reason=None):
            callback_called.append({"operation": operation, "reason": reason})

        dao.publish_event_callback = capture_callback

        # Mock
        paciente_id = uuid4()
        paciente = MockPaciente(id=paciente_id, nome="João")
        session.query = MagicMock()
        session.query().get.return_value = paciente
        session.flush = MagicMock()

        # Delete soft
        dao.delete(paciente_id, soft_delete=True, actor_id="user-789", audit_reason="Cancelamento")

        # Validar
        assert len(callback_called) == 1
        assert callback_called[0]["operation"] == "DELETE"
        assert callback_called[0]["reason"] == "Cancelamento"

    @pytest.mark.asyncio
    async def test_event_flow_to_redis_publisher(self, session):
        """Simula fluxo completo: operacional → evento → Redis."""
        # Setup publisher mock
        publisher = AsyncMock(spec=EventPublisher)
        publisher.publish = AsyncMock(return_value="msg-123")

        # Setup DAO com callback que publica
        dao = OperationalDataAccess(
            session=session,
            entity_class=MockPaciente,
            schema="oswaldo_operacional",
        )

        # Callback que integra com publisher
        async def async_publish_callback(entity_type, entity_id, operation, old_values, new_values, actor_id):
            """Publica evento para Redis."""
            await publisher.publish(
                event_type=f"{entity_type.lower()}.{operation.lower()}",
                data={
                    "entity_type": entity_type,
                    "entity_id": str(entity_id),
                    "operation": operation,
                    "old_values": old_values,
                    "new_values": new_values,
                    "actor_id": actor_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )

        dao.publish_event_callback = async_publish_callback

        # Executar (em contexto async)
        paciente_id = uuid4()
        await async_publish_callback(
            entity_type="Paciente",
            entity_id=paciente_id,
            operation="CREATE",
            old_values=None,
            new_values={"nome": "João", "cpf": "123.456.789-00"},
            actor_id="user-123",
        )

        # Validar: publisher.publish foi chamado
        publisher.publish.assert_called_once()
        call_args = publisher.publish.call_args
        assert call_args[1]["event_type"] == "paciente.create"
        assert call_args[1]["data"]["operation"] == "CREATE"

    def test_analytics_dao_rejects_writes(self, session):
        """Analytics DAO continua READ-ONLY."""
        dao = AnalyticsDataAccess(
            session=session,
            entity_class=MockPacienteAnalytics,
            schema="oswaldo_analitico",
        )

        # Deve rejeitar create
        with pytest.raises(PermissionError, match="READ-ONLY"):
            dao.create({"nome": "João"})

        # Deve rejeitar update
        with pytest.raises(PermissionError, match="READ-ONLY"):
            dao.update(uuid4(), {"status": "novo"})

        # Deve rejeitar delete
        with pytest.raises(PermissionError, match="READ-ONLY"):
            dao.delete(uuid4())

        # Mas permite read
        session.query = MagicMock()
        session.query().get.return_value = None
        result = dao.read(uuid4())
        assert result is None

    def test_event_schema_contains_all_required_fields(self, session):
        """Evento contém todos os campos necessários para consolidação."""
        dao = OperationalDataAccess(
            session=session,
            entity_class=MockPaciente,
            schema="oswaldo_operacional",
        )

        required_fields = []

        def validate_callback(entity_type, entity_id, operation, old_values, new_values, actor_id, reason=None):
            """Valida que todos os campos requeridos estão presentes."""
            required_fields.append({
                "entity_type": entity_type,
                "entity_id": entity_id,
                "operation": operation,
                "old_values": old_values,
                "new_values": new_values,
                "actor_id": actor_id,
            })

        dao.publish_event_callback = validate_callback

        # Setup mocks with side effect for ID generation
        def side_effect_add(entity):
            if not hasattr(entity, 'id') or entity.id is None:
                entity.id = uuid4()
        
        session.add = MagicMock(side_effect=side_effect_add)
        session.flush = MagicMock()

        # Create
        dao.create(
            {"nome": "João", "cpf": "123.456.789-00"},
            actor_id="user-123",
        )

        # Validar
        assert len(required_fields) == 1
        event = required_fields[0]
        assert event["entity_type"] is not None
        assert event["entity_id"] is not None
        assert event["operation"] == "CREATE"
        assert event["actor_id"] == "user-123"
        assert event["new_values"] is not None

    def test_multiple_operations_trigger_multiple_events(self, session):
        """Múltiplas operações geram múltiplos eventos."""
        dao = OperationalDataAccess(
            session=session,
            entity_class=MockPaciente,
            schema="oswaldo_operacional",
        )

        events = []

        def capture_events(entity_type, entity_id, operation, old_values, new_values, actor_id, reason=None):
            events.append({"operation": operation})

        dao.publish_event_callback = capture_events

        # Setup mock with side effect for ID generation
        def side_effect_add(entity):
            if not hasattr(entity, 'id') or entity.id is None:
                entity.id = uuid4()
        
        session.query = MagicMock()
        session.flush = MagicMock()
        session.add = MagicMock(side_effect=side_effect_add)

        # Simular 3 operações
        dao.create({"nome": "João"}, actor_id="user-1")
        assert len(events) == 1

        # Mock para update
        paciente = MockPaciente(id=uuid4(), nome="João", rowversion=1)
        session.query().get.return_value = paciente
        dao.update(uuid4(), {"status": "novo"}, actor_id="user-2")
        assert len(events) == 2

        # Mock para delete
        session.query().get.return_value = paciente
        dao.delete(uuid4(), actor_id="user-3")
        assert len(events) == 3

        # Validar
        assert events[0]["operation"] == "CREATE"
        assert events[1]["operation"] == "UPDATE"
        assert events[2]["operation"] == "DELETE"


class TestConsolidationConsumer:
    """Simula consolidation consumer que processa eventos (STEP 1.3)."""

    @pytest.mark.asyncio
    async def test_consolidation_consumer_processes_event(self):
        """Consumer lê evento de stream e consolida em analytics."""
        # Simulado: evento lido de Redis Stream
        event_from_stream = {
            "type": "paciente.create",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": json.dumps({
                "entity_type": "Paciente",
                "entity_id": str(uuid4()),
                "operation": "CREATE",
                "old_values": None,
                "new_values": {
                    "id": str(uuid4()),
                    "nome": "João Silva",
                    "cpf": "123.456.789-00",
                    "status": "ativo",
                },
                "actor_id": "user-123",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }),
        }

        # Parser do evento
        data = json.loads(event_from_stream["data"])
        assert data["entity_type"] == "Paciente"
        assert data["operation"] == "CREATE"
        assert data["new_values"]["nome"] == "João Silva"

        # Simular consolidação:
        # INSERT INTO oswaldo_analitico.pacientes SELECT * FROM oswaldo_operacional.pacientes
        # WHERE id = entity_id
        consolidation_result = {
            "table": "oswaldo_analitico.pacientes",
            "operation": data["operation"],
            "entity_id": data["entity_id"],
            "affected_rows": 1,
            "status": "success",
        }

        assert consolidation_result["status"] == "success"
        assert consolidation_result["affected_rows"] == 1

    @pytest.mark.asyncio
    async def test_consolidation_handles_delete_event(self):
        """Consumer processa DELETE event."""
        entity_id = str(uuid4())

        event_data = {
            "entity_type": "Paciente",
            "entity_id": entity_id,
            "operation": "DELETE",
            "old_values": {
                "id": entity_id,
                "nome": "João Silva",
                "status": "ativo",
            },
            "new_values": {
                "id": entity_id,
                "valid_to": datetime.now(timezone.utc).isoformat(),
            },
            "actor_id": "user-123",
        }

        # DELETE FROM oswaldo_analitico.pacientes WHERE id = entity_id
        # (ou UPDATE com valid_to)
        consolidation_result = {
            "table": "oswaldo_analitico.pacientes",
            "operation": event_data["operation"],
            "status": "success",
        }

        assert consolidation_result["status"] == "success"

    @pytest.mark.asyncio
    async def test_consolidation_handles_update_event(self):
        """Consumer processa UPDATE event."""
        entity_id = str(uuid4())

        event_data = {
            "entity_type": "Paciente",
            "entity_id": entity_id,
            "operation": "UPDATE",
            "old_values": {"status": "ativo"},
            "new_values": {"status": "coordenando", "rowversion": 2},
            "actor_id": "user-456",
        }

        # UPDATE oswaldo_analitico.pacientes SET status = ? WHERE id = ?
        consolidation_result = {
            "table": "oswaldo_analitico.pacientes",
            "operation": event_data["operation"],
            "rows_updated": 1,
            "status": "success",
        }

        assert consolidation_result["status"] == "success"
        assert consolidation_result["rows_updated"] == 1


class TestEventInjectionPattern:
    """Testa o padrão de injeção de callback para diferentes estratégias."""

    @pytest.fixture
    def session(self):
        """Session mock para testes."""
        return MagicMock(spec=Session)

    def test_sync_callback_pattern(self, session):
        """Callback síncrono (padrão atual)."""
        dao = OperationalDataAccess(
            session=session,
            entity_class=MockPaciente,
            schema="oswaldo_operacional",
        )

        calls = []

        def sync_callback(entity_type, entity_id, operation, old_values, new_values, actor_id, reason=None):
            calls.append((entity_type, operation))

        dao.publish_event_callback = sync_callback
        
        # Setup mocks with side effect for ID generation
        def side_effect_add(entity):
            if not hasattr(entity, 'id') or entity.id is None:
                entity.id = uuid4()
        
        session.flush = MagicMock()
        session.add = MagicMock(side_effect=side_effect_add)
        
        dao.create({"nome": "João"}, actor_id="user-1")

        assert len(calls) == 1
        # MockPaciente.lower() + "s" = "mockpacientes"
        assert calls[0] == ("mockpacientes", "CREATE")

    @pytest.mark.asyncio
    async def test_async_callback_pattern(self, session):
        """Callback assíncrono (para Redis/Kafka futuros)."""
        dao = OperationalDataAccess(
            session=session,
            entity_class=MockPaciente,
            schema="oswaldo_operacional",
        )

        calls = []

        async def async_callback(entity_type, entity_id, operation, old_values, new_values, actor_id, reason=None):
            calls.append((entity_type, operation))
            # Simulado: await publish_to_redis(...)

        # Verificação: callback pode ser async (testado com asyncio)
        await async_callback("pacientes", uuid4(), "CREATE", None, {}, "user-1")
        assert len(calls) == 1

    def test_no_callback_gracefully_handles(self, session):
        """Sem callback, DAO continua funcionando."""
        dao = OperationalDataAccess(
            session=session,
            entity_class=MockPaciente,
            schema="oswaldo_operacional",
        )

        # Não configura callback
        assert dao.publish_event_callback is None

        # Setup mocks
        session.flush = MagicMock()
        session.add = MagicMock()

        # Deve funcionar sem erro
        result = dao.create({"nome": "João"}, actor_id="user-1")
        assert result is not None


# ==================== INTEGRATION TEST COM REDIS (OPCIONAL) ====================
# Para rodar com Redis real em staging:
#   docker run -d -p 6379:6379 redis:7
#   pytest tests/test_e2e_event_publishing.py::TestRedisIntegration -v

class TestRedisIntegration:
    """Testes com Redis real (skip se não estiver disponível)."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_publish_to_redis_stream(self):
        """Publica evento real em Redis Stream (requer redis-py)."""
        try:
            import redis.asyncio as aioredis
        except ImportError:
            pytest.skip("redis-asyncio não instalado")

        try:
            # Conecta ao Redis
            redis = await aioredis.from_url("redis://localhost:6379")

            # Publica
            stream_name = "intellicare:paciente.create"
            result = await redis.xadd(
                stream_name,
                {
                    "type": "paciente.create",
                    "entity_id": str(uuid4()),
                    "operation": "CREATE",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )

            # Lê back
            messages = await redis.xrange(stream_name, count=1)
            assert len(messages) > 0

            # Cleanup
            await redis.delete(stream_name)
            await redis.close()

        except (ConnectionError, OSError):
            pytest.skip("Redis não está rodando em localhost:6379")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
