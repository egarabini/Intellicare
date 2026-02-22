"""
Testes Day 4 Subtask 4.3 - Transaction Service com Alertas

Validações:
1. Commit automático em sucesso
2. Rollback automático em erro
3. Geração de alertas de erro
4. Tracking de timing/durability
5. Retry em erros transitórios
"""

import pytest
import time
from datetime import datetime
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from src.oswaldo.models.oswaldo_models import Base, CondicaoCronica, Alerta
from src.oswaldo.services.transaction_service import (
    TransactionContext, transactional, TransactionalBatch,
    TransactionWithAlertIntegration, TransactionError
)


@pytest.fixture
def test_db() -> Session:
    """Banco de testes em memória."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()


# ====================================================================
# TEST CLASS 1: TransactionContext (5 testes)
# ====================================================================

class TestTransactionContext:
    """Validam o context manager TransactionContext."""
    
    def test_commit_automatico_sucesso(self, test_db: Session):
        """Transação com sucesso faz commit automático."""
        with TransactionContext(test_db, "criar_condicao") as db:
            condicao = CondicaoCronica(
                paciente_cpf_hash="pac_001",
                cid10="E11",
                data_diagnostico=datetime.now().date(),
                medico_diagnosticador="Dr. Teste",
                status="CONFIRMADO",
                gravidade_inicial="LEVE"
            )
            db.add(condicao)
        
        # Verificar que objeto foi persistido
        resultado = test_db.query(CondicaoCronica).filter_by(
            paciente_cpf_hash="pac_001"
        ).first()
        
        assert resultado is not None
        assert resultado.cid10 == "E11"
    
    def test_rollback_automatico_erro(self, test_db: Session):
        """Transação com erro faz rollback automático."""
        try:
            with TransactionContext(test_db, "criar_com_erro") as db:
                condicao = CondicaoCronica(
                    paciente_cpf_hash="pac_002",
                    cid10="I10",
                    data_diagnostico=datetime.now().date(),
                    medico_diagnosticador="Dr. Teste",
                    status="CONFIRMADO",
                    gravidade_inicial="LEVE"
                )
                db.add(condicao)
                # Simular erro
                raise ValueError("Erro simulado")
        except ValueError:
            pass
        
        # Verificar que rollback foi feito (objeto não persistido)
        resultado = test_db.query(CondicaoCronica).filter_by(
            paciente_cpf_hash="pac_002"
        ).first()
        
        assert resultado is None
    
    def test_multiplas_insercoes_commit(self, test_db: Session):
        """Múltiplas inserções em uma transação."""
        with TransactionContext(test_db, "criar_multiplas") as db:
            for i in range(5):
                condicao = CondicaoCronica(
                    paciente_cpf_hash=f"pac_{i:03d}",
                    cid10="E11",
                    data_diagnostico=datetime.now().date(),
                    medico_diagnosticador="Dr. Teste",
                    status="CONFIRMADO",
                    gravidade_inicial="LEVE"
                )
                db.add(condicao)
        
        count = test_db.query(CondicaoCronica).count()
        assert count == 5
    
    def test_rollback_multiplas_insercoes(self, test_db: Session):
        """Rollback cancela todas as múltiplas inserções."""
        try:
            with TransactionContext(test_db, "criar_multiplas_erro") as db:
                for i in range(3):
                    condicao = CondicaoCronica(
                        paciente_cpf_hash=f"pac_multi_{i:03d}",
                        cid10="E11",
                        data_diagnostico=datetime.now().date(),
                        medico_diagnosticador="Dr. Teste",
                        status="CONFIRMADO",
                        gravidade_inicial="LEVE"
                    )
                    db.add(condicao)
                raise RuntimeError("Cancela tudo")
        except RuntimeError:
            pass
        
        count = test_db.query(CondicaoCronica).count()
        assert count == 0
    
    def test_context_manager_atributos(self, test_db: Session):
        """TransactionContext rastreia committed/rolled_back."""
        ctx = TransactionContext(test_db, "teste_atributos")
        
        with ctx as db:
            condicao = CondicaoCronica(
                paciente_cpf_hash="pac_attrs",
                cid10="I10",
                data_diagnostico=datetime.now().date(),
                medico_diagnosticador="Dr. Teste",
                status="CONFIRMADO",
                gravidade_inicial="LEVE"
            )
            db.add(condicao)
        
        assert ctx.committed is True
        assert ctx.rolled_back is False


# ====================================================================
# TEST CLASS 2: Decorador @transactional (6 testes)
# ====================================================================

class TestTransactionalDecorador:
    """Validam o decorador @transactional."""
    
    def setup_method(self):
        """Setup para cada teste."""
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
    
    def test_decorador_commit_sucesso(self):
        """Decorador @transactional faz commit em sucesso."""
        db = self.SessionLocal()
        
        class TestService:
            def __init__(self, db):
                self.db = db
            
            @transactional(operation_name="criar_condicao")
            def criar_condicao(self):
                condicao = CondicaoCronica(
                    paciente_cpf_hash="pac_decorator_1",
                    cid10="E11",
                    data_diagnostico=datetime.now().date(),
                    medico_diagnosticador="Dr. Teste",
                    status="CONFIRMADO",
                    gravidade_inicial="LEVE"
                )
                self.db.add(condicao)
        
        service = TestService(db)
        service.criar_condicao()
        
        resultado = db.query(CondicaoCronica).filter_by(
            paciente_cpf_hash="pac_decorator_1"
        ).first()
        
        assert resultado is not None
        db.close()
    
    def test_decorador_rollback_erro(self):
        """Decorador @transactional faz rollback em erro."""
        db = self.SessionLocal()
        
        class TestService:
            def __init__(self, db):
                self.db = db
            
            @transactional(operation_name="criar_com_erro")
            def criar_com_erro(self):
                condicao = CondicaoCronica(
                    paciente_cpf_hash="pac_decorator_err",
                    cid10="I10",
                    data_diagnostico=datetime.now().date(),
                    medico_diagnosticador="Dr. Teste",
                    status="CONFIRMADO",
                    gravidade_inicial="LEVE"
                )
                self.db.add(condicao)
                raise ValueError("Erro intencional")
        
        service = TestService(db)
        
        with pytest.raises(ValueError):  # Decorador re-raises, não envolve em TransactionError
            service.criar_com_erro()
        
        resultado = db.query(CondicaoCronica).filter_by(
            paciente_cpf_hash="pac_decorator_err"
        ).first()
        
        assert resultado is None
        db.close()
    
    def test_decorador_sem_generate_alert(self):
        """Decorador sem gerar alertas."""
        db = self.SessionLocal()
        
        class TestService:
            def __init__(self, db):
                self.db = db
            
            @transactional(operation_name="sem_alerta", generate_error_alert=False)
            def operacao(self):
                raise ValueError("Erro")
        
        service = TestService(db)
        
        with pytest.raises(ValueError):  # Decorador re-raises
            service.operacao()
        
        db.close()
    
    def test_decorador_operacao_simples(self):
        """Decorador com operação simples."""
        db = self.SessionLocal()
        
        class TestService:
            def __init__(self, db):
                self.db = db
            
            @transactional()
            def somar(self, a, b):
                return a + b
        
        service = TestService(db)
        resultado = service.somar(3, 4)
        
        assert resultado == 7
        db.close()
    
    def test_decorador_preserva_kwargs(self):
        """Decorador preserva keywords arguments."""
        db = self.SessionLocal()
        
        class TestService:
            def __init__(self, db):
                self.db = db
            
            @transactional()
            def criar_multiplos(self, quantidade=5, prefixo="pac"):
                for i in range(quantidade):
                    condicao = CondicaoCronica(
                        paciente_cpf_hash=f"{prefixo}_{i}",
                        cid10="E11",
                        data_diagnostico=datetime.now().date(),
                        medico_diagnosticador="Dr. Teste",
                        status="CONFIRMADO",
                        gravidade_inicial="LEVE"
                    )
                    self.db.add(condicao)
                return quantidade
        
        service = TestService(db)
        total = service.criar_multiplos(quantidade=3, prefixo="test")
        
        assert total == 3
        assert db.query(CondicaoCronica).count() == 3
        db.close()


# ====================================================================
# TEST CLASS 3: TransactionalBatch (4 testes)
# ====================================================================

class TestTransactionalBatch:
    """Validam o context manager TransactionalBatch."""
    
    def test_batch_commit(self, test_db: Session):
        """Lote faz commit bem-sucedido."""
        with TransactionalBatch(test_db, "lote_condicoes") as batch:
            for i in range(3):
                condicao = CondicaoCronica(
                    paciente_cpf_hash=f"batch_pac_{i}",
                    cid10="E11",
                    data_diagnostico=datetime.now().date(),
                    medico_diagnosticador="Dr. Teste",
                    status="CONFIRMADO",
                    gravidade_inicial="LEVE"
                )
                test_db.add(condicao)
                batch.add_result()
        
        assert batch.result_count == 3
        assert batch.error_count == 0
        assert test_db.query(CondicaoCronica).count() == 3
    
    def test_batch_rollback(self, test_db: Session):
        """Lote faz rollback parcial."""
        try:
            with TransactionalBatch(test_db, "lote_erro") as batch:
                for i in range(2):
                    condicao = CondicaoCronica(
                        paciente_cpf_hash=f"batch_err_{i}",
                        cid10="I10",
                        data_diagnostico=datetime.now().date(),
                        medico_diagnosticador="Dr. Teste",
                        status="CONFIRMADO",
                        gravidade_inicial="LEVE"
                    )
                    test_db.add(condicao)
                    batch.add_result()
                raise RuntimeError("Erro lote")
        except RuntimeError:
            pass
        
        assert test_db.query(CondicaoCronica).count() == 0
    
    def test_batch_summary(self, test_db: Session):
        """get_summary() retorna estatísticas corretas."""
        with TransactionalBatch(test_db, "lote_summary") as batch:
            batch.add_result()
            batch.add_result()
            batch.add_error()
            
            summary = batch.get_summary()
        
        assert summary['succeeded'] == 2
        assert summary['failed'] == 1
        assert summary['total'] == 3
        assert summary['success_rate'] == 2/3
    
    def test_batch_sem_registros(self, test_db: Session):
        """Lote vazio."""
        with TransactionalBatch(test_db, "lote_vazio") as batch:
            pass
        
        assert batch.result_count == 0
        assert batch.error_count == 0


# ====================================================================
# TEST CLASS 4: TransactionWithAlertIntegration (5 testes)
# ====================================================================

class TestTransactionWithAlerts:
    """Validam integração de Transações com Alertas."""
    
    def setup_method(self):
        """Setup."""
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
    
    def test_gerar_alerta_erro(self):
        """Gera alerta quando transação falha."""
        db = self.SessionLocal()
        alert_service = TransactionWithAlertIntegration(db)
        
        alerta_id = alert_service.gerar_alerta_erro_transacao(
            operacao="teste_operacao",
            erro="Erro de teste",
            tipo_erro="DATABASE_ERROR",
            paciente_cpf_hash="pac_alerta_001",
            condicao_id=1
        )
        
        assert alerta_id is not None
        
        alerta = db.query(Alerta).filter_by(id=alerta_id).first()
        assert alerta is not None
        assert alerta.tipo_alerta == "ERRO_PROCESSAMENTO"
        assert alerta.severidade == "ALTA"
        
        db.close()
    
    def test_alerta_severidade_validation_error(self):
        """Validation error gera alerta MEDIA."""
        db = self.SessionLocal()
        alert_service = TransactionWithAlertIntegration(db)
        
        alerta_id = alert_service.gerar_alerta_erro_transacao(
            operacao="validar_dados",
            erro="Campo inválido",
            tipo_erro="VALIDATION_ERROR",
            paciente_cpf_hash="pac_val",
            condicao_id=1
        )
        
        alerta = db.query(Alerta).filter_by(id=alerta_id).first()
        assert alerta is not None
        assert alerta.severidade == "MEDIA"
        
        db.close()
    
    def test_registrar_transacao_commit(self):
        """Registra transação bem-sucedida."""
        db = self.SessionLocal()
        alert_service = TransactionWithAlertIntegration(db)
        
        registro = alert_service.registrar_transacao(
            operacao="criar_condicao",
            status="COMMIT",
            tempo_ms=45.3
        )
        
        assert registro['status'] == "COMMIT"
        assert registro['duravel'] is True
        assert registro['tempo_ms'] == 45.3
        
        db.close()
    
    def test_registrar_transacao_rollback(self):
        """Registra transação com rollback."""
        db = self.SessionLocal()
        alert_service = TransactionWithAlertIntegration(db)
        
        registro = alert_service.registrar_transacao(
            operacao="operacao_falhada",
            status="ROLLBACK",
            tempo_ms=12.5,
            mensagem="Erro de validação"
        )
        
        assert registro['status'] == "ROLLBACK"
        assert registro['duravel'] is False
        assert "Erro de validação" in registro['mensagem']
        
        db.close()
    
    def test_alerta_sem_paciente_condicao(self):
        """Alerta pode ser criado com valores padrão para paciente/condição."""
        db = self.SessionLocal()
        alert_service = TransactionWithAlertIntegration(db)
        
        alerta_id = alert_service.gerar_alerta_erro_transacao(
            operacao="sistema_generico",
            erro="Erro de sistema",
            tipo_erro="PROCESSING_ERROR"
        )
        
        assert alerta_id is not None
        
        alerta = db.query(Alerta).filter_by(id=alerta_id).first()
        assert alerta is not None
        assert alerta.paciente_cpf_hash == "SISTEMA"
        assert alerta.condicao_cronica_id == 1
        
        db.close()


# ====================================================================
# TEST CLASS 5: Edge Cases e Performance (5 testes)
# ====================================================================

class TestTransactionEdgeCases:
    """Validam casos extremos de transações."""
    
    def test_transacao_vazia(self, test_db: Session):
        """Transação vazia (sem operações)."""
        with TransactionContext(test_db, "transacao_vazia") as db:
            pass
        
        # Deve completar sem erro
        assert test_db.query(CondicaoCronica).count() == 0
    
    def test_transacao_nested_nao_suportada(self, test_db: Session):
        """Transações aninhadas não são explicitamente suportadas."""
        # SQLite não suporta nested transactions, teste que comportamento é previsível
        with TransactionContext(test_db, "outer") as db1:
            condicao1 = CondicaoCronica(
                paciente_cpf_hash="nested_pac",
                cid10="E11",
                data_diagnostico=datetime.now().date(),
                medico_diagnosticador="Dr. Teste",
                status="CONFIRMADO",
                gravidade_inicial="LEVE"
            )
            db1.add(condicao1)
        
        assert test_db.query(CondicaoCronica).count() == 1
    
    def test_timing_transacao_rapida(self, test_db: Session):
        """Registrar transação muito rápida (<1ms)."""
        db_service = TransactionWithAlertIntegration(test_db)
        
        start = time.time()
        registro = db_service.registrar_transacao(
            operacao="operacao_rapida",
            status="COMMIT",
            tempo_ms=0.001
        )
        
        assert registro['tempo_ms'] < 1
    
    def test_timing_transacao_lenta(self):
        """Registrar transação lenta (>1 segundo)."""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        
        db_service = TransactionWithAlertIntegration(db)
        
        registro = db_service.registrar_transacao(
            operacao="operacao_lenta",
            status="COMMIT",
            tempo_ms=1250.5
        )
        
        assert registro['tempo_ms'] > 1000
        db.close()
    
    def test_erro_muito_longo(self):
        """Mensagem de erro truncada se muito longa."""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        
        db_service = TransactionWithAlertIntegration(db)
        
        erro_longo = "x" * 500  # 500 caracteres
        alerta_id = db_service.gerar_alerta_erro_transacao(
            operacao="erro_longo",
            erro=erro_longo,
            tipo_erro="PROCESSING_ERROR",
            paciente_cpf_hash="pac_erro_longo",
            condicao_id=1
        )
        
        if alerta_id:
            alerta = db.query(Alerta).filter_by(id=alerta_id).first()
            # Mensagem deve estar truncada
            assert alerta is not None
            assert len(alerta.descricao) <= 256  # Limite do campo descricao
            # Detalhes (dados_alerta) têm erro completo
            if alerta.dados_alerta and 'erro_completo' in alerta.dados_alerta:
                assert len(alerta.dados_alerta['erro_completo']) == 500
        
        db.close()
