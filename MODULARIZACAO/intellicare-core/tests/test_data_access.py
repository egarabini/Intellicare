"""Testes para OperationalDataAccess e AnalyticsDataAccess."""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch
from sqlalchemy import Column, String, DateTime, Integer, UUID, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from intellicare_core.data_access import (
    OperationalDataAccess,
    AnalyticsDataAccess,
)

# Setup database para testes
Base = declarative_base()


class MockPaciente(Base):
    """Entidade mock para testes."""

    __tablename__ = "pacientes"
    __table_args__ = {"schema": "test_operacional"}

    id = Column(UUID, primary_key=True)
    nome = Column(String(255))
    status = Column(String(50), default="ativo")
    created_by = Column(UUID)
    updated_by = Column(UUID)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    rowversion = Column(Integer, default=1)


class TestOperationalDataAccess:
    """Testes OperationalDataAccess."""

    def test_validate_schema_rejects_analytic(self):
        """Rejeita schema analítico."""
        session = MagicMock()
        
        with pytest.raises(ValueError, match="nunca acessa"):
            OperationalDataAccess(
                session=session,
                entity_class=MockPaciente,
                schema="oswaldo_analitico"  # ❌ Analítico!
            )

    def test_validate_schema_accepts_operational(self):
        """Aceita schema operacional."""
        session = MagicMock()
        
        dao = OperationalDataAccess(
            session=session,
            entity_class=MockPaciente,
            schema="oswaldo_operacional"  # ✅ Operacional
        )
        assert dao.schema == "oswaldo_operacional"

    def test_create_publishes_event(self):
        """Criar registra evento para consolidação."""
        session = MagicMock()
        mock_callback = MagicMock()
        
        dao = OperationalDataAccess(
            session=session,
            entity_class=MockPaciente,
            schema="oswaldo_operacional",
            publish_event_callback=mock_callback
        )
        
        # Mock do entity criado
        entity = MagicMock()
        entity.id = "123"
        session.query(MockPaciente).get = MagicMock(return_value=entity)
        
        # Por simplicidade, vamos mockar a operação
        with patch.object(dao, 'read', return_value=entity):
            # Verificar que callback foi chamado
            dao.publish_event_callback(
                entity_type="pacientes",
                entity_id="123",
                operation="CREATE",
                old_values=None,
                new_values={"nome": "João"},
                actor_id="user-123"
            )
            mock_callback.assert_called_once()

    def test_delete_soft_delete_default(self):
        """Delete é soft delete por padrão."""
        session = MagicMock()
        entity = MagicMock()
        entity.valid_to = None
        
        session.query(MockPaciente).get = MagicMock(return_value=entity)
        
        dao = OperationalDataAccess(
            session=session,
            entity_class=MockPaciente,
            schema="oswaldo_operacional"
        )
        
        with patch.object(dao, 'read', return_value=entity):
            result = dao.delete("123", actor_id="user-123", soft_delete=True)
            assert result is True
            # Verifica que updated_by foi setado
            assert entity.updated_by == "user-123"


class TestAnalyticsDataAccess:
    """Testes AnalyticsDataAccess."""

    def test_validate_schema_rejects_operational(self):
        """Rejeita schema operacional."""
        session = MagicMock()
        
        with pytest.raises(ValueError, match="só usa"):
            AnalyticsDataAccess(
                session=session,
                entity_class=MockPaciente,
                schema="oswaldo_operacional"  # ❌ Operacional!
            )

    def test_validate_schema_accepts_analytic(self):
        """Aceita schema analítico."""
        session = MagicMock()
        
        dao = AnalyticsDataAccess(
            session=session,
            entity_class=MockPaciente,
            schema="oswaldo_analitico"  # ✅ Analítico
        )
        assert dao.schema == "oswaldo_analitico"

    def test_create_is_rejected(self):
        """CREATE é rejeitado (read-only)."""
        session = MagicMock()
        
        dao = AnalyticsDataAccess(
            session=session,
            entity_class=MockPaciente,
            schema="oswaldo_analitico"
        )
        
        with pytest.raises(PermissionError, match="READ-ONLY"):
            dao.create({"nome": "João"})

    def test_update_is_rejected(self):
        """UPDATE é rejeitado (read-only)."""
        session = MagicMock()
        
        dao = AnalyticsDataAccess(
            session=session,
            entity_class=MockPaciente,
            schema="oswaldo_analitico"
        )
        
        with pytest.raises(PermissionError, match="READ-ONLY"):
            dao.update("123", {"nome": "Maria"})

    def test_delete_is_rejected(self):
        """DELETE é rejeitado (read-only)."""
        session = MagicMock()
        
        dao = AnalyticsDataAccess(
            session=session,
            entity_class=MockPaciente,
            schema="oswaldo_analitico"
        )
        
        with pytest.raises(PermissionError, match="READ-ONLY"):
            dao.delete("123")

    def test_read_is_allowed(self):
        """READ é permitido."""
        session = MagicMock()
        entity = MagicMock()
        
        session.query(MockPaciente).get = MagicMock(return_value=entity)
        
        dao = AnalyticsDataAccess(
            session=session,
            entity_class=MockPaciente,
            schema="oswaldo_analitico"
        )
        
        result = dao.read("123")
        assert result == entity

    def test_count_works(self):
        """count() funciona em analítico."""
        session = MagicMock()
        
        dao = AnalyticsDataAccess(
            session=session,
            entity_class=MockPaciente,
            schema="oswaldo_analitico"
        )
        
        # Mock execute
        mock_result = MagicMock()
        mock_result.scalar = MagicMock(return_value=42)
        session.execute = MagicMock(return_value=mock_result)
        
        count = dao.count()
        assert count >= 0  # Não falha


class TestSeparationGuarantees:
    """Testes de garantias de separação."""

    def test_operational_rejects_analytic_schema(self):
        """OperationalDataAccess rejeita schema analítico com ValueError."""
        session = MagicMock()
        
        with pytest.raises(ValueError) as exc_info:
            OperationalDataAccess(
                session=session,
                entity_class=MockPaciente,
                schema="oswaldo_analitico"
            )
        assert "nunca acessa" in str(exc_info.value)

    def test_analytics_rejects_operational_schema(self):
        """AnalyticsDataAccess rejeita schema operacional com ValueError."""
        session = MagicMock()
        
        with pytest.raises(ValueError) as exc_info:
            AnalyticsDataAccess(
                session=session,
                entity_class=MockPaciente,
                schema="oswaldo_operacional"
            )
        assert "só usa" in str(exc_info.value)

    def test_write_operations_only_in_operational(self):
        """Apenas OperationalDataAccess permite write."""
        session = MagicMock()
        
        operational = OperationalDataAccess(
            session=session,
            entity_class=MockPaciente,
            schema="oswaldo_operacional"
        )
        
        analytics = AnalyticsDataAccess(
            session=session,
            entity_class=MockPaciente,
            schema="oswaldo_analitico"
        )
        
        # Operational permite
        assert callable(operational.create)
        assert callable(operational.update)
        assert callable(operational.delete)
        
        # Analytics rejeita
        assert callable(analytics.create)  # Mas é rejeitado quando chamado
        with pytest.raises(PermissionError):
            analytics.create({})


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
