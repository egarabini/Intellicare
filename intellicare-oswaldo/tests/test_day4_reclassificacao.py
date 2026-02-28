"""
Testes para ReclassificacaoService (Subtask 4.1)

Validam:
1. Query para histórico de classificações
2. Comparação de estágios
3. Detecção de piora progressiva
4. Lógica de geração de alertas
5. Edge cases e erros
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from src.oswaldo.models.oswaldo_models import (
    Base, CondicaoCronica, Estadiamento, Alerta
)
from src.oswaldo.services.reclassificacao_service import ReclassificacaoService


@pytest.fixture
def test_db() -> Session:
    """Cria banco de testes em memória."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()


@pytest.fixture
def reclassificacao_service(test_db: Session) -> ReclassificacaoService:
    """Inicializa ReclassificacaoService com banco de testes."""
    return ReclassificacaoService(test_db)


@pytest.fixture
def condicao_has(test_db: Session) -> CondicaoCronica:
    """Cria condição de HAS para testes."""
    condicao = CondicaoCronica(
        paciente_cpf_hash="abc123def456",
        cid10="I10",
        data_diagnostico=datetime.now().date(),
        medico_diagnosticador="Dr. Silva",
        status="CONFIRMADO",
        gravidade_inicial="LEVE"
    )
    test_db.add(condicao)
    test_db.commit()
    test_db.refresh(condicao)
    return condicao


@pytest.fixture
def condicao_drc(test_db: Session) -> CondicaoCronica:
    """Cria condição de DRC para testes."""
    condicao = CondicaoCronica(
        paciente_cpf_hash="xyz789uvw000",
        cid10="N18",
        data_diagnostico=datetime.now().date(),
        medico_diagnosticador="Dr. Santos",
        status="CONFIRMADO",
        gravidade_inicial="MODERADA"
    )
    test_db.add(condicao)
    test_db.commit()
    test_db.refresh(condicao)
    return condicao


# ====================================================================
# TEST CLASS 1: Query para Reclassificação (5 testes)
# ====================================================================

class TestQueryReclassificacao:
    """Validam métodos de query para histórico de classificações."""
    
    def test_obter_ultima_classificacao_existe(self, reclassificacao_service, 
                                               test_db: Session, condicao_has):
        """
        Testa busca de última classificação quando existe histórico.
        
        Cenário: 2 classificações anteriores
        Esperado: Retorna a mais recente
        """
        # Setup: Adicionar 2 classificações
        est1 = Estadiamento(
            condicao_cronica_id=condicao_has.id,
            sistema_classificacao="HAS",
            estagio="ESTAGIO_1",
            data_classificacao=datetime.now() - timedelta(days=30),
            criterios={"PA": "140/90"}
        )
        est2 = Estadiamento(
            condicao_cronica_id=condicao_has.id,
            sistema_classificacao="HAS",
            estagio="ESTAGIO_2",
            data_classificacao=datetime.now() - timedelta(days=1),
            criterios={"PA": "160/100"}
        )
        test_db.add_all([est1, est2])
        test_db.commit()
        
        # Action
        ultima = reclassificacao_service.obter_ultima_classificacao(condicao_has.id)
        
        # Assert
        assert ultima is not None
        assert ultima.estagio == "ESTAGIO_2"
        assert ultima.data_classificacao > est1.data_classificacao
    
    def test_obter_ultima_classificacao_nao_existe(self, reclassificacao_service, 
                                                   condicao_has, condicao_drc):
        """
        Testa busca quando não existe classificação anterior.
        
        Cenário: Condição sem histórico de estadiamento
        Esperado: Retorna None
        """
        # Action
        ultima = reclassificacao_service.obter_ultima_classificacao(condicao_has.id)
        
        # Assert
        assert ultima is None
    
    def test_obter_historico_classificacoes(self, reclassificacao_service,
                                            test_db: Session, condicao_has):
        """
        Testa busca de histórico completo com limite.
        
        Cenário: 5 classificações, limite=3
        Esperado: Retorna 3 mais recentes em ordem desc
        """
        # Setup: Adicionar 5 classificações
        for i in range(5):
            est = Estadiamento(
                condicao_cronica_id=condicao_has.id,
                sistema_classificacao="HAS",
                estagio=f"ESTAGIO_{i+1}",
                data_classificacao=datetime.now() - timedelta(days=5-i),
                criterios={"PA": "160/100"}
            )
            test_db.add(est)
        test_db.commit()
        
        # Action
        historico = reclassificacao_service.obter_historico_classificacoes(
            condicao_has.id, limite=3
        )
        
        # Assert
        assert len(historico) == 3
        # Verificar que estão em ordem decrescente
        for i, est in enumerate(historico):
            if i > 0:
                assert est.data_classificacao <= historico[i-1].data_classificacao
    
    def test_obter_condicao_cronica(self, reclassificacao_service, condicao_has):
        """
        Testa busca de metadados da condição.
        
        Cenário: Buscar condição existente
        Esperado: Retorna CondicaoCronica com dados corretos
        """
        # Action
        condicao = reclassificacao_service.obter_condicao_cronica(condicao_has.id)
        
        # Assert
        assert condicao is not None
        assert condicao.cid10 == "I10"
        assert condicao.status == "CONFIRMADO"
    
    def test_obter_condicao_nao_existe(self, reclassificacao_service):
        """
        Testa busca de condição inexistente.
        
        Cenário: ID inválido
        Esperado: Retorna None
        """
        # Action
        condicao = reclassificacao_service.obter_condicao_cronica(999)
        
        # Assert
        assert condicao is None


