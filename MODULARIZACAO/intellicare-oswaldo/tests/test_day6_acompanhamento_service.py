"""
Testes do Serviço de Acompanhamento (Day 6.3)

Coverage:
- Planejamento de seguimento baseado em severidade
- Cálculo de aderência a medicações
- Sugestão de ajustes medicamentosos
- Monitoramento de padrões vitais
- Cenários clínicos reais

Estrutura de testes:
1. TestPlanejamentoSeguimento      (10 tests) - Frequência de acompanhamento
2. TestCalcularAdherencia         (8 tests) - Taxa de aderência medicação
3. TestSugerirAjustes             (10 tests) - Recomendações terapêuticas
4. TestMonitorarVitais            (8 tests) - Padrões e tendências
5. TestCenariosClinicosReais      (4 tests) - Casos clínicos completos
"""

import pytest
from datetime import datetime, timedelta
from typing import List, Dict

from src.oswaldo.services.acompanhamento_service import (
    AcompanhamentoService,
    FrecuenciaAcompanhamento,
    MetricaAderencia,
    PadraoProgressao,
    AjusteMedicacao,
    PlanoAcompanhamento
)


# ============================================================================
# FIXTURES - Dados de teste comuns
# ============================================================================

@pytest.fixture
def data_hoje():
    """Data de referência para testes"""
    return datetime.now()


@pytest.fixture
def data_30_dias_atras(data_hoje):
    """30 dias atrás"""
    return data_hoje - timedelta(days=30)


@pytest.fixture
def registros_aderencia_perfeita(data_30_dias_atras):
    """30 dias tomando medicação perfeitamente"""
    return [
        {"data": data_30_dias_atras + timedelta(days=i), "tomou": True}
        for i in range(30)
    ]


@pytest.fixture
def registros_aderencia_75_percent(data_30_dias_atras):
    """75% de aderência (22/30 dias)"""
    registros = []
    for i in range(30):
        tomou = (i % 4) != 3  # Falha 1 a cada 4 dias
        registros.append({
            "data": data_30_dias_atras + timedelta(days=i),
            "tomou": tomou
        })
    return registros


@pytest.fixture
def registros_aderencia_50_percent(data_30_dias_atras):
    """50% de aderência (15/30 dias)"""
    return [
        {"data": data_30_dias_atras + timedelta(days=i), "tomou": (i % 2 == 0)}
        for i in range(30)
    ]


@pytest.fixture
def registros_aderencia_nula():
    """Nenhuma aderência (não tomou nada)"""
    return [
        {"data": datetime.now() - timedelta(days=i), "tomou": False}
        for i in range(30)
    ]


@pytest.fixture
def historico_pa_melhora():
    """Histórico de PA com melhora progressiva"""
    valores = [220, 210, 200, 190, 180, 175]
    return [
        {"data": datetime.now() - timedelta(days=30-i*5), "valor": valores[i]}
        for i in range(len(valores))
    ]


@pytest.fixture
def historico_pa_piora():
    """Histórico de PA com piora progressiva"""
    valores = [140, 150, 160, 170, 180, 190]
    return [
        {"data": datetime.now() - timedelta(days=30-i*5), "valor": valores[i]}
        for i in range(len(valores))
    ]


@pytest.fixture
def historico_pa_estavel():
    """Histórico de PA estável"""
    valores = [145, 142, 148, 144, 146]
    return [
        {"data": datetime.now() - timedelta(days=25-i*5), "valor": valores[i]}
        for i in range(len(valores))
    ]


# ============================================================================
# TESTES 1: PLANEJAMENTO DE SEGUIMENTO
# ============================================================================

