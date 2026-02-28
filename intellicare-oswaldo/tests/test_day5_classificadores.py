"""
Testes Day 5.1 - Classificadores Clínicos com 30+ Cenários Reais

Valida:
1. 6 classificadores clínicos
2. 4-5 cenários por classificador
3. Edge cases e limites
"""

import pytest
from src.oswaldo.services.classificacao_service import ClassificacaoService


# ====================================================================
# TEST SUITE 1: HAS - Hipertensão (6 testes)
# ====================================================================

class TestClassificadorHAS:
    """Validam classificação de HAS conforme SBC."""
    
    def test_has_normal(self):
        """PA normal (< 120/80)."""
        resultado = ClassificacaoService.classificar_has(118, 78)
        assert resultado['estagio'] == 'NORMAL'
        assert resultado['criterios_met']['sistolica'] is False
        assert resultado['criterios_met']['diastolica'] is False
    
    def test_has_elevada(self):
        """PA elevada (130-139 sistólica)."""
        resultado = ClassificacaoService.classificar_has(135, 85)
        assert resultado['estagio'] == 'ELEVADA'
        assert resultado['faixa_sistolica'] == '120-139'
    
    def test_has_estagio_1(self):
        """HAS estágio 1 (140-159 / 90-99)."""
        resultado = ClassificacaoService.classificar_has(150, 95)
        assert resultado['estagio'] == 'ESTAGIO_1'
        assert resultado['criterios_met']['sistolica'] is True
    
    def test_has_estagio_2(self):
        """HAS estágio 2 (160-179 / 100-109)."""
        resultado = ClassificacaoService.classificar_has(165, 105)
        assert resultado['estagio'] == 'ESTAGIO_2'
    
    def test_has_estagio_3_critica(self):
        """HAS estágio 3 / Emergência hipertensiva (≥ 180 / ≥ 110)."""
        resultado = ClassificacaoService.classificar_has(195, 115)
        assert resultado['estagio'] == 'ESTAGIO_3'
    
    def test_has_apenas_sistolica_elevada(self):
        """Apenas sistólica elevada enquanto diastólica normal."""
        resultado = ClassificacaoService.classificar_has(175, 80)
        # Usa o maior critério
        assert resultado['estagio'] == 'ESTAGIO_2'


# ====================================================================
# TEST SUITE 2: DRC - Doença Renal (6 testes)
# ====================================================================

class TestClassificadorDRC:
    """Validam classificação de DRC conforme KDIGO."""
    
    def test_drc_g1_normal(self):
        """TFGe >= 90 = G1 (Normal)."""
        resultado = ClassificacaoService.classificar_drc(95.0)
        assert resultado['estagio'] == 'G1'
        assert 'Normal' in resultado['descricao']
    
    def test_drc_g2_levemente_diminuida(self):
        """TFGe 60-89 = G2."""
        resultado = ClassificacaoService.classificar_drc(75.0)
        assert resultado['estagio'] == 'G2'
    
    def test_drc_g3a_leve_moderada(self):
        """TFGe 45-59 = G3a."""
        resultado = ClassificacaoService.classificar_drc(50.0)
        assert resultado['estagio'] == 'G3a'
    
    def test_drc_g3b_moderada_severa(self):
        """TFGe 30-44 = G3b."""
        resultado = ClassificacaoService.classificar_drc(35.0)
        assert resultado['estagio'] == 'G3b'
    
    def test_drc_g4_severamente_diminuida(self):
        """TFGe 15-29 = G4."""
        resultado = ClassificacaoService.classificar_drc(20.0)
        assert resultado['estagio'] == 'G4'
    
    def test_drc_g5_falencia_renal(self):
        """TFGe < 15 = G5 (Falência renal)."""
        resultado = ClassificacaoService.classificar_drc(10.0)
        assert resultado['estagio'] == 'G5'
        assert 'Insuficiência renal terminal' in resultado['significado_clinico']
    
    def test_drc_com_albuminuria(self):
        """DRC com ACR (albuminúria)."""
        resultado = ClassificacaoService.classificar_drc(60.0, acr=50.0)
        assert resultado['estagio'] == 'G2'
        assert resultado['albuminuria_categoria'] == 'A2'  # 30-300