# ====================================================================
# TEST CLASS 2: Comparação de Estágios (5 testes)
# ====================================================================

class TestComparacaoEstagio:
    """Validam lógica de comparação entre estágios clínicos."""
    
    def test_comparar_estadios_piora_has(self, reclassificacao_service):
        """
        Testa detecção de piora em HAS.
        
        Cenário: ESTAGIO_1 → ESTAGIO_2
        Esperado: piora=True, delta=1
        """
        # Action
        resultado = reclassificacao_service.comparar_estadios(
            estagio_anterior="ESTAGIO_1",
            estagio_novo="ESTAGIO_2",
            sistema="HAS"
        )
        
        # Assert
        assert resultado['mudou'] is True
        assert resultado['piora'] is True
        assert resultado['melhora'] is False
        assert resultado['delta_severidade'] == 1
    
    def test_comparar_estadios_melhora_drc(self, reclassificacao_service):
        """
        Testa detecção de melhora em DRC.
        
        Cenário: G3b → G3a
        Esperado: melhora=True, piora=False
        """
        # Action
        resultado = reclassificacao_service.comparar_estadios(
            estagio_anterior="G3b",
            estagio_novo="G3a",
            sistema="DRC"
        )
        
        # Assert
        assert resultado['mudou'] is True
        assert resultado['melhora'] is True
        assert resultado['piora'] is False
        assert resultado['delta_severidade'] < 0
    
    def test_comparar_estadios_sem_mudanca(self, reclassificacao_service):
        """
        Testa caso onde não há mudança de estágio.
        
        Cenário: ESTAGIO_2 → ESTAGIO_2
        Esperado: mudou=False, delta=0
        """
        # Action
        resultado = reclassificacao_service.comparar_estadios(
            estagio_anterior="ESTAGIO_2",
            estagio_novo="ESTAGIO_2",
            sistema="HAS"
        )
        
        # Assert
        assert resultado['mudou'] is False
        assert resultado['piora'] is False
        assert resultado['melhora'] is False
        assert resultado['delta_severidade'] == 0
    
    def test_comparar_estadios_critica_diabetes(self, reclassificacao_service):
        """
        Testa detecção de crítico em Diabetes.
        
        Cenário: MODERADO → CRITICA
        Esperado: piora=True, delta=2
        """
        # Action
        resultado = reclassificacao_service.comparar_estadios(
            estagio_anterior="MODERADO",
            estagio_novo="CRITICA",
            sistema="DIABETES"
        )
        
        # Assert
        assert resultado['piora'] is True
        assert resultado['delta_severidade'] > 1
    
    def test_comparar_estadios_sistema_invalido(self, reclassificacao_service):
        """
        Testa comportamento com sistema inválido.
        
        Cenário: Sistema não mapeado
        Esperado: mudou=False, sem exceção
        """
        # Action
        resultado = reclassificacao_service.comparar_estadios(
            estagio_anterior="X",
            estagio_novo="Y",
            sistema="SISTEMA_INEXISTENTE"
        )
        
        # Assert
        assert resultado['mudou'] is False


# ====================================================================
# TEST CLASS 3: Detecção de Piora (4 testes)
# ====================================================================

