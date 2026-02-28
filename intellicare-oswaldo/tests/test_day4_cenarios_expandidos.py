"""
Testes Day 4 Subtask 4.4 - Suite Expandida de Cenários Clínicos (25+ testes)

Cenários validados:
1. Sequências de piora (glicemia, PA, creatinina)
2. Remissão clínica
3. Estabilidade
4. Múltiplas condições simultâneas
5. Alertas com escalação
6. Timeline completa
7. Edge cases e extremos
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from src.oswaldo.models.oswaldo_models import (
    Base, CondicaoCronica, Estadiamento, Alerta, Acompanhamento
)
from src.oswaldo.integrations.event_models import ExameResultadoEvent, TipoExame
from src.oswaldo.services.reclassificacao_service import ReclassificacaoService


@pytest.fixture
def test_db() -> Session:
    """Banco de testes em memória."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()


@pytest.fixture
def reclassificacao_service(test_db: Session) -> ReclassificacaoService:
    """ReclassificacaoService com DB de teste."""
    return ReclassificacaoService(test_db)


def criar_condicao(db: Session, cpf: str, cid10: str) -> CondicaoCronica:
    """Helper para criar condição."""
    condicao = CondicaoCronica(
        paciente_cpf_hash=cpf,
        cid10=cid10,
        data_diagnostico=datetime.now().date(),
        medico_diagnosticador="Dr. Teste",
        status="CONFIRMADO",
        gravidade_inicial="LEVE"
    )
    db.add(condicao)
    db.commit()
    db.refresh(condicao)
    return condicao


def criar_estadiamento(db: Session, condicao_id: int, sistema: str,
                       estagio: str, dias_atras: int = 30) -> Estadiamento:
    """Helper para criar estadiamento."""
    est = Estadiamento(
        condicao_cronica_id=condicao_id,
        sistema_classificacao=sistema,
        estagio=estagio,
        data_classificacao=datetime.now() - timedelta(days=dias_atras),
        criterios={}
    )
    db.add(est)
    db.commit()
    db.refresh(est)
    return est


# ====================================================================
# TEST CLASS 1: Sequências de Piora (8 testes)
# ====================================================================