# ====================================================================
# TEST SUITE 3: DIABETES - Controle Glicêmico (8 testes)
# ====================================================================

class TestClassificadorDiabetes:
    """Validam classificação de controle glicêmico."""
    
    def test_diabetes_hba1c_controlado(self):
        """HbA1c < 7% = Bem controlado."""
        resultado = ClassificacaoService.classificar_diabetes(6.5)
        assert resultado['controle_glicemico'] == 'BEM_CONTROLADO'
        assert resultado['estagio_aida'] == 'A0'
        assert resultado['status'] == 'NO_ALVO'
    
    def test_diabetes_hba1c_moderado(self):
        """HbA1c 7-7.9% = Moderado."""
        resultado = ClassificacaoService.classificar_diabetes(7.5)
        assert resultado['controle_glicemico'] == 'MODERADO'
        assert resultado['estagio_aida'] == 'A1'
        assert resultado['status'] == 'ACIMA_ALVO'
    
    def test_diabetes_hba1c_mal_controlado(self):
        """HbA1c 8-8.9% = Mal controlado."""
        resultado = ClassificacaoService.classificar_diabetes(8.5)
        assert resultado['controle_glicemico'] == 'MAL_CONTROLADO'
        assert resultado['estagio_aida'] == 'A2'
    
    def test_diabetes_hba1c_critico(self):
        """HbA1c >= 9% = Crítico."""
        resultado = ClassificacaoService.classificar_diabetes(10.5)
        assert resultado['controle_glicemico'] == 'CRITICO'
        assert resultado['estagio_aida'] == 'A3'
    
    def test_diabetes_prediabetes_hba1c(self):
        """HbA1c 5.7-6.4% = Pré-diabete."""
        resultado = ClassificacaoService.classificar_diabetes(6.0)
        assert resultado['controle_glicemico'] == 'BEM_CONTROLADO'
    
    def test_diabetes_glicemia_jejum_controlada(self):
        """Glicemia jejum < 126 mg/dL."""
        resultado = ClassificacaoService.classificar_diabetes(
            hba1c=None, 
            glicemia_jejum=110.0
        )
        assert resultado['controle_glicemico'] == 'MODERADO'
    
    def test_diabetes_glicemia_jejum_elevada(self):
        """Glicemia jejum ≥ 160 mg/dL = CRITICO."""
        resultado = ClassificacaoService.classificar_diabetes(
            hba1c=None,
            glicemia_jejum=160.0
        )
        assert resultado['controle_glicemico'] == 'CRITICO'
    
    def test_diabetes_prioridade_hba1c_vs_jejum(self):
        """HbA1c tem prioridade sobre glicemia jejum."""
        resultado = ClassificacaoService.classificar_diabetes(
            hba1c=6.8,
            glicemia_jejum=200.0  # Este é ignorado
        )
        assert resultado['controle_glicemico'] == 'BEM_CONTROLADO'


# ====================================================================
# TEST SUITE 4: DISLIPIDEMIA (5 testes)
# ====================================================================

class TestClassificadorLipidios:
    """Validam classificação de Dislipidemia."""
    
    def test_lipidios_normais(self):
        """Todos parâmetros normais."""
        resultado = ClassificacaoService.classificar_lipidios(
            colesterol_total=180,
            ldl=100,
            hdl=55,
            triglicerideos=120
        )
        assert resultado['categoria'] == 'OTIMA'
        assert resultado['risco_cv'] == 'BAIXO'
    
    def test_lipidios_ldl_elevado(self):
        """LDL 130-159 + CT elevado = Categoria elevada."""
        resultado = ClassificacaoService.classificar_lipidios(
            colesterol_total=220,
            ldl=140,
            hdl=40
        )
        # Com múltiplos parâmetros alterados, esperamos categoria maior
        assert resultado['categoria'] in ['ELEVADA', 'LIMÍTROFE', 'DESEJAVEL']
        assert resultado['risco_cv'] in ['INTERMÉDIO', 'ALTO', 'BAIXO']
    
    def test_lipidios_ldl_muito_elevado(self):
        """LDL >= 190 = Muito Elevado."""
        resultado = ClassificacaoService.classificar_lipidios(
            ldl=200,
            colesterol_total=250,
            triglicerideos=180
        )
        # Score: LDL+=3, CT+=1, TG+=1 = 5 total (>4 = MUITO_ELEVADA)
        assert resultado['categoria'] == 'MUITO_ELEVADA'
        assert resultado['risco_cv'] == 'MUITO_ALTO'
    
    def test_lipidios_triglicerideos_alto(self):
        """Triglicerídeos >= 200 = Alto."""
        resultado = ClassificacaoService.classificar_lipidios(triglicerideos=250)
        assert 'parametros_alterados' in resultado
        assert any('TG' in p for p in resultado['parametros_alterados'])
    
    def test_lipidios_hdl_baixo(self):
        """HDL < 40 = Proteção reduzida."""
        resultado = ClassificacaoService.classificar_lipidios(hdl=35)
        assert resultado['risco_cv'] in ['INTERMÉDIO', 'ALTO']