class TestDeteccaoPiora:
    """Validam detecção de piora progressiva."""
    
    def test_detectar_piora_progressiva(self, reclassificacao_service,
                                       test_db: Session, condicao_has):
        """
        Testa detecção quando há piora real.
        
        Cenário: ESTAGIO_1 → ESTAGIO_2
        Esperado: piora_detectada=True
        """
        # Setup
        ultima = Estadiamento(
            condicao_cronica_id=condicao_has.id,
            sistema_classificacao="HAS",
            estagio="ESTAGIO_1",
            data_classificacao=datetime.now(),
            criterios={}
        )
        test_db.add(ultima)
        test_db.commit()
        
        # Action
        resultado = reclassificacao_service.detectar_piora_progressiva(
            ultima=ultima,
            novo_estagio="ESTAGIO_2",
            sistema="HAS"
        )
        
        # Assert
        assert resultado['piora_detectada'] is True
        assert "Piora progressiva" in resultado['motivo']
    
    def test_detectar_piora_primeira_classificacao(self, reclassificacao_service,
                                                   condicao_has):
        """
        Testa caso de primeira classificação (sem precedente).
        
        Cenário: ultima=None
        Esperado: piora_detectada=False
        """
        # Action
        resultado = reclassificacao_service.detectar_piora_progressiva(
            ultima=None,
            novo_estagio="ESTAGIO_1",
            sistema="HAS"
        )
        
        # Assert
        assert resultado['piora_detectada'] is False
        assert "Primeira" in resultado['motivo']
    
    def test_detectar_melhora_nao_alerta(self, reclassificacao_service,
                                        test_db: Session, condicao_drc):
        """
        Testa caso de melhora (não gera piora).
        
        Cenário: G4 → G3b
        Esperado: piora_detectada=False
        """
        # Setup
        ultima = Estadiamento(
            condicao_cronica_id=condicao_drc.id,
            sistema_classificacao="DRC",
            estagio="G4",
            data_classificacao=datetime.now(),
            criterios={}
        )
        test_db.add(ultima)
        test_db.commit()
        
        # Action
        resultado = reclassificacao_service.detectar_piora_progressiva(
            ultima=ultima,
            novo_estagio="G3b",
            sistema="DRC"
        )
        
        # Assert
        assert resultado['piora_detectada'] is False
    
    def test_detectar_mudanca_pequena_nao_alerta(self, reclassificacao_service,
                                                 test_db: Session, condicao_drc):
        """
        Testa mudança pequena (< 1 nível).
        
        Cenário: G3a → G3b (delta = 0.5)
        Esperado: piora_detectada=False
        """
        # Setup
        ultima = Estadiamento(
            condicao_cronica_id=condicao_drc.id,
            sistema_classificacao="DRC",
            estagio="G3a",
            data_classificacao=datetime.now(),
            criterios={}
        )
        test_db.add(ultima)
        test_db.commit()
        
        # Action
        resultado = reclassificacao_service.detectar_piora_progressiva(
            ultima=ultima,
            novo_estagio="G3b",
            sistema="DRC"
        )
        
        # Assert
        # G3a: 2, G3b: 2.5, delta: 0.5 < 1 → piora_detectada=False
        assert resultado['piora_detectada'] is False


# ====================================================================
# TEST CLASS 4: Lógica de Alerta (5 testes)
# ====================================================================