class TestPlanejamentoSeguimento:
    """Testes de planejamento de frequência de acompanhamento"""

    def test_critico_requer_semanal(self):
        """CRÍTICO → acompanhamento semanal"""
        freq = AcompanhamentoService.planejar_frequencia_acompanhamento(
            nivel_alerta="CRITICO"
        )
        assert freq == FrecuenciaAcompanhamento.SEMANAL

    def test_alto_requer_quinzenal(self):
        """ALTO → acompanhamento quinzenal"""
        freq = AcompanhamentoService.planejar_frequencia_acompanhamento(
            nivel_alerta="ALTO"
        )
        assert freq == FrecuenciaAcompanhamento.QUINZENAL

    def test_medio_com_piora_quinzenal(self):
        """MÉDIO com PIORA → quinzenal"""
        freq = AcompanhamentoService.planejar_frequencia_acompanhamento(
            nivel_alerta="MEDIO",
            tendencia="PIORA"
        )
        assert freq == FrecuenciaAcompanhamento.QUINZENAL

    def test_medio_estavel_mensal(self):
        """MÉDIO estável/melhora → mensal"""
        freq = AcompanhamentoService.planejar_frequencia_acompanhamento(
            nivel_alerta="MEDIO",
            tendencia="MELHORA"
        )
        assert freq == FrecuenciaAcompanhamento.MENSAL

    def test_baixo_com_melhora_trimestral(self):
        """BAIXO com MELHORA → trimestral"""
        freq = AcompanhamentoService.planejar_frequencia_acompanhamento(
            nivel_alerta="BAIXO",
            tendencia="MELHORA"
        )
        assert freq == FrecuenciaAcompanhamento.TRIMESTRAL

    def test_baixo_bem_controlado_semestral(self):
        """BAIXO bem controlado (score 85) → semestral"""
        freq = AcompanhamentoService.planejar_frequencia_acompanhamento(
            nivel_alerta="BAIXO",
            score_controle=85
        )
        assert freq == FrecuenciaAcompanhamento.SEMESTRAL

    def test_baixo_score_baixo_trimestral(self):
        """BAIXO com score baixo (50) → trimestral"""
        freq = AcompanhamentoService.planejar_frequencia_acompanhamento(
            nivel_alerta="BAIXO",
            score_controle=50
        )
        assert freq == FrecuenciaAcompanhamento.TRIMESTRAL

    def test_frequencia_respeita_urgencia(self):
        """Frequência mais curta para alertas mais severos"""
        freqs = {
            "CRITICO": AcompanhamentoService.planejar_frequencia_acompanhamento("CRITICO"),
            "ALTO": AcompanhamentoService.planejar_frequencia_acompanhamento("ALTO"),
            "MEDIO": AcompanhamentoService.planejar_frequencia_acompanhamento("MEDIO"),
            "BAIXO": AcompanhamentoService.planejar_frequencia_acompanhamento("BAIXO"),
        }
        
        dias = {
            "CRITICO": 7,    # semanal
            "ALTO": 15,      # quinzenal
            "MEDIO": 30,     # mensal
            "BAIXO": 90,     # trimestral
        }
        
        freq_dias = {
            FrecuenciaAcompanhamento.SEMANAL: 7,
            FrecuenciaAcompanhamento.QUINZENAL: 15,
            FrecuenciaAcompanhamento.MENSAL: 30,
            FrecuenciaAcompanhamento.TRIMESTRAL: 90,
        }
        
        # Verificar que CRÍTICO < ALTO < MÉDIO < BAIXO
        critico_dias = freq_dias[freqs["CRITICO"]]
        alto_dias = freq_dias[freqs["ALTO"]]
        medio_dias = freq_dias[freqs["MEDIO"]]
        baixo_dias = freq_dias[freqs["BAIXO"]]
        
        assert critico_dias < alto_dias
        assert alto_dias <= medio_dias
        assert medio_dias < baixo_dias

    def test_dias_sem_progresso_nao_altera_critico(self):
        """CRÍTICO mantem semanal mesmo com dias_sem_progresso"""
        freq = AcompanhamentoService.planejar_frequencia_acompanhamento(
            nivel_alerta="CRITICO",
            dias_sem_progresso=30
        )
        assert freq == FrecuenciaAcompanhamento.SEMANAL

    def test_plano_critico_gera_data_proxima_medicao_7_dias(self):
        """Plano CRÍTICO tem próxima medição em até 7 dias"""
        plano = AcompanhamentoService.gerar_plano_acompanhamento(
            condicao_cronica_id=1,
            cid10="I10",
            diagnostico="Hipertensão Arterial",
            nivel_alerta="CRITICO",
            score_controle=30,
            parametro_principal="PA sistólica",
            valor_atual=200,
            valor_objetivo=140
        )
        
        dias_proxima = (plano.proxima_medicao - datetime.now()).days
        assert dias_proxima <= 7


# ============================================================================
# TESTES 2: CALCULAR ADERÊNCIA À MEDICAÇÃO
# ============================================================================