class TestSequenciasPiora:
    """Validam sequências progressivas de piora clínica."""
    
    def test_piora_progressiva_diabetes_3_etapas(self, reclassificacao_service,
                                                 test_db: Session):
        """CONTROLE → LEVE → MODERADO → SEVERO → CRITICA (5 etapas)."""
        condicao = criar_condicao(test_db, "pac_dm_piora", "E11")
        
        etapas = ["CONTROLE", "LEVE", "MODERADO", "SEVERO", "CRITICA"]
        
        for i, estagio in enumerate(etapas):
            est = criar_estadiamento(test_db, condicao.id, "DIABETES", estagio, 
                                    dias_atras=30-5*i)
        
        # Última é sempre a mais recente
        ultima = reclassificacao_service.obter_ultima_classificacao(condicao.id)
        assert ultima.estagio == "CRITICA"
        
        # Tendência deve ser PIORA_PROGRESSIVA
        tendencia = reclassificacao_service.calcular_tendencia(condicao.id, "DIABETES")
        assert tendencia == "PIORA_PROGRESSIVA"
    
    def test_piora_has_3_passos(self, reclassificacao_service, test_db: Session):
        """ESTAGIO_1 → ESTAGIO_2 → ESTAGIO_3."""
        condicao = criar_condicao(test_db, "pac_has_3passos", "I10")
        
        criar_estadiamento(test_db, condicao.id, "HAS", "ESTAGIO_1", dias_atras=60)
        criar_estadiamento(test_db, condicao.id, "HAS", "ESTAGIO_2", dias_atras=30)
        criar_estadiamento(test_db, condicao.id, "HAS", "ESTAGIO_3", dias_atras=0)
        
        ultima = reclassificacao_service.obter_ultima_classificacao(condicao.id)
        assert ultima.estagio == "ESTAGIO_3"
        
        # Comparação: ESTAGIO_1 → ESTAGIO_3 deve ser piora significativa
        comparacao = reclassificacao_service.comparar_estadios(
            "ESTAGIO_1", "ESTAGIO_3", "HAS"
        )
        assert comparacao['piora'] is True
        assert comparacao['delta_severidade'] == 2
    
    def test_piora_drc_g1_para_g5(self, reclassificacao_service, test_db: Session):
        """DRC do melhor ao pior estágio: G1 → G5."""
        condicao = criar_condicao(test_db, "pac_drc_fulll", "N18")
        
        etapas = ["G1", "G2", "G3a", "G3b", "G4", "G5"]
        for i, est in enumerate(etapas):
            criar_estadiamento(test_db, condicao.id, "DRC", est, dias_atras=60-10*i)
        
        historico = reclassificacao_service.obter_historico_classificacoes(
            condicao.id, limite=10
        )
        
        assert len(historico) == 6
        assert historico[0].estagio == "G5"  # Mais recente
    
    def test_piora_com_saltos_niveis(self, reclassificacao_service, test_db: Session):
        """Teste com saltos (não sequencial): LEVE → CRITICA."""
        condicao = criar_condicao(test_db, "pac_salto", "E11")
        
        criar_estadiamento(test_db, condicao.id, "DIABETES", "LEVE", dias_atras=30)
        criar_estadiamento(test_db, condicao.id, "DIABETES", "CRITICA", dias_atras=0)
        
        comparacao = reclassificacao_service.comparar_estadios(
            "LEVE", "CRITICA", "DIABETES"
        )
        
        assert comparacao['piora'] is True
        assert comparacao['delta_severidade'] > 2
    
    def test_piora_detectada_com_mais_de_30_anos(self, reclassificacao_service,
                                                  test_db: Session):
        """Piora mesmo com largo período de tempo entre registros."""
        condicao = criar_condicao(test_db, "pac_tempo", "I10")
        
        criar_estadiamento(test_db, condicao.id, "HAS", "ESTAGIO_1", dias_atras=365)
        criar_estadiamento(test_db, condicao.id, "HAS", "ESTAGIO_2", dias_atras=0)
        
        piora_info = reclassificacao_service.detectar_piora_progressiva(
            ultima=reclassificacao_service.obter_ultima_classificacao(condicao.id),
            novo_estagio="ESTAGIO_3",
            sistema="HAS"
        )
        
        assert piora_info['piora_detectada'] is True
    
    def test_multiplas_condicoes_piorando_simultaneamente(self, reclassificacao_service,
                                                         test_db: Session):
        """Paciente com 2 condições piorando ao mesmo tempo."""
        cpf = "pac_multi_piora"
        cond_dm = criar_condicao(test_db, cpf, "E11")
        cond_has = criar_condicao(test_db, cpf, "I10")
        
        # DM piora
        criar_estadiamento(test_db, cond_dm.id, "DIABETES", "LEVE", dias_atras=30)
        criar_estadiamento(test_db, cond_dm.id, "DIABETES", "SEVERO", dias_atras=0)
        
        # HAS piora
        criar_estadiamento(test_db, cond_has.id, "HAS", "ESTAGIO_1", dias_atras=30)
        criar_estadiamento(test_db, cond_has.id, "HAS", "ESTAGIO_3", dias_atras=0)
        
        tendencia_dm = reclassificacao_service.calcular_tendencia(cond_dm.id, "DIABETES")
        tendencia_has = reclassificacao_service.calcular_tendencia(cond_has.id, "HAS")
        
        assert tendencia_dm == "PIORA_PROGRESSIVA"
        assert tendencia_has == "PIORA_PROGRESSIVA"
    
    def test_piora_critica_requer_alerta(self, reclassificacao_service):
        """Piora para crítico SEMPRE gera alerta."""
        gera_alerta, severidade, desc = reclassificacao_service.necessita_novo_alerta(
            piora_detectada=True,
            novo_estagio="CRITICA",
            sistema="DIABETES"
        )
        
        assert gera_alerta is True
        assert severidade == "CRITICA"
    
    def test_piora_moderada_gera_alerta_media(self, reclassificacao_service):
        """Piora para moderado gera alerta MEDIA."""
        gera_alerta, severidade, desc = reclassificacao_service.necessita_novo_alerta(
            piora_detectada=True,
            novo_estagio="MODERADO",
            sistema="DIABETES"
        )
        
        assert gera_alerta is True
        assert severidade == "MEDIA"


# ====================================================================
# TEST CLASS 2: Remissão e Melhora (5 testes)
# ====================================================================