class TestNecessidadeAlerta:
    """Validam lógica de geração de alertas."""
    
    def test_alerta_por_piora_progressiva(self, reclassificacao_service):
        """
        Testa geração de alerta por piora.
        
        Cenário: piora_detectada=True
        Esperado: gera_alerta=True, severidade baseada no estagio
        """
        # Action
        gera_alerta, severidade, desc = reclassificacao_service.necessita_novo_alerta(
            piora_detectada=True,
            novo_estagio="ESTAGIO_2",
            sistema="HAS"
        )
        
        # Assert
        assert gera_alerta is True
        assert severidade in ["BAIXA", "MEDIA", "ALTA", "CRITICA"]
        assert "Piora" in desc
    
    def test_alerta_critica_inicial(self, reclassificacao_service):
        """
        Testa alerta para crítico na primeira vez.
        
        Cenário: piora_detectada=False, mas novo_estagio=CRITICA
        Esperado: gera_alerta=True, severidade=CRITICA
        """
        # Action
        gera_alerta, severidade, desc = reclassificacao_service.necessita_novo_alerta(
            piora_detectada=False,
            novo_estagio="CRITICA",
            sistema="DIABETES"
        )
        
        # Assert
        assert gera_alerta is True
        assert severidade == "CRITICA"
    
    def test_sem_alerta_melhora(self, reclassificacao_service):
        """
        Testa que melhora nunca gera alerta.
        
        Cenário: piora_detectada=False, novo_estagio=melhora
        Esperado: gera_alerta=False
        """
        # Action
        gera_alerta, severidade, desc = reclassificacao_service.necessita_novo_alerta(
            piora_detectada=False,
            novo_estagio="G1",
            sistema="DRC"
        )
        
        # Assert
        assert gera_alerta is False
    
    def test_alerta_severidade_alta(self, reclassificacao_service):
        """
        Testa mapeamento correto de severidade de alerta.
        
        Cenário: novo_estagio com alta severidade
        Esperado: severidade=ALTA ou CRITICA
        """
        # Action
        gera_alerta, severidade, desc = reclassificacao_service.necessita_novo_alerta(
            piora_detectada=True,
            novo_estagio="ESTAGIO_3",
            sistema="HAS"
        )
        
        # Assert
        assert gera_alerta is True
        assert severidade in ["ALTA", "CRITICA"]
    
    def test_alerta_com_palavra_critica(self, reclassificacao_service):
        """
        Testa reconhecimento de 'CRITICA' no nome do estágio.
        
        Cenário: novo_estagio contém 'CRITICA'
        Esperado: gera_alerta=True, severidade=CRITICA
        """
        # Action
        gera_alerta, severidade, desc = reclassificacao_service.necessita_novo_alerta(
            piora_detectada=False,
            novo_estagio="G5_CRITICA",
            sistema="DRC"
        )
        
        # Assert
        assert gera_alerta is True
        assert severidade == "CRITICA"


# ====================================================================
# TEST CLASS 5: Tendências e Aggregations (2 testes)
# ====================================================================

class TestTendenciaClassificacao:
    """Validam cálculo de tendências."""
    
    def test_calcular_tendencia_piora_progressiva(self, reclassificacao_service,
                                                 test_db: Session, condicao_has):
        """
        Testa identificação de tendência de piora progressiva.
        
        Cenário: ESTAGIO_1 → ESTAGIO_2 → ESTAGIO_3
        Esperado: tendencia=PIORA_PROGRESSIVA
        """
        # Setup: Criar 3 classificações com piora progressiva
        for i in range(3):
            est = Estadiamento(
                condicao_cronica_id=condicao_has.id,
                sistema_classificacao="HAS",
                estagio=f"ESTAGIO_{i+1}",
                data_classificacao=datetime.now() - timedelta(days=2-i),
                criterios={}
            )
            test_db.add(est)
        test_db.commit()
        
        # Action
        tendencia = reclassificacao_service.calcular_tendencia(
            condicao_has.id, "HAS"
        )
        
        # Assert
        assert tendencia == "PIORA_PROGRESSIVA"
    
    def test_calcular_tendencia_estavel(self, reclassificacao_service,
                                       test_db: Session, condicao_drc):
        """
        Testa identificação de tendência estável.
        
        Cenário: G3a → G3a
        Esperado: tendencia=ESTAVEL
        """
        # Setup
        for _ in range(2):
            est = Estadiamento(
                condicao_cronica_id=condicao_drc.id,
                sistema_classificacao="DRC",
                estagio="G3a",
                data_classificacao=datetime.now() - timedelta(days=30),
                criterios={}
            )
            test_db.add(est)
        test_db.commit()
        
        # Action
        tendencia = reclassificacao_service.calcular_tendencia(
            condicao_drc.id, "DRC"
        )
        
        # Assert
        assert tendencia == "ESTAVEL"


# ====================================================================
# SUMMARY
# ====================================================================
# Total: 21 testes para Subtask 4.1
# Cobertura:
# - Query (5 testes): obter_ultima, obter_historico, obter_condicao
# - Comparação (5 testes): piora, melhora, sem mudança, crítico, inválido
# - Piora (4 testes): piora, primeira_vez, melhora, mudança_pequena
# - Alerta (5 testes): por piora, crítico inicial, melhora, severidade, palavra_critica
# - Tendência (2 testes): piora progressiva, estável
# ====================================================================