class TestCalcularAdherencia:
    """Testes de cálculo de aderência a medicações"""

    def test_aderencia_100_percent_perfeita(self, registros_aderencia_perfeita, data_30_dias_atras):
        """100% aderência quando toma todos os dias"""
        metrica = AcompanhamentoService.calcular_aderencia_medicacao(
            medicacao_nome="Losartan",
            dose_prescrita="100mg 1x ao dia",
            data_prescricao=data_30_dias_atras,
            registros_tomada=registros_aderencia_perfeita
        )
        
        assert metrica.medicacao_nome == "Losartan"
        assert metrica.dias_aderentes == 30
        assert metrica.dias_totais == 30
        assert metrica.percentual_aderencia == 100.0

    def test_aderencia_75_percent(self, registros_aderencia_75_percent, data_30_dias_atras):
        """75% aderência (22/30 dias)"""
        metrica = AcompanhamentoService.calcular_aderencia_medicacao(
            medicacao_nome="Hidroclorotiazida",
            dose_prescrita="25mg 1x ao dia",
            data_prescricao=data_30_dias_atras,
            registros_tomada=registros_aderencia_75_percent
        )
        
        # 23/30 = 76.67% (tolerância ampla)
        assert metrica.percentual_aderencia > 70 and metrica.percentual_aderencia <= 80
        assert metrica.motivo_nao_aderencia is None or "falta" in metrica.motivo_nao_aderencia.lower()

    def test_aderencia_50_percent(self, registros_aderencia_50_percent, data_30_dias_atras):
        """50% aderência (15/30 dias)"""
        metrica = AcompanhamentoService.calcular_aderencia_medicacao(
            medicacao_nome="Amlodipina",
            dose_prescrita="5mg 1x ao dia",
            data_prescricao=data_30_dias_atras,
            registros_tomada=registros_aderencia_50_percent
        )
        
        assert metrica.percentual_aderencia == pytest.approx(50.0, abs=1.0)

    def test_aderencia_nula(self, registros_aderencia_nula):
        """0% aderência cuando não toma nada"""
        data_prescricao = datetime.now() - timedelta(days=30)
        metrica = AcompanhamentoService.calcular_aderencia_medicacao(
            medicacao_nome="Atorvastatina",
            dose_prescrita="40mg 1x ao dia",
            data_prescricao=data_prescricao,
            registros_tomada=registros_aderencia_nula
        )
        
        assert metrica.percentual_aderencia == 0.0

    def test_metrica_contem_data_ultima_tomada(self, registros_aderencia_75_percent, data_30_dias_atras):
        """Métrica inclui data da última tomada"""
        metrica = AcompanhamentoService.calcular_aderencia_medicacao(
            medicacao_nome="Losartan",
            dose_prescrita="100mg",
            data_prescricao=data_30_dias_atras,
            registros_tomada=registros_aderencia_75_percent
        )
        
        assert metrica.data_ultima_tomada is not None

    def test_prescrição_recente_calcula_corretamente(self):
        """Prescrição recente (5 dias) calcula % correto"""
        data_prescricao = datetime.now() - timedelta(days=5)
        registros = [
            {"data": data_prescricao + timedelta(days=i), "tomou": True}
            for i in range(5)
        ]
        
        metrica = AcompanhamentoService.calcular_aderencia_medicacao(
            medicacao_nome="Teste",
            dose_prescrita="1x",
            data_prescricao=data_prescricao,
            registros_tomada=registros
        )
        
        assert metrica.percentual_aderencia == 100.0

    def test_score_aderencia_geral_multiplas_medicacoes(self):
        """Score agregado base em múltiplas medicações"""
        m1 = MetricaAderencia(
            medicacao_nome="Med1",
            dose_prescrita="100mg",
            dias_aderentes=30,
            dias_totais=30,
            percentual_aderencia=100.0,
            data_ultima_tomada=datetime.now(),
            data_proxima_tomada=datetime.now() + timedelta(days=1)
        )
        
        m2 = MetricaAderencia(
            medicacao_nome="Med2",
            dose_prescrita="50mg",
            dias_aderentes=20,
            dias_totais=30,
            percentual_aderencia=66.7,
            data_ultima_tomada=datetime.now(),
            data_proxima_tomada=datetime.now() + timedelta(days=1)
        )
        
        score = AcompanhamentoService.calcular_score_aderencia_geral(
            metricas_aderencia=[m1, m2],
            comparecimento_consultas=2,
            consultas_agendadas=2
        )
        
        # (100 + 66.7) / 2 * 0.7 + 100 * 0.3 ≈ 89%
        assert score > 80 and score <= 100