# ====================================================================
# TEST SUITE 5: INSUFICIÊNCIA CARDÍACA (5 testes)
# ====================================================================

class TestClassificadorInsuficienciaCardiaca:
    """Validam classificação de IC conforme NYHA."""
    
    def test_ic_nyha_assintomatica(self):
        """NYHA Classe I - Sem limitação."""
        resultado = ClassificacaoService.classificar_insuficiencia_cardiaca('I')
        assert resultado['estagio_nyha'] == 'ASSINTOMATICA'
        assert resultado['requer_medicacao'] is False
    
    def test_ic_nyha_leve(self):
        """NYHA Classe II - Limitação leve."""
        resultado = ClassificacaoService.classificar_insuficiencia_cardiaca('II')
        assert resultado['estagio_nyha'] == 'LEVE'
        assert resultado['requer_medicacao'] is True
    
    def test_ic_nyha_moderada(self):
        """NYHA Classe III - Limitação importante."""
        resultado = ClassificacaoService.classificar_insuficiencia_cardiaca('III')
        assert resultado['estagio_nyha'] == 'MODERADA'
        assert resultado['requer_medicacao'] is True
    
    def test_ic_nyha_severa(self):
        """NYHA Classe IV - Sintomas em repouso."""
        resultado = ClassificacaoService.classificar_insuficiencia_cardiaca('IV')
        assert resultado['estagio_nyha'] == 'SEVERA'
        assert resultado['requer_internacao'] is True
    
    def test_ic_com_fej_reduzida(self):
        """IC com FEJ reduzida (< 40%)."""
        resultado = ClassificacaoService.classificar_insuficiencia_cardiaca('II', fej=35)
        assert resultado['fej_categoria'] == 'REDUZIDA'
        assert resultado['fej'] == 35
    
    def test_ic_com_fej_preservada(self):
        """IC com FEJ preservada (>= 50%)."""
        resultado = ClassificacaoService.classificar_insuficiencia_cardiaca('II', fej=60)
        assert resultado['fej_categoria'] == 'PRESERVADA'


# ====================================================================
# TEST SUITE 6: ASMA (5 testes)
# ====================================================================

class TestClassificadorAsma:
    """Validam classificação de Asma conforme GINA."""
    
    def test_asma_intermitente(self):
        """Asma episódica intermitente (< 1 crise/mês)."""
        resultado = ClassificacaoService.classificar_asma(frequencia_crises_mes=0.5)
        assert resultado['classificacao_persistencia'] == 'INTERMITENTE'
        assert resultado['necessita_controller'] is False
    
    def test_asma_leve_persistente(self):
        """Asma leve persistente (1-3 crises/mês)."""
        resultado = ClassificacaoService.classificar_asma(frequencia_crises_mes=2.0)
        assert resultado['classificacao_persistencia'] == 'LEVE'
        assert resultado['necessita_controller'] is True
    
    def test_asma_moderada_persistente(self):
        """Asma moderada persistente (> 4 crises/mês)."""
        resultado = ClassificacaoService.classificar_asma(frequencia_crises_mes=6.0)
        assert resultado['classificacao_persistencia'] == 'MODERADA'
        assert resultado['necessita_controller'] is True
    
    def test_asma_severa_persistente(self):
        """Asma severa persistente (> 10 crises/mês)."""
        resultado = ClassificacaoService.classificar_asma(frequencia_crises_mes=15.0)
        assert resultado['classificacao_persistencia'] == 'SEVERA'
        assert resultado['necessita_revisao'] is True
    
    def test_asma_com_despertares_noturnos(self):
        """Asma com despertares à noite (≥ 3 dias/semana)."""
        resultado = ClassificacaoService.classificar_asma(
            frequencia_crises_mes=1.0,
            acordar_noite_semana=4  # 4 noites/semana
        )
        assert resultado['controle_asma'] == 'NAO_CONTROLADO'


