"""
Testes de integração para RabbitMQ Consumer e Event Handlers.

- Test consumer initialization
- Test event validation
- Test handlers (mock events)
- Test E2E: event → database update
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.oswaldo.integrations.event_models import (
    ExameResultadoEvent,
    PacienteDadosEvent,
    RequestConsultaEvent,
    TipoExame
)
from src.oswaldo.integrations.rabbitmq_consumer import FlorenzeRabbitMQConsumer
from src.oswaldo.integrations.event_handlers import FlorenzeEventHandlers
from src.oswaldo.models.oswaldo_models import CondicaoCronica, Estadiamento, Alerta, Acompanhamento


class TestEventModels:
    """Testes para validação de event models."""
    
    def test_exame_resultado_event_valid(self):
        """Validar ExameResultadoEvent com dados válidos."""
        
        event_data = {
            "event_type": "exame_resultado",
            "paciente_cpf_hash": "abc123xyz",
            "data_coleta": "2026-02-13T10:30:00Z",
            "tipo_exame": "glicemia",
            "valor": 250.5,
            "unidade": "mg/dL",
            "valor_referencia": "70-100",
            "laboratorio": "Lab Central",
            "medico_solicitante": "Dr. Silva"
        }
        
        # Deve parsear sem erros
        event = ExameResultadoEvent(**event_data)
        assert event.paciente_cpf_hash == "abc123xyz"
        assert event.valor == 250.5
        assert event.tipo_exame == TipoExame.GLICEMIA
    
    def test_paciente_dados_event_valid(self):
        """Validar PacienteDadosEvent com dados válidos."""
        
        event_data = {
            "event_type": "paciente_dados",
            "paciente_cpf_hash": "abc123xyz",
            "idade": 65,
            "sexo": "M",
            "peso_kg": 80.5,
            "altura_cm": 175,
            "imc": 26.3
        }
        
        event = PacienteDadosEvent(**event_data)
        assert event.idade == 65
        assert event.peso_kg == 80.5
    
    def test_request_consulta_event_valid(self):
        """Validar RequestConsultaEvent com dados válidos."""
        
        event_data = {
            "event_type": "request_consulta",
            "paciente_cpf_hash": "abc123xyz",
            "motivo": "Acompanhamento hipertensão",
            "urgencia": "normal",
            "medico_solicitante": "Dr. Silva"
        }
        
        event = RequestConsultaEvent(**event_data)
        assert event.urgencia == "normal"


class TestFlorenzeConsumer:
    """Testes para FlorenzeRabbitMQConsumer."""
    
    def test_consumer_init(self):
        """Inicializar consumer com parâmetros."""
        
        consumer = FlorenzeRabbitMQConsumer(
            host="localhost",
            port=5672,
            username="guest",
            password="guest"
        )
        
        assert consumer.host == "localhost"
        assert consumer.port == 5672
        assert consumer.running is False
        assert len(consumer.handlers) == 0
    
    def test_register_handler(self):
        """Registrar handler para event type."""
        
        consumer = FlorenzeRabbitMQConsumer()
        mock_handler = Mock()
        
        consumer.register_handler("exame_resultado", mock_handler)
        
        assert "exame_resultado" in consumer.handlers
        assert consumer.handlers["exame_resultado"] == mock_handler
    
    def test_metrics_tracking(self):
        """Verificar que métricas estão sendo rastreadas."""
        
        consumer = FlorenzeRabbitMQConsumer()
        
        metrics = consumer.get_metrics()
        
        assert metrics["events_received"] == 0
        assert metrics["events_processed"] == 0
        assert metrics["events_failed"] == 0
        assert metrics["status"] == "stopped"
    
    @patch('pika.BlockingConnection')
    def test_connect_success(self, mock_connection):
        """Testar conexão bem-sucedida com RabbitMQ."""
        
        # Mock da conexão
        mock_conn_instance = MagicMock()
        mock_channel = MagicMock()
        mock_connection.return_value = mock_conn_instance
        mock_conn_instance.channel.return_value = mock_channel
        
        consumer = FlorenzeRabbitMQConsumer()
        consumer.connect()
        
        assert consumer.connection is not None
        assert consumer.channel is not None
        mock_channel.basic_qos.assert_called_once_with(prefetch_count=1)


class TestEventHandlers:
    """Testes para FlorenzeEventHandlers."""
    
    def test_handler_initialization(self, test_db_session):
        """Inicializar event handlers com banco de dados."""
        
        handlers = FlorenzeEventHandlers(db_session=test_db_session)
        
        assert handlers.db is not None
        assert handlers.diagnostico_service is not None
        assert handlers.classificacao_service is not None
    
    def test_handle_exame_resultado_no_condicao(self, test_db_session):
        """Test handle_exame_resultado quando paciente não tem condição ativa."""
        
        handlers = FlorenzeEventHandlers(db_session=test_db_session)
        
        event = {
            "paciente_cpf_hash": "inexistente123",
            "tipo_exame": "glicemia",
            "valor": 250.5,
            "laboratorio": "Lab Central",
            "medico_solicitante": "Dr. Silva"
        }
        
        # Não deve lançar exceção
        handlers.handle_exame_resultado(event)
    
    def test_handle_exame_resultado_with_condicao(self, test_db_session):
        """Test handle_exame_resultado com condição ativa."""
        
        # Criar condição teste
        condicao = CondicaoCronica(
            paciente_cpf_hash="pacient_test",
            cid10="E11",
            data_diagnostico=datetime.utcnow().date(),
            status="CONFIRMADO"
        )
        test_db_session.add(condicao)
        test_db_session.commit()
        
        handlers = FlorenzeEventHandlers(db_session=test_db_session)
        
        event = {
            "paciente_cpf_hash": "pacient_test",
            "tipo_exame": "glicemia",
            "valor": 250.5,
            "laboratorio": "Lab Central",
            "medico_solicitante": "Dr. Silva"
        }
        
        handlers.handle_exame_resultado(event)
        
        # Verificar que acompanhamento foi criado
        acompanhamentos = test_db_session.query(Acompanhamento).filter(
            Acompanhamento.paciente_cpf_hash == "pacient_test"
        ).all()
        
        assert len(acompanhamentos) > 0
    
    def test_detectar_piora_has(self):
        """Testar detecção de piora em HAS."""
        
        handlers = FlorenzeEventHandlers()
        
        # NORMAL → ESTAGIO_1 = piora
        assert handlers._detectar_piora("NORMAL", "ESTAGIO_1") is True
        
        # ESTAGIO_1 → ESTAGIO_2 = piora
        assert handlers._detectar_piora("ESTAGIO_1", "ESTAGIO_2") is True
        
        # ESTAGIO_2 → ESTAGIO_1 = melhora (não é piora)
        assert handlers._detectar_piora("ESTAGIO_2", "ESTAGIO_1") is False
        
        # ELEVADA → ELEVADA = sem mudança
        assert handlers._detectar_piora("ELEVADA", "ELEVADA") is False
    
    def test_calcular_severidade(self):
        """Testar cálculo de severidade de alerta."""
        
        handlers = FlorenzeEventHandlers()
        
        # Crítico
        assert handlers._calcular_severidade("CRITICO") == "CRITICO"
        assert handlers._calcular_severidade("G5") == "CRITICO"
        
        # Alto
        assert handlers._calcular_severidade("MAL_CONTROLADO") == "ALTO"
        assert handlers._calcular_severidade("G4") == "ALTO"
        
        # Médio
        assert handlers._calcular_severidade("MODERADO") == "MÉDIO"
        assert handlers._calcular_severidade("G3a") == "MÉDIO"
        
        # Baixo
        assert handlers._calcular_severidade("BEM_CONTROLADO") == "BAIXO"
        assert handlers._calcular_severidade("G1") == "BAIXO"


class TestE2EEventFlow:
    """Testes E2E: event → database update."""
    
    def test_exame_resultado_flow(self, test_db_session):
        """E2E: Receber exame → Registrar acompanhamento."""
        
        # Setup: criar condição
        condicao = CondicaoCronica(
            paciente_cpf_hash="e2e_test_001",
            cid10="E11",
            data_diagnostico=datetime.utcnow().date(),
            status="CONFIRMADO"
        )
        test_db_session.add(condicao)
        test_db_session.commit()
        
        # Simular evento
        handlers = FlorenzeEventHandlers(db_session=test_db_session)
        
        event = {
            "paciente_cpf_hash": "e2e_test_001",
            "tipo_exame": "glicemia",
            "valor": 350.0,
            "laboratorio": "Lab Central",
            "medico_solicitante": "Dr. Silva"
        }
        
        handlers.handle_exame_resultado(event)
        
        # Verificar:
        # 1. Acompanhamento foi criado
        acompanhamentos = test_db_session.query(Acompanhamento).filter(
            Acompanhamento.paciente_cpf_hash == "e2e_test_001"
        ).all()
        assert len(acompanhamentos) == 1
        assert acompanhamentos[0].glicemia == 350.0
        
        # 2. Alerta foi gerado (porque glicemia alta)
        alertas = test_db_session.query(Alerta).filter(
            Alerta.paciente_cpf_hash == "e2e_test_001"
        ).all()
        assert len(alertas) > 0
        assert alertas[0].tipo_alerta == "PIORA_PROGRESSIVA"


@pytest.fixture
def test_db_session():
    """Fixture para obter sessão de teste do banco de dados."""
    from src.oswaldo.database.session import SessionLocal
    from src.oswaldo.models.oswaldo_models import Base
    
    db = SessionLocal()
    
    # Limpar todas as tabelas antes do teste
    db.query(Alerta).delete()
    db.query(Acompanhamento).delete()
    db.query(Estadiamento).delete()
    db.query(CondicaoCronica).delete()
    db.commit()
    
    try:
        yield db
    finally:
        db.rollback()
        db.close()