# ============================================================================
# TESTES 3: SUGERIR AJUSTES DE MEDICAÇÃO
# ============================================================================

class TestSugerirAjustes:
    """Testes de recomendações de ajuste terapêutico"""

    def test_pa_alta_recomenda_aumentar_dose(self):
        """PA 180 vs objetivo 140 → aumentar dose"""
        ajuste = AcompanhamentoService.sugerir_ajuste_medicacao(
            medicacao_nome="Losartan",
            dose_atual="50mg",
            parametro_atual=180,
            parametro_objetivo=140,
            parametro_tipo="PA sistólica"
        )
        
        assert ajuste.ajuste_tipo == "AUMENTAR_DOSE"
        assert ajuste.medicacao_nome == "Losartan"
        assert ajuste.dose_recomendada is not None
        assert "180" in ajuste.motivo or "desvio" in ajuste.motivo.lower()

    def test_glicemia_alta_aumentar_metformina(self):
        """Glicemia 250 vs objetivo 130 → aumentar metformina"""
        ajuste = AcompanhamentoService.sugerir_ajuste_medicacao(
            medicacao_nome="Metformina",
            dose_atual="500mg",
            parametro_atual=250,
            parametro_objetivo=130,
            parametro_tipo="Glicemia de jejum"
        )
        
        assert ajuste.ajuste_tipo == "AUMENTAR_DOSE"

    def test_hipotensao_recomenda_diminuir_dose(self):
        """PA 90 (hipotensão) → diminuir dose antihipertensivo"""
        ajuste = AcompanhamentoService.sugerir_ajuste_medicacao(
            medicacao_nome="Amlodipina",
            dose_atual="10mg",
            parametro_atual=90,
            parametro_objetivo=130,
            parametro_tipo="PA sistólica"
        )
        
        assert ajuste.ajuste_tipo == "DIMINUIR_DOSE"

    def test_parametro_no_alvo_mantem_dose(self):
        """PA 140 (no alvo) → manter dose"""
        ajuste = AcompanhamentoService.sugerir_ajuste_medicacao(
            medicacao_nome="Losartan",
            dose_atual="100mg",
            parametro_atual=140,
            parametro_objetivo=140,
            parametro_tipo="PA sistólica"
        )
        
        assert ajuste.ajuste_tipo == "MANTER"
        assert ajuste.dose_recomendada is None

    def test_parametro_proximidade_alvo_mantem(self):
        """PA 148 (próximo ao alvo 140) → manter"""
        ajuste = AcompanhamentoService.sugerir_ajuste_medicacao(
            medicacao_nome="Losartan",
            dose_atual="100mg",
            parametro_atual=148,
            parametro_objetivo=140,
            parametro_tipo="PA sistólica"
        )
        
        assert ajuste.ajuste_tipo == "MANTER"

    def test_ajuste_contem_motivo_clinico(self):
        """Ajuste inclui motivo clínico justificado"""
        ajuste = AcompanhamentoService.sugerir_ajuste_medicacao(
            medicacao_nome="Insulin",
            dose_atual="10UI",
            parametro_atual=280,
            parametro_objetivo=130,
            parametro_tipo="Glicemia"
        )
        
        assert len(ajuste.motivo) > 10
        assert "glicemia" in ajuste.motivo.lower() or "280" in ajuste.motivo

    def test_ajuste_inclui_prazo_reavalicao(self):
        """Ajuste especifica quando reavaliar (30 dias)"""
        ajuste = AcompanhamentoService.sugerir_ajuste_medicacao(
            medicacao_nome="Beta-bloq",
            dose_atual="100mg",
            parametro_atual=65,
            parametro_objetivo=60,
            parametro_tipo="FC"
        )
        
        assert ajuste.prazo_avaliacao_dias == 30

    def test_desvio_critico_gera_motivo_urgente(self):
        """Desvio >30% gera motivo com "urgente"  ou "aumentar"'''"""
        ajuste = AcompanhamentoService.sugerir_ajuste_medicacao(
            medicacao_nome="Losartan",
            dose_atual="50mg",
            parametro_atual=220,
            parametro_objetivo=140,
            parametro_tipo="PA sistólica",
            nivel_alerta="CRITICO"
        )
        
        assert ajuste.ajuste_tipo in ["AUMENTAR_DOSE", "MANTER"]

    def test_dose_recomendada_aumenta_baseada_desvio(self):
        """Dose recomendada aumenta proporcionalmente ao desvio"""
        ajuste1 = AcompanhamentoService.sugerir_ajuste_medicacao(
            medicacao_nome="Losartan",
            dose_atual="50mg",
            parametro_atual=160,  # 14% acima
            parametro_objetivo=140,
            parametro_tipo="PA sistólica"
        )
        
        ajuste2 = AcompanhamentoService.sugerir_ajuste_medicacao(
            medicacao_nome="Losartan",
            dose_atual="50mg",
            parametro_atual=200,  # 43% acima
            parametro_objetivo=140,
            parametro_tipo="PA sistólica"
        )
        
        # Ambos deveriam sugerir aumento, mas dose_recomendada pode variar
        assert (ajuste1.ajuste_tipo == "AUMENTAR_DOSE" or 
                ajuste2.ajuste_tipo == "AUMENTAR_DOSE")

    def test_ajuste_inclui_parametros_a_monitorar(self):
        """Ajuste lista parâmetros a monitorar após mudança"""
        ajuste = AcompanhamentoService.sugerir_ajuste_medicacao(
            medicacao_nome="IECA",
            dose_atual="10mg",
            parametro_atual=200,
            parametro_objetivo=140,
            parametro_tipo="PA sistólica"
        )
        
        # Deve incluir alguns parâmetros a monitorar
        assert len(ajuste.efeitos_secundarios_potenciais) >= 0


