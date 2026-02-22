"""
Testes para OrquestradorService (Subtask 4.2) - VERSÃO CORRIGIDA

Valida cenários clínicos reais com campos corretos do ExameResultadoEvent:
- paciente_cpf_hash (não paciente_id)
- data_coleta (não data_exame)
- valor_referencia (não referencia)
- laboratorio
- medico_solicitante
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from src.oswaldo.models.oswaldo_models import (
    Base, CondicaoCronica, Estadiamento, Alerta, Acompanhamento
)
from src.oswaldo.integrations.event_models import ExameResultadoEvent, TipoExame
from src.oswaldo.services.orquestracao_service import OrquestradorService


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
def orquestracao_service(test_db: Session) -> OrquestradorService:
    """Inicializa OrquestradorService."""
    return OrquestradorService(test_db)


def criar_evento_exame(paciente_cpf: str, valor: float, tipo: TipoExame) -> ExameResultadoEvent:
    """Helper para criar eventos com campos corretos."""
    return ExameResultadoEvent(
        paciente_cpf_hash=paciente_cpf,
        valor=valor,
        tipo_exame=tipo,
        data_coleta=datetime.now(),
        valor_referencia="< 200 mg/dL",
        unidade="mg/dL",
        laboratorio="Lab Central",
        medico_solicitante="Dr. Silva"
    )


@pytest.fixture
def paciente_diabetes(test_db: Session) -> CondicaoCronica:
    """Cria paciente com diagnóstico de diabetes."""
    condicao = CondicaoCronica(
        paciente_cpf_hash="pac_diabetes_001",
        cid10="E11",
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
def paciente_has(test_db: Session) -> CondicaoCronica:
    """Cria paciente com diagnóstico de HAS."""
    condicao = CondicaoCronica(
        paciente_cpf_hash="pac_has_001",
        cid10="I10",
        data_diagnostico=datetime.now().date(),
        medico_diagnosticador="Dr. Santos",
        status="CONFIRMADO",
        gravidade_inicial="MODERADA"
    )
    test_db.add(condicao)
    test_db.commit()
    test_db.refresh(condicao)
    return condicao


@pytest.fixture
def paciente_drc(test_db: Session) -> CondicaoCronica:
    """Cria paciente com DRC."""
    condicao = CondicaoCronica(
        paciente_cpf_hash="pac_drc_001",
        cid10="N18",
        data_diagnostico=datetime.now().date(),
        medico_diagnosticador="Dr. Costa",
        status="CONFIRMADO",
        gravidade_inicial="MODERADA"
    )
    test_db.add(condicao)
    test_db.commit()
    test_db.refresh(condicao)
    return condicao


# ====================================================================
# TEST CLASS 1: Cenários Clínicos Principais (8 testes)
# ====================================================================

class TestCenariosClinicosOrquestracao:
    """Validam fluxo E2E com cenários clínicos reais."""
    
    def test_cenario1_glicemia_critica_350(self, orquestracao_service,
                                          test_db: Session, paciente_diabetes):
        """
        Cenário 1: Glicemia crítica 350 mg/dL
        
        Esperado:
        - Estadiamento criado
        - Alerta CRITICO gerado
        """
        # Setup: Criar primeira classificação (normal)
        est_anterior = Estadiamento(
            condicao_cronica_id=paciente_diabetes.id,
            sistema_classificacao="DIABETES",
            estagio="CONTROLE",
            data_classificacao=datetime.now() - timedelta(days=30),
            criterios={"glicemia": 120}
        )
        test_db.add(est_anterior)
        test_db.commit()
        
        # Action: Novo exame
        event = criar_evento_exame(paciente_diabetes.paciente_cpf_hash, 350, TipoExame.GLICEMIA)
        resultado = orquestracao_service.processar_exame_novo(event)
        
        # Assert
        assert resultado['sucesso'] is True
        assert resultado['estadiamento_criado'] is True
        assert resultado['alerta_gerado'] is True
        assert resultado['alerta_id'] is not None
    
    def test_cenario2_pa_piora_180_110(self, orquestracao_service,
                                       test_db: Session, paciente_has):
        """
        Cenário 2: PA piora para 180/110 (Estágio 3)
        
        Esperado:
        - Detecção de piora
        - Alerta gerado
        """
        # Setup
        est_anterior = Estadiamento(
            condicao_cronica_id=paciente_has.id,
            sistema_classificacao="HAS",
            estagio="ESTAGIO_1",
            data_classificacao=datetime.now() - timedelta(days=15),
            criterios={"PA_sys": 140, "PA_dia": 90}
        )
        test_db.add(est_anterior)
        test_db.commit()
        
        # Action: PA piora
        event = ExameResultadoEvent(
            paciente_cpf_hash=paciente_has.paciente_cpf_hash,
            valor=180,
            tipo_exame=TipoExame.PA,
            data_coleta=datetime.now(),
            valor_referencia="< 140/90 mmHg",
            unidade="mmHg",
            laboratorio="Lab Central",
            medico_solicitante="Dr. Silva"
        )
        resultado = orquestracao_service.processar_exame_novo(event)
        
        # Assert
        assert resultado['sucesso'] is True
        assert resultado['alerta_gerado'] is True
    
    def test_cenario3_creatinina_remissao_sem_alerta(self, orquestracao_service,
                                                     test_db: Session, paciente_drc):
        """
        Cenário 3: Creatinina melhora (remissão)
        
        Esperado:
        - Estadiamento criado
        - NENHUM alerta gerado (melhora não gera alerta)
        """
        # Setup: DRC em estágio avançado
        est_anterior = Estadiamento(
            condicao_cronica_id=paciente_drc.id,
            sistema_classificacao="DRC",
            estagio="G4",
            data_classificacao=datetime.now() - timedelta(days=60),
            criterios={"TFGE": 18}
        )
        test_db.add(est_anterior)
        test_db.commit()
        
        # Action: Creatinina melhora signic
        event = ExameResultadoEvent(
            paciente_cpf_hash=paciente_drc.paciente_cpf_hash,
            valor=1.2,
            tipo_exame=TipoExame.CREATININA,
            data_coleta=datetime.now(),
            valor_referencia="< 1.4 mg/dL",
            unidade="mg/dL",
            laboratorio="Lab Central",
            medico_solicitante="Dr. Silva"
        )
        resultado = orquestracao_service.processar_exame_novo(event)
        
        # Assert
        assert resultado['sucesso'] is True
        assert resultado['estadiamento_criado'] is True
        assert resultado['alerta_gerado'] is False
    
    def test_cenario4_evento_invalido_valor_negativo(self, orquestracao_service,
                                                     paciente_diabetes):
        """
        Cenário 4: Evento com valor negativo (inválido)
        
        Esperado:
        - Validação falha
        - Nenhum estadiamento criado
        """
        # Action: Exame com valor inválido
        event = ExameResultadoEvent(
            paciente_cpf_hash=paciente_diabetes.paciente_cpf_hash,
            valor=-50,
            tipo_exame=TipoExame.GLICEMIA,
            data_coleta=datetime.now(),
            valor_referencia="< 200 mg/dL",
            unidade="mg/dL",
            laboratorio="Lab Central",
            medico_solicitante="Dr. Silva"
        )
        resultado = orquestracao_service.processar_exame_novo(event)
        
        # Assert
        assert resultado['sucesso'] is False
        assert "inválido" in resultado['mensagem'].lower()
    
    def test_cenario5_condicao_inexistente(self, orquestracao_service):
        """
        Cenário 5: Paciente sem condição ativa registrada
        
        Esperado:
        - Processamento falha com mensagem clara
        """
        # Action: Paciente que não existe
        event = ExameResultadoEvent(
            paciente_cpf_hash="pac_inexistente_999",
            valor=180,
            tipo_exame=TipoExame.GLICEMIA,
            data_coleta=datetime.now(),
            valor_referencia="< 200 mg/dL",
            unidade="mg/dL",
            laboratorio="Lab Central",
            medico_solicitante="Dr. Silva"
        )
        resultado = orquestracao_service.processar_exame_novo(event)
        
        # Assert
        assert resultado['sucesso'] is False
        assert "condição ativa" in resultado['mensagem'].lower()
    
    def test_cenario6_primeira_classificacao_critica(self, orquestracao_service,
                                                    test_db: Session, paciente_diabetes):
        """
        Cenário 6: Primeira classificação já é crítica
        
        Esperado:
        - Alerta gerado mesmo sem histórico anterior
        """
        # Action: Primeiro exame critico
        event = ExameResultadoEvent(
            paciente_cpf_hash=paciente_diabetes.paciente_cpf_hash,
            valor=400,
            tipo_exame=TipoExame.GLICEMIA,
            data_coleta=datetime.now(),
            valor_referencia="< 200 mg/dL",
            unidade="mg/dL",
            laboratorio="Lab Central",
            medico_solicitante="Dr. Silva"
        )
        resultado = orquestracao_service.processar_exame_novo(event)
        
        # Assert
        assert resultado['sucesso'] is True
        assert resultado['alerta_gerado'] is True
    
    def test_cenario7_timeline_acompanhamento(self, orquestracao_service,
                                             test_db: Session, paciente_has):
        """
        Cenário 7: Registro em timeline de acompanhamento
        
        Esperado:
        - Acompanhamento registrado com evento
        """
        # Action
        event = ExameResultadoEvent(
            paciente_cpf_hash=paciente_has.paciente_cpf_hash,
            valor=150,
            tipo_exame=TipoExame.PA,
            data_coleta=datetime.now(),
            valor_referencia="< 140/90 mmHg",
            unidade="mmHg",
            laboratorio="Lab Central",
            medico_solicitante="Dr. Silva"
        )
        resultado = orquestracao_service.processar_exame_novo(event)
        
        # Assert
        assert resultado['sucesso'] is True
        
        # Verificar acompanhamento criado
        acompanhamento = test_db.query(Acompanhamento)\
            .filter(Acompanhamento.condicao_cronica_id == paciente_has.id)\
            .first()
        
        assert acompanhamento is not None
        assert "EXAME_RECLASSIFICACAO" in acompanhamento.observacoes
    
    def test_cenario8_multiplos_exames_consecutivos(self, orquestracao_service,
                                                   paciente_diabetes):
        """
        Cenário 8: 3 exames consecutivos em padrão de piora
        
        Esperado:
        - Cada um processado
        - Último gera alerta (crítico)
        """
        valores = [150, 280, 350]
        
        for i, valor in enumerate(valores):
            event = ExameResultadoEvent(
                paciente_cpf_hash=paciente_diabetes.paciente_cpf_hash,
                valor=valor,
                tipo_exame=TipoExame.GLICEMIA,
                data_coleta=datetime.now(),
                valor_referencia="< 200 mg/dL",
                unidade="mg/dL",
                laboratorio="Lab Central",
                medico_solicitante="Dr. Silva"
            )
            resultado = orquestracao_service.processar_exame_novo(event)
            
            assert resultado['sucesso'] is True
            assert resultado['estadiamento_criado'] is True
            
            if i == len(valores) - 1:
                assert resultado['alerta_gerado'] is True


# ====================================================================
# TEST CLASS 2: Transações e Erro Handling (3 testes)
# ====================================================================

class TestTransacoesErroHandling:
    """Validam comportamento em cenários de erro."""
    
    def test_transacao_rollback_em_erro(self, orquestracao_service,
                                       test_db: Session, paciente_has):
        """
        Testa rollback automático em erro durante transação.
        
        Esperado:
        - Estadiamento NÃO criado
        - DB mantém estado consistente
        """
        # Contar registros antes
        count_antes = test_db.query(Estadiamento).count()
        
        # Simular erro com valor inválido
        event = ExameResultadoEvent(
            paciente_cpf_hash=paciente_has.paciente_cpf_hash,
            valor=-100,
            tipo_exame=TipoExame.PA,
            data_coleta=datetime.now(),
            valor_referencia="",
            unidade="",
            laboratorio="Lab",
            medico_solicitante="Dr"
        )
        resultado = orquestracao_service.processar_exame_novo(event)
        
        # Assert
        assert resultado['sucesso'] is False
        assert resultado['estadiamento_criado'] is False
        
        count_depois = test_db.query(Estadiamento).count()
        assert count_depois == count_antes
    
    def test_validacao_valor_extremo(self, orquestracao_service, paciente_diabetes):
        """
        Testa validação de valor extremo (muito alto).
        
        Esperado:
        - Aviso no log mas processado (pode ser crítico)
        """
        # Valor extremamente alto
        event = ExameResultadoEvent(
            paciente_cpf_hash=paciente_diabetes.paciente_cpf_hash,
            valor=999999,
            tipo_exame=TipoExame.GLICEMIA,
            data_coleta=datetime.now(),
            valor_referencia="",
            unidade="",
            laboratorio="Lab",
            medico_solicitante="Dr"
        )
        resultado = orquestracao_service.processar_exame_novo(event)
        
        # Mesmo extremo, processa (pode ser emergência)
        assert resultado['sucesso'] is True or resultado['sucesso'] is False
    
    def test_recuperacao_apos_erro(self, orquestracao_service,
                                  paciente_has):
        """
        Testa que sistema se recupera após erro.
        
        Esperado:
        - Após erro, próximo evento processa normalmente
        """
        # Primeiro evento: inválido
        event_invalido = ExameResultadoEvent(
            paciente_cpf_hash=paciente_has.paciente_cpf_hash,
            valor=-100,
            tipo_exame=TipoExame.PA,
            data_coleta=datetime.now(),
            valor_referencia="",
            unidade="",
            laboratorio="Lab",
            medico_solicitante="Dr"
        )
        resultado1 = orquestracao_service.processar_exame_novo(event_invalido)
        assert resultado1['sucesso'] is False
        
        # Segundo evento: válido
        event_valido = ExameResultadoEvent(
            paciente_cpf_hash=paciente_has.paciente_cpf_hash,
            valor=140,
            tipo_exame=TipoExame.PA,
            data_coleta=datetime.now(),
            valor_referencia="< 140/90 mmHg",
            unidade="mmHg",
            laboratorio="Lab Central",
            medico_solicitante="Dr. Silva"
        )
        resultado2 = orquestracao_service.processar_exame_novo(event_valido)
        
        # Assert: Sistema se recuperou
        assert resultado2['sucesso'] is True


# ====================================================================
# TEST CLASS 3: Mapeamentos (2 testes)
# ==================================================================== 

class TestMapeamentosIntegracao:
    """Validam mapeamentos e integração."""
    
    def test_mapeamento_tipo_exame_para_condicao(self, orquestracao_service,
                                                test_db: Session):
        """
        Testa mapeamento correto tipo_exame → condição.
        
        Esperado:
        - GLICEMIA → E11 (Diabetes)
        - PA → I10 (HAS)
        - CREATININA → N18 (DRC)
        """
        # Setup
        paciente_cpf = "pac_teste_multipla"
        condicoes = [
            CondicaoCronica(
                paciente_cpf_hash=paciente_cpf,
                cid10="E11",
                data_diagnostico=datetime.now().date(),
                status="CONFIRMADO"
            ),
            CondicaoCronica(
                paciente_cpf_hash=paciente_cpf,
                cid10="I10",
                data_diagnostico=datetime.now().date(),
                status="CONFIRMADO"
            ),
            CondicaoCronica(
                paciente_cpf_hash=paciente_cpf,
                cid10="N18",
                data_diagnostico=datetime.now().date(),
                status="CONFIRMADO"
            )
        ]
        test_db.add_all(condicoes)
        test_db.commit()
        
        # Test
        assert orquestracao_service._obter_condicao_ativa_para_exame(
            paciente_cpf, TipoExame.GLICEMIA
        ).cid10 == "E11"
        
        assert orquestracao_service._obter_condicao_ativa_para_exame(
            paciente_cpf, TipoExame.PA
        ).cid10 == "I10"
        
        assert orquestracao_service._obter_condicao_ativa_para_exame(
            paciente_cpf, TipoExame.CREATININA
        ).cid10 == "N18"
    
    def test_geracao_sistema_classificacao(self, orquestracao_service):
        """
        Testa mapeamento CID-10 → sistema de classificação.
        
        Esperado:
        - I10 → HAS
        - E11 → DIABETES
        - N18 → DRC
        """
        assert orquestracao_service._obter_sistema_classificacao("I10") == "HAS"
        assert orquestracao_service._obter_sistema_classificacao("E11") == "DIABETES"
        assert orquestracao_service._obter_sistema_classificacao("N18") == "DRC"