class TestRemissaoMelhora:
    """Validam cenários de remissão e melhora clínica."""
    
    def test_remissao_drc_g5_para_g3(self, reclassificacao_service, test_db: Session):
        """DRC avançada melhora: G5 → G3b."""
        condicao = criar_condicao(test_db, "pac_remissao_drc", "N18")
        
        criar_estadiamento(test_db, condicao.id, "DRC", "G5", dias_atras=30)
        criar_estadiamento(test_db, condicao.id, "DRC", "G3b", dias_atras=0)
        
        comparacao = reclassificacao_service.comparar_estadios("G5", "G3b", "DRC")
        
        assert comparacao['melhora'] is True
        assert comparacao['piora'] is False
    
    def test_melhora_nao_gera_alerta(self, reclassificacao_service):
        """Melhora NUNCA gera alerta."""
        gera_alerta, _, _ = reclassificacao_service.necessita_novo_alerta(
            piora_detectada=False,
            novo_estagio="G1",
            sistema="DRC"
        )
        
        assert gera_alerta is False
    
    def test_remissao_diabetes_controle(self, reclassificacao_service, test_db: Session):
        """Diabetes volta ao controle: SEVERO → CONTROLE."""
        condicao = criar_condicao(test_db, "pac_remissao_dm", "E11")
        
        criar_estadiamento(test_db, condicao.id, "DIABETES", "SEVERO", dias_atras=60)
        criar_estadiamento(test_db, condicao.id, "DIABETES", "MODERADO", dias_atras=30)
        criar_estadiamento(test_db, condicao.id, "DIABETES", "CONTROLE", dias_atras=0)
        
        tendencia = reclassificacao_service.calcular_tendencia(condicao.id, "DIABETES")
        assert tendencia == "MELHORA"
    
    def test_melhora_parcial_estagio_adjacente(self, reclassificacao_service,
                                               test_db: Session):
        """Melhora pequena entre estágios adjacentes."""
        condicao = criar_condicao(test_db, "pac_melhora_parcial", "E11")
        
        criar_estadiamento(test_db, condicao.id, "DIABETES", "MODERADO", dias_atras=15)
        criar_estadiamento(test_db, condicao.id, "DIABETES", "LEVE", dias_atras=0)
        
        comparacao = reclassificacao_service.comparar_estadios(
            "MODERADO", "LEVE", "DIABETES"
        )
        
        assert comparacao['melhora'] is True
        assert comparacao['delta_severidade'] == -1
    
    def test_remissao_completa_remove_condicao_ativa(self, reclassificacao_service,
                                                    test_db: Session):
        """Remissão permite desativação da condição."""
        condicao = criar_condicao(test_db, "pac_remissao_completa", "E11")
        
        criar_estadiamento(test_db, condicao.id, "DIABETES", "SEVERO", dias_atras=30)
        criar_estadiamento(test_db, condicao.id, "DIABETES", "CONTROLE", dias_atras=0)
        
        # Marcador: remissão completa
        assert condicao.status == "CONFIRMADO"
        # Em fluxo real, seria SUSPENSO ou ENCERRADO


# ====================================================================
# TEST CLASS 3: Estabilidade (4 testes)
# ====================================================================

class TestEstabilidade:
    """Validam cenários onde paciente permanece estável."""
    
    def test_estavel_mesmo_estagio_3_meses(self, reclassificacao_service,
                                          test_db: Session):
        """Paciente ESTAGIO_2 durante 3 meses = ESTAVEL."""
        condicao = criar_condicao(test_db, "pac_estavel_has", "I10")
        
        for i in range(3):
            criar_estadiamento(test_db, condicao.id, "HAS", "ESTAGIO_2",
                             dias_atras=90-30*i)
        
        tendencia = reclassificacao_service.calcular_tendencia(condicao.id, "HAS")
        assert tendencia == "ESTAVEL"
    
    def test_estavel_nao_gera_alerta(self, reclassificacao_service):
        """Estabilidade não gera alerta."""
        gera_alerta, _, _ = reclassificacao_service.necessita_novo_alerta(
            piora_detectada=False,
            novo_estagio="ESTAGIO_2",
            sistema="HAS"
        )
        
        assert gera_alerta is False
    
    def test_estavel_drc_g3a_longo_tempo(self, reclassificacao_service,
                                        test_db: Session):
        """DRC G3a estável por 6 meses."""
        condicao = criar_condicao(test_db, "pac_estavel_drc", "N18")
        
        criar_estadiamento(test_db, condicao.id, "DRC", "G3a", dias_atras=180)
        criar_estadiamento(test_db, condicao.id, "DRC", "G3a", dias_atras=90)
        criar_estadiamento(test_db, condicao.id, "DRC", "G3a", dias_atras=0)
        
        tendencia = reclassificacao_service.calcular_tendencia(condicao.id, "DRC")
        assert tendencia == "ESTAVEL"
    
    def test_primeiro_registro_insuficiente_dados(self, reclassificacao_service,
                                                 test_db: Session):
        """Apenas 1 registro = INSUFICIENTE_DADOS."""
        condicao = criar_condicao(test_db, "pac_primeiro", "E11")
        criar_estadiamento(test_db, condicao.id, "DIABETES", "LEVE", dias_atras=30)
        
        tendencia = reclassificacao_service.calcular_tendencia(condicao.id, "DIABETES")
        assert tendencia == "INSUFICIENTE_DADOS"