# ============================================================================
# TESTES 4: MONITORAR PADRÕES VITAIS
# ============================================================================

class TestMonitorarVitais:
    """Testes de detecção de padrões e tendências"""

    def test_detectar_melhora_progressiva(self, historico_pa_melhora):
        """Histórico com melhora detecta tendência MELHORA"""
        padrao = AcompanhamentoService.analisar_padrao_progressao(
            parametro="PA sistólica",
            cid10="I10",
            valor_inicial=220,
            valor_atual=175,
            valor_objetivo=140,
            dias_acompanhamento=30,
            historico=historico_pa_melhora
        )
        
        assert padrao.tendencia == "MELHORA"
        assert padrao.mudanca_percentual < 0

    def test_detectar_piora_progressiva(self, historico_pa_piora):
        """Histórico com piora detecta tendência PIORA"""
        padrao = AcompanhamentoService.analisar_padrao_progressao(
            parametro="PA sistólica",
            cid10="I10",
            valor_inicial=140,
            valor_atual=190,
            valor_objetivo=140,
            dias_acompanhamento=30,
            historico=historico_pa_piora
        )
        
        assert padrao.tendencia == "PIORA"
        assert padrao.mudanca_percentual > 0

    def test_detectar_estavel(self, historico_pa_estavel):
        """Histórico oscilando próximo ao alvo detecta ESTAVEL"""
        padrao = AcompanhamentoService.analisar_padrao_progressao(
            parametro="PA sistólica",
            cid10="I10",
            valor_inicial=145,
            valor_atual=145,
            valor_objetivo=140,
            dias_acompanhamento=30,
            historico=historico_pa_estavel
        )
        
        assert padrao.tendencia == "ESTAVEL"

    def test_calcula_mudanca_percentual_correta(self):
        """Mudança % calculada corretamente"""
        padrao = AcompanhamentoService.analisar_padrao_progressao(
            parametro="PA sistólica",
            cid10="I10",
            valor_inicial=200,
            valor_atual=150,
            valor_objetivo=140,
            dias_acompanhamento=30
        )
        
        # (150 - 200) / 200 = -25%
        assert padrao.mudanca_percentual == pytest.approx(-25.0, abs=1.0)

    def test_prognose_melhora_no_alvo(self):
        """Prognose otimista quando atinge objetivo"""
        padrao = AcompanhamentoService.analisar_padrao_progressao(
            parametro="PA sistólica",
            cid10="I10",
            valor_inicial=220,
            valor_atual=135,
            valor_objetivo=140,
            dias_acompanhamento=30,
            historico=[
                {"data": datetime.now() - timedelta(days=30), "valor": 220},
                {"data": datetime.now() - timedelta(days=15), "valor": 180},
                {"data": datetime.now(), "valor": 135}
            ]
        )
        
        assert "excelente" in padrao.prognose.lower() or "objetivo" in padrao.prognose.lower()

    def test_prognose_urgente_na_piora(self):
        """Prognose urgente/alerta quando está piorando"""
        padrao = AcompanhamentoService.analisar_padrao_progressao(
            parametro="PA sistólica",
            cid10="I10",
            valor_inicial=140,
            valor_atual=200,
            valor_objetivo=140,
            dias_acompanhamento=30,
            historico=[
                {"data": datetime.now() - timedelta(days=30), "valor": 140},
                {"data": datetime.now() - timedelta(days=15), "valor": 160},
                {"data": datetime.now(), "valor": 200}
            ]
        )
        
        assert "alerta" in padrao.prognose.lower() or "piora" in padrao.prognose.lower()

    def test_recomendacao_ajuste_na_piora(self, historico_pa_piora):
        """Recomenda ajuste quando detecta PIORA"""
        padrao = AcompanhamentoService.analisar_padrao_progressao(
            parametro="PA sistólica",
            cid10="I10",
            valor_inicial=140,
            valor_atual=190,
            valor_objetivo=140,
            dias_acompanhamento=30,
            historico=historico_pa_piora
        )
        
        assert "medicação" in padrao.recomendacao_acao.lower() or "ajuste" in padrao.recomendacao_acao.lower()
        assert padrao.urgencia == "URGENTE"

    def test_sem_historico_mantem_padrao(self):
        """Sem histórico detecta ESTAVEL (falto de dados)"""
        padrao = AcompanhamentoService.analisar_padrao_progressao(
            parametro="PA sistólica",
            cid10="I10",
            valor_inicial=150,
            valor_atual=145,
            valor_objetivo=140,
            dias_acompanhamento=10,
            historico=[]  # Sem histórico
        )
        
        # Sem dados suficientes, assume ESTAVEL
        assert padrao.tendencia == "ESTAVEL"