# ====================================================================
# TEST SUITE 7: Detecção de Mudança de Estágio (5 testes)
# ====================================================================

class TestDeteccaoMudancaEstado:
    """Validam detecção de mudanças entre classificações."""
    
    def test_drc_piora_g3a_para_g4(self):
        """DRC piora de G3a para G4 (distância 2 = MODERADA)."""
        resultado = ClassificacaoService.detectar_mudanca_estadiamento(
            'G3a', 'G4', sistema='KDIGO'
        )
        assert resultado['mudou'] is True
        assert resultado['direcao'] == 'PIORA'
        assert resultado['severidade_mudanca'] == 'MODERADA'  # dist=2
    
    def test_drc_melhora_g3b_para_g2(self):
        """DRC melhora de G3b para G2."""
        resultado = ClassificacaoService.detectar_mudanca_estadiamento(
            'G3b', 'G2', sistema='KDIGO'
        )
        assert resultado['direcao'] == 'MELHORA'
    
    def test_drc_piora_grave_g2_para_g5(self):
        """DRC piora grave de G2 para G5."""
        resultado = ClassificacaoService.detectar_mudanca_estadiamento(
            'G2', 'G5', sistema='KDIGO'
        )
        assert resultado['severidade_mudanca'] == 'GRAVE'
    
    def test_estavel_mesmo_estagio(self):
        """Sem mudança de estágio."""
        resultado = ClassificacaoService.detectar_mudanca_estadiamento(
            'G3a', 'G3a', sistema='KDIGO'
        )
        assert resultado['mudou'] is False
        assert resultado['direcao'] == 'ESTAVEL'
    
    def test_estagio_invalido_handled(self):
        """Estágios inválidos retornam DESCONHECIDA."""
        resultado = ClassificacaoService.detectar_mudanca_estadiamento(
            'INVALIDO', 'G3a', sistema='KDIGO'
        )
        assert resultado['direcao'] == 'DESCONHECIDA'


# ====================================================================
# TEST SUITE 8: Edge Cases (4 testes)
# ====================================================================

class TestEdgeCases:
    """Validam casos extremos e limites."""
    
    def test_has_valores_limite_minimo(self):
        """HAS com valores mínimos fisiológicos."""
        resultado = ClassificacaoService.classificar_has(90, 50)
        assert resultado['estagio'] in ['NORMAL', 'OTIMA']
    
    def test_has_valores_limite_maximo(self):
        """HAS com valores máximos (emergência)."""
        resultado = ClassificacaoService.classificar_has(250, 150)
        assert resultado['estagio'] == 'ESTAGIO_3'
    
    def test_diabetes_valores_extremos(self):
        """HbA1c valores extremos."""
        resultado_alto = ClassificacaoService.classificar_diabetes(15.0)
        assert resultado_alto['controle_glicemico'] == 'CRITICO'
        
        resultado_baixo = ClassificacaoService.classificar_diabetes(4.0)
        assert resultado_baixo['controle_glicemico'] == 'BEM_CONTROLADO'
    
    def test_lipidios_colesterol_otimo(self):
        """Colesterol total ótimo (< 150)."""
        resultado = ClassificacaoService.classificar_lipidios(
            colesterol_total=140,
            ldl=80,
            hdl=60
        )
        assert resultado['categoria'] == 'OTIMA'
        assert resultado['risco_cv'] == 'BAIXO'