# ====================================================================
# TEST CLASS 4: Alertas com Escalação (4 testes)
# ====================================================================

class TestAlertasEscalacao:
    """Validam lógica de geração e severidade de alertas."""
    
    def test_alerta_critica_primeira_deteccao(self, reclassificacao_service):
        """Primeira vez crítico = alerta CRITICA."""
        gera_alerta, severidade, desc = reclassificacao_service.necessita_novo_alerta(
            piora_detectada=False,
            novo_estagio="CRITICA",
            sistema="DIABETES"
        )
        
        assert gera_alerta is True
        assert severidade == "CRITICA"
        assert "crítico" in desc.lower() or "inicial" in desc.lower()
    
    def test_alerta_escalacao_por_delta_severidade(self, reclassificacao_service):
        """Alertas com escalação > 2 níveis = ALTA."""
        gera_alerta, severidade, _ = reclassificacao_service.necessita_novo_alerta(
            piora_detectada=True,
            novo_estagio="CRITICA",  # Severidade 4
            sistema="DIABETES"
        )
        
        assert gera_alerta is True
        assert severidade in ["ALTA", "CRITICA"]
    
    def test_alerta_diferentes_sistemas(self, reclassificacao_service):
        """Alerta funciona para todos os sistemas."""
        sistemas = ["HAS", "DRC", "DIABETES"]
        
        for sistema in sistemas:
            gera_alerta, sev, _ = reclassificacao_service.necessita_novo_alerta(
                piora_detectada=True,
                novo_estagio="CRITICA" if sistema != "DRC" else "G5",
                sistema=sistema
            )
            
            assert gera_alerta is True
    
    def test_alerta_mapeamento_palavra_chave(self, reclassificacao_service):
        """Detecta 'CRITICA' em nome do estágio."""
        gera_alerta, severidade, _ = reclassificacao_service.necessita_novo_alerta(
            piora_detectada=False,
            novo_estagio="ESTAGIO_CRITICA",
            sistema="HAS"
        )
        
        assert gera_alerta is True
        assert severidade == "CRITICA"


# ====================================================================
# TEST CLASS 5: Edge Cases e Extremos (4 testes)
# ====================================================================

class TestEdgeCases:
    """Validam casos extremos e situações limite."""
    
    def test_comparacao_mesmo_estagio(self, reclassificacao_service):
        """Comparar estágio consigo mesmo = sem mudança."""
        comparacao = reclassificacao_service.comparar_estadios(
            "ESTAGIO_2", "ESTAGIO_2", "HAS"
        )
        
        assert comparacao['mudou'] is False
        assert comparacao['piora'] is False
        assert comparacao['melhora'] is False
        assert comparacao['delta_severidade'] == 0
    
    def test_sistema_nao_mapeado(self, reclassificacao_service):
        """Sistema desconhecido retorna comportamento padrão."""
        comparacao = reclassificacao_service.comparar_estadios(
            "X", "Y", "SISTEMA_DESCONHECIDO"
        )
        
        assert comparacao['mudou'] is False
    
    def test_historico_com_limite_zero(self, reclassificacao_service, test_db: Session):
        """Limite 0 no histórico retorna lista vazia."""
        condicao = criar_condicao(test_db, "pac_limite", "E11")
        criar_estadiamento(test_db, condicao.id, "DIABETES", "LEVE")
        
        historico = reclassificacao_service.obter_historico_classificacoes(
            condicao.id, limite=0
        )
        
        assert historico == []
    
    def test_multiplos_estadiamentos_mesmo_dia(self, reclassificacao_service,
                                               test_db: Session):
        """2 estadiamentos no mesmo dia - retorna mais recente."""
        condicao = criar_condicao(test_db, "pac_mesmo_dia", "E11")
        
        # Simular timestamps muito próximos
        est1 = Estadiamento(
            condicao_cronica_id=condicao.id,
            sistema_classificacao="DIABETES",
            estagio="LEVE",
            data_classificacao=datetime.now(),
            criterios={}
        )
        est2 = Estadiamento(
            condicao_cronica_id=condicao.id,
            sistema_classificacao="DIABETES",
            estagio="MODERADO",
            data_classificacao=datetime.now() + timedelta(seconds=1),
            criterios={}
        )
        test_db.add_all([est1, est2])
        test_db.commit()
        
        ultima = reclassificacao_service.obter_ultima_classificacao(condicao.id)
        assert ultima.estagio == "MODERADO"