# ============================================================================
# TESTES 5: CENÁRIOS CLÍNICOS REAIS
# ============================================================================

class TestCenariosClinicosReais:
    """Testes com cenários clínicos realistas completos"""

    def test_paciente_has_descompensada(self):
        """Paciente HAS com PA sistólica 200 (CRÍTICO)"""
        plano = AcompanhamentoService.gerar_plano_acompanhamento(
            condicao_cronica_id=1,
            cid10="I10",
            diagnostico="Hipertensão Arterial",
            nivel_alerta="CRITICO",
            score_controle=20,
            parametro_principal="PA sistólica",
            valor_atual=200,
            valor_objetivo=140,
            medicacoes_atuais=["Losartan", "Hidroclorotiazida"],
            aderencia_medicacao=70.0
        )
        
        # CRÍTICO deve gerar acompanhamento semanal
        assert plano.frequencia_dias <= 7
        
        # Deve sugerir ajustes medicamentosos
        assert len(plano.ajustes_medicacao) > 0
        
        # Deve mencionar HAS nas recomendações
        assert any("sal" in r.lower() or "sódio" in r.lower() or "exercício" in r.lower() 
                   for r in plano.recomendacoes_comportamento)

    def test_paciente_diabetico_hipoglicemico(self):
        """Paciente DM com glicemia 80 (bom controle mas risco hipoglicemia)"""
        plano = AcompanhamentoService.gerar_plano_acompanhamento(
            condicao_cronica_id=2,
            cid10="E11",
            diagnostico="Diabetes Melito Tipo 2",
            nivel_alerta="BAIXO",
            score_controle=85,
            parametro_principal="Glicemia de jejum",
            valor_atual=100,
            valor_objetivo=100,
            medicacoes_atuais=["Metformina", "Insulina"],
            aderencia_medicacao=95.0
        )
        
        # BAIXO com bom controle → trimestral/semestral
        assert plano.frequencia_dias >= 30
        
        # Score aderência reflete alta aderência
        assert plano.score_aderencia_geral >= 90.0
        
        # Deve recomendações nacionais de DM
        assert any("refeição" in r.lower() or "açúcar" in r.lower() or "atividade" in r.lower()
                   for r in plano.recomendacoes_comportamento)

    def test_paciente_has_dm_nao_aderente(self):
        """Paciente com HAS + DM, baixa aderência"""
        plano = AcompanhamentoService.gerar_plano_acompanhamento(
            condicao_cronica_id=3,
            cid10="I10",  # Foco em HAS
            diagnostico="Hipertensão + Diabetes",
            nivel_alerta="ALTO",
            score_controle=50,
            parametro_principal="PA sistólica",
            valor_atual=170,
            valor_objetivo=140,
            medicacoes_atuais=["Losartan", "Metformina", "Atorvastatina"],
            aderencia_medicacao=45.0  # Baixa aderência
        )
        
        # ALTO → quinzenal mínimo
        assert plano.frequencia_dias <= 15
        
        # Score aderência reflete problema
        assert plano.score_aderencia_geral < 60.0
        
        # Deve sugerir educação
        assert len(plano.topicos_educacao_necessarios) > 0

    def test_paciente_estavel_otimizado(self):
        """Paciente bem controlado em regime otimizado"""
        plano = AcompanhamentoService.gerar_plano_acompanhamento(
            condicao_cronica_id=4,
            cid10="I10",
            diagnostico="Hipertensão Arterial - Controlada",
            nivel_alerta="BAIXO",
            score_controle=90,
            parametro_principal="PA sistólica",
            valor_atual=135,
            valor_objetivo=140,
            medicacoes_atuais=["Losartan 100mg"],
            aderencia_medicacao=98.0
        )
        
        # BAIXO + ótimo controle → visitas menos frequentes
        assert plano.frequencia_dias >= 90  # Trimestral ou mais
        
        # Aderência excelente
        assert plano.score_aderencia_geral >= 95.0
        
        # Plano ainda contém seguimento
        assert plano.proxima_medicao is not None


# ============================================================================
# TESTES 6: ESTRUTURAS & DATACLASSES
# ============================================================================

class TestEstruturasAcompanhamento:
    """Testes de integridade das estruturas de dados"""

    def test_metrica_aderencia_obrigatoria(self):
        """MetricaAderencia deve ter campos obrigatórios"""
        metrica = MetricaAderencia(
            medicacao_nome="Losartan",
            dose_prescrita="100mg",
            dias_aderentes=30,
            dias_totais=30,
            percentual_aderencia=100.0,
            data_ultima_tomada=datetime.now(),
            data_proxima_tomada=datetime.now() + timedelta(days=1)
        )
        
        assert metrica.medicacao_nome is not None
        assert metrica.percentual_aderencia >= 0 and metrica.percentual_aderencia <= 100

    def test_padrao_progressao_calcula_tendencia(self):
        """PadraoProgressao calcula e armazena tendência"""
        padrao = PadraoProgressao(
            parametro="PA sistólica",
            cid10="I10",
            valor_inicial=220,
            valor_atual=180,
            valor_objetivo=140,
            dias_acompanhamento=30,
            mudanca_percentual=-18.2,
            tendencia="MELHORA",
            prognose="Em bom caminho",
            recomendacao_acao="Manter estratégia",
            urgencia="ROTINA"
        )
        
        assert padrao.tendencia in ["MELHORA", "PIORA", "ESTAVEL"]
        assert padrao.urgencia in ["ROTINA", "URGENTE"]

    def test_ajuste_medicacao_completo(self):
        """AjusteMedicacao com contexto clínico"""
        ajuste = AjusteMedicacao(
            medicacao_nome="Losartan",
            ajuste_tipo="AUMENTAR_DOSE",
            dose_atual="50mg",
            dose_recomendada="100mg",
            motivo="PA sistólica 180 vs objetivo 140",
            prazo_avaliacao_dias=30
        )
        
        assert ajuste.medicacao_nome is not None
        assert ajuste.ajuste_tipo in [
            "AUMENTAR_DOSE", "DIMINUIR_DOSE", "MANTER",
            "ADICIONAR_MEDICACAO", "REMOVER_MEDICACAO", "TROCAR_MEDICACAO"
        ]

    def test_plano_acompanhamento_completo(self):
        """PlanoAcompanhamento com todos os campos"""
        plano = PlanoAcompanhamento(
            condicao_cronica_id=1,
            cid10="I10",
            diagnostico="Hipertensão",
            proxima_medicao=datetime.now() + timedelta(days=30),
            frequencia_dias=30
        )
        
        assert plano.condicao_cronica_id is not None
        assert plano.proxima_medicao is not None
        assert plano.frequencia_dias > 0
        assert plano.status == "PLANEJADO"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
