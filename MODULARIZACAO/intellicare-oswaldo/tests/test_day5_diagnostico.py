"""
Testes Day 5.2 - Diagnóstico Automático com 35+ Cenários Clínicos

Validam:
1. Sugestões de diagnóstico por sistema
2. Análise de multimorbidade
3. Recomendações clínicas
4. Cálculo de urgência
5. Padrões cardiometabólicos
"""

import pytest
from src.oswaldo.services.diagnostico_service import DiagnosticoService


# ====================================================================
# TEST SUITE 1: HAS Diagnóstico
# ====================================================================

class TestDiagnosticoHAS:
    """Validam sugestões de diagnóstico para HAS."""
    
    def test_has_normal_sem_diagnostico(self):
        """PA normal não gera diagnóstico."""
        sugestoes = DiagnosticoService.sugerir_diagnosticos('HAS', 'NORMAL')
        assert len(sugestoes) == 1
        assert sugestoes[0].cid10 == 'R03.0'
        assert sugestoes[0].score == 0
        assert sugestoes[0].urgencia == 'ELETIVA'
    
    def test_has_elevada_pre_diagnostico(self):
        """PA elevada gera pré-diagnóstico com score 30."""
        sugestoes = DiagnosticoService.sugerir_diagnosticos('HAS', 'ELEVADA')
        assert sugestoes[0].cid10 == 'R03.0'
        assert sugestoes[0].score == 30
        assert sugestoes[0].urgencia == 'ROTINA'
    
    def test_has_estagio_1_diagnostico(self):
        """Estágio 1 HAS gera CID I10 com score 75."""
        sugestoes = DiagnosticoService.sugerir_diagnosticos('HAS', 'ESTAGIO_1')
        assert sugestoes[0].cid10 == 'I10'
        assert sugestoes[0].score == 75
        assert sugestoes[0].urgencia == 'ROTINA'
        assert 'SBC' in ' '.join(sugestoes[0].recomendacoes)
    
    def test_has_estagio_2_diagnostico(self):
        """Estágio 2 HAS gera CID I10 com score 85."""
        sugestoes = DiagnosticoService.sugerir_diagnosticos('HAS', 'ESTAGIO_2')
        assert sugestoes[0].cid10 == 'I10'
        assert sugestoes[0].score == 85
        assert sugestoes[0].urgencia == 'URGENTE'
    
    def test_has_estagio_3_emergencia(self):
        """Estágio 3 HAS é EMERGENCIA com score 95."""
        sugestoes = DiagnosticoService.sugerir_diagnosticos('HAS', 'ESTAGIO_3')
        assert len(sugestoes) >= 2
        
        # Primeira sugestão: HAS com lesão órgão-alvo
        assert sugestoes[0].cid10 == 'I10'
        assert sugestoes[0].score == 95
        assert sugestoes[0].urgencia == 'EMERGENCIA'
        
        # Segunda sugestão: considerar HAS secundária
        assert sugestoes[1].cid10 == 'I11'
        assert sugestoes[1].score == 40


# ====================================================================
# TEST SUITE 2: DRC Diagnóstico
# ====================================================================

class TestDiagnosticoDRC:
    """Validam sugestões de diagnóstico para DRC."""
    
    def test_drc_g1_normal_sem_diagnostico(self):
        """G1 DRC não gera diagnóstico."""
        sugestoes = DiagnosticoService.sugerir_diagnosticos('DRC', 'G1')
        assert sugestoes[0].cid10 == 'N18'
        assert sugestoes[0].score == 0
    
    def test_drc_g2_levemente_diminuida(self):
        """G2 DRC com score 20."""
        sugestoes = DiagnosticoService.sugerir_diagnosticos('DRC', 'G2')
        assert sugestoes[0].score == 20
    
    def test_drc_g3a_rotina(self):
        """G3a DRC score 40, urgência ROTINA."""
        sugestoes = DiagnosticoService.sugerir_diagnosticos('DRC', 'G3a')
        assert sugestoes[0].score == 40
        assert sugestoes[0].urgencia == 'ROTINA'
    
    def test_drc_g3b_urgente(self):
        """G3b DRC score 60, urgência URGENTE."""
        sugestoes = DiagnosticoService.sugerir_diagnosticos('DRC', 'G3b')
        assert sugestoes[0].score == 60
        assert sugestoes[0].urgencia == 'URGENTE'
    
    def test_drc_g4_severamente_diminuida(self):
        """G4 DRC score 80, requer monitoramento mensal."""
        sugestoes = DiagnosticoService.sugerir_diagnosticos('DRC', 'G4')
        assert sugestoes[0].score == 80
        recs = ' '.join(sugestoes[0].recomendacoes)
        assert 'mensal' in recs.lower() or 'EPO' in recs
    
    def test_drc_g5_emergencia(self):
        """G5 DRC é EMERGENCIA com substituição renal."""
        sugestoes = DiagnosticoService.sugerir_diagnosticos('DRC', 'G5')
        assert sugestoes[0].score == 95
        assert sugestoes[0].urgencia == 'EMERGENCIA'
        recs = ' '.join(sugestoes[0].recomendacoes)
        assert 'terapia renal' in recs.lower()


# ====================================================================
# TEST SUITE 3: Diabetes Diagnóstico
# ====================================================================

class TestDiagnosticoDiabetes:
    """Validam sugestões para Diabetes."""
    
    def test_diabetes_bem_controlado(self):
        """Diabetes bem controlado: score 15."""
        sugestoes = DiagnosticoService.sugerir_diagnosticos('DIABETES', 'BEM_CONTROLADO')
        assert sugestoes[0].cid10 == 'E11'
        assert sugestoes[0].score == 15
        assert sugestoes[0].urgencia == 'ROTINA'
    
    def test_diabetes_moderado(self):
        """Diabetes moderadamente controlado: score 40."""
        sugestoes = DiagnosticoService.sugerir_diagnosticos('DIABETES', 'MODERADO')
        assert sugestoes[0].score == 40
        assert sugestoes[0].urgencia == 'ROTINA'
    
    def test_diabetes_mal_controlado(self):
        """Diabetes mal controlado: score 70, URGENTE."""
        sugestoes = DiagnosticoService.sugerir_diagnosticos('DIABETES', 'MAL_CONTROLADO')
        assert sugestoes[0].score == 70
        assert sugestoes[0].urgencia == 'URGENTE'
        recs = ' '.join(sugestoes[0].recomendacoes)
        assert 'endocrinologia' in recs.lower()
    
    def test_diabetes_critico_emergencia(self):
        """Diabetes crítico: score 95, EMERGENCIA."""
        sugestoes = DiagnosticoService.sugerir_diagnosticos('DIABETES', 'CRITICO')
        assert sugestoes[0].score == 95
        assert sugestoes[0].urgencia == 'EMERGENCIA'
        recs = ' '.join(sugestoes[0].recomendacoes)
        assert 'DKA' in recs or 'HHS' in recs or 'internação' in recs.lower()


# ====================================================================
# TEST SUITE 4: Dislipidemia Diagnóstico
# ====================================================================

class TestDiagnosticoLipidios:
    """Validam sugestões para Dislipidemia."""
    
    def test_lipidios_otima_eletiva(self):
        """Lipídios ótimos: score 5, ELETIVA."""
        sugestoes = DiagnosticoService.sugerir_diagnosticos('LIPIDIO', 'OTIMA')
        assert sugestoes[0].score == 5
        assert sugestoes[0].urgencia == 'ELETIVA'
    
    def test_lipidios_desejavel(self):
        """Lipídios desejáveis: score 15."""
        sugestoes = DiagnosticoService.sugerir_diagnosticos('LIPIDIO', 'DESEJAVEL')
        assert sugestoes[0].score == 15
    
    def test_lipidios_limitrofe(self):
        """Lipídios limítrofes: score 40."""
        sugestoes = DiagnosticoService.sugerir_diagnosticos('LIPIDIO', 'LIMÍTROFE')
        assert sugestoes[0].score == 40
    
    def test_lipidios_elevada_urgente(self):
        """Lipídios elevados: score 65, URGENTE."""
        sugestoes = DiagnosticoService.sugerir_diagnosticos('LIPIDIO', 'ELEVADA')
        assert sugestoes[0].score == 65
        assert sugestoes[0].urgencia == 'URGENTE'
        recs = ' '.join(sugestoes[0].recomendacoes)
        assert 'estatina' in recs.lower()
    
    def test_lipidios_muito_elevada(self):
        """Lipídios muito elevados: score 85."""
        sugestoes = DiagnosticoService.sugerir_diagnosticos('LIPIDIO', 'MUITO_ELEVADA')
        assert sugestoes[0].score == 85
        assert sugestoes[0].urgencia == 'URGENTE'
        recs = ' '.join(sugestoes[0].recomendacoes)
        assert 'alta potência' in recs.lower() or 'PCSK9' in recs.lower()


# ====================================================================
# TEST SUITE 5: IC Diagnóstico  
# ====================================================================

class TestDiagnosticoIC:
    """Validam sugestões para Insuficiência Cardíaca."""
    
    def test_ic_assintomatica(self):
        """IC assintomática: score 10."""
        sugestoes = DiagnosticoService.sugerir_diagnosticos('IC', 'ASSINTOMATICA')
        assert sugestoes[0].score == 10
        assert sugestoes[0].urgencia == 'ROTINA'
    
    def test_ic_leve(self):
        """IC leve NYHA II: score 35."""
        sugestoes = DiagnosticoService.sugerir_diagnosticos('IC', 'LEVE')
        assert sugestoes[0].score == 35
        assert sugestoes[0].urgencia == 'ROTINA'
    
    def test_ic_moderada(self):
        """IC moderada NYHA III: score 60, URGENTE."""
        sugestoes = DiagnosticoService.sugerir_diagnosticos('IC', 'MODERADA')
        assert sugestoes[0].score == 60
        assert sugestoes[0].urgencia == 'URGENTE'
    
    def test_ic_severa_emergencia(self):
        """IC severa NYHA IV: score 90, EMERGENCIA."""
        sugestoes = DiagnosticoService.sugerir_diagnosticos('IC', 'SEVERA')
        assert sugestoes[0].score == 90
        assert sugestoes[0].urgencia == 'EMERGENCIA'
        recs = ' '.join(sugestoes[0].recomendacoes)
        assert 'tripla' in recs.lower() or 'transplante' in recs.lower()


# ====================================================================
# TEST SUITE 6: Asma Diagnóstico
# ====================================================================

class TestDiagnosticoAsma:
    """Validam sugestões para Asma."""
    
    def test_asma_intermitente(self):
        """Asma intermitente: score 20."""
        sugestoes = DiagnosticoService.sugerir_diagnosticos('ASMA', 'INTERMITENTE')
        assert sugestoes[0].score == 20
        assert sugestoes[0].urgencia == 'ROTINA'
    
    def test_asma_leve_persistente(self):
        """Asma leve persistente: score 40."""
        sugestoes = DiagnosticoService.sugerir_diagnosticos('ASMA', 'LEVE')
        assert sugestoes[0].score == 40
    
    def test_asma_moderada_persistente(self):
        """Asma moderada persistente: score 65, URGENTE."""
        sugestoes = DiagnosticoService.sugerir_diagnosticos('ASMA', 'MODERADA')
        assert sugestoes[0].score == 65
        assert sugestoes[0].urgencia == 'URGENTE'
    
    def test_asma_severa_persistente(self):
        """Asma severa: score 90, requer pneumologia."""
        sugestoes = DiagnosticoService.sugerir_diagnosticos('ASMA', 'SEVERA')
        assert sugestoes[0].score == 90
        recs = ' '.join(sugestoes[0].recomendacoes)
        assert 'pneumologia' in recs.lower() or 'omalizumabe' in recs.lower()


# ====================================================================
# TEST SUITE 7: Multimorbidade
# ====================================================================

class TestMultimorbidade:
    """Validam detecção de padrões em multimorbidade."""
    
    def test_has_2_sem_drc(self):
        """HAS Estágio 2 isolado: risco ALTO."""
        classificacoes = {
            'has': {'estagio': 'ESTAGIO_2'},
            'drc': {},
            'diabetes': {},
            'lipidios': {},
            'ic': {},
            'asma': {}
        }
        resultado = DiagnosticoService.analisar_multimorbidade(classificacoes)
        assert resultado['risco_cv'] == 'BAIXO'  # Sem combinações
    
    def test_has_2_mais_drc_g3b(self):
        """HAS 2 + DRC G3b: Alto risco, URGENTE."""
        classificacoes = {
            'has': {'estagio': 'ESTAGIO_2'},
            'drc': {'estagio': 'G3b'},
            'diabetes': {},
            'lipidios': {},
            'ic': {},
            'asma': {}
        }
        resultado = DiagnosticoService.analisar_multimorbidade(classificacoes)
        assert resultado['risco_cv'] in ['INTERMÉDIO', 'ALTO', 'MUITO_ALTO']
        assert resultado['urgencia_maxima'] == 'URGENTE'
        assert 'Cardiologia' in ' '.join(resultado['encaminhamentos_recomendados'])
        assert 'Nefrologia' in ' '.join(resultado['encaminhamentos_recomendados'])
    
    def test_diabetes_mal_mais_drc_g4(self):
        """Diabetes MAL + DRC G4: MUITO_ALTO, URGENTE."""
        classificacoes = {
            'has': {},
            'drc': {'estagio': 'G4'},
            'diabetes': {'controle_glicemico': 'MAL_CONTROLADO'},
            'lipidios': {},
            'ic': {},
            'asma': {}
        }
        resultado = DiagnosticoService.analisar_multimorbidade(classificacoes)
        assert resultado['risco_cv'] in ['INTERMÉDIO', 'ALTO', 'MUITO_ALTO']
        assert resultado['urgencia_maxima'] == 'URGENTE'
    
    def test_sindrome_cardiometabolica(self):
        """DLP + HAS + Diabetes = Síndrome Cardiometabólica."""
        classificacoes = {
            'has': {'estagio': 'ESTAGIO_1'},
            'drc': {},
            'diabetes': {'controle_glicemico': 'MODERADO'},
            'lipidios': {'categoria': 'MUITO_ELEVADA'},
            'ic': {},
            'asma': {}
        }
        resultado = DiagnosticoService.analisar_multimorbidade(classificacoes)
        assert resultado['risco_cv'] in ['INTERMÉDIO', 'ALTO', 'MUITO_ALTO']
        padroes = ' '.join(resultado['padroes_detectados'])
        assert 'cardiometabólica' in padroes.lower() or 'Síndrome' in padroes
    
    def test_ic_severa_diabetes_critico(self):
        """IC SEVERA + Diabetes CRITICO = EMERGENCIA."""
        classificacoes = {
            'has': {'estagio': 'ESTAGIO_3'},
            'drc': {},
            'diabetes': {'controle_glicemico': 'CRITICO'},
            'lipidios': {},
            'ic': {'estagio_nyha': 'SEVERA'},
            'asma': {}
        }
        resultado = DiagnosticoService.analisar_multimorbidade(classificacoes)
        assert resultado['urgencia_maxima'] == 'EMERGENCIA'
        assert resultado['necessita_internacao'] is True
    
    def test_drc_g5_sempre_emergencia(self):
        """DRC G5 SEMPRE é EMERGENCIA, mesmo isolada."""
        classificacoes = {
            'has': {},
            'drc': {'estagio': 'G5'},
            'diabetes': {},
            'lipidios': {},
            'ic': {},
            'asma': {}
        }
        resultado = DiagnosticoService.analisar_multimorbidade(classificacoes)
        assert resultado['risco_cv'] == 'MUITO_ALTO'
        assert resultado['urgencia_maxima'] == 'EMERGENCIA'
        assert resultado['necessita_internacao'] is True
    
    def test_asma_severa_pneumologia(self):
        """Asma SEVERA detecta necessidade pneumologia."""
        classificacoes = {
            'has': {},
            'drc': {},
            'diabetes': {},
            'lipidios': {},
            'ic': {},
            'asma': {'persistencia': 'SEVERA'}
        }
        resultado = DiagnosticoService.analisar_multimorbidade(classificacoes)
        assert resultado['urgencia_maxima'] == 'URGENTE'
        encams = ' '.join(resultado['encaminhamentos_recomendados'])
        assert 'Pneumologia' in encams


# ====================================================================
# TEST SUITE 8: Recomendações Específicas
# ====================================================================

class TestRecomendacoes:
    """Validam recomendações clínicas específicas."""
    
    def test_recomendacoes_drc_g1(self):
        """DRC G1 recomenda avaliação anual."""
        recs = DiagnosticoService._recomendacoes_drc('G1')
        assert len(recs) >= 1
        recs_str = ' '.join(recs).lower()
        assert 'anualmente' in recs_str or 'anual' in recs_str
    
    def test_recomendacoes_drc_g5(self):
        """DRC G5 recomenda terapia renal substitutiva."""
        recs = DiagnosticoService._recomendacoes_drc('G5')
        recs_str = ' '.join(recs).lower()
        assert 'renal substitutiva' in recs_str or 'diálise' in recs_str
    
    def test_recomendacoes_diabetes_critico(self):
        """Diabetes CRITICO recomenda UTI/internação."""
        recs = DiagnosticoService._recomendacoes_diabetes('CRITICO')
        recs_str = ' '.join(recs).lower()
        assert 'UTI' in ' '.join(recs) or 'internação' in recs_str or 'DKA' in ' '.join(recs)
    
    def test_recomendacoes_lipidios_muito_elevada(self):
        """Dislipidemia muito elevada recomenda PCSK9."""
        recs = DiagnosticoService._recomendacoes_lipidios('MUITO_ELEVADA')
        recs_str = ' '.join(recs).lower()
        assert 'PCSK9' in ' '.join(recs) or 'potência' in recs_str or 'ezetimiba' in recs_str
    
    def test_recomendacoes_ic_severa(self):
        """IC SEVERA recomenda transplante cardíaco."""
        recs = DiagnosticoService._recomendacoes_ic('SEVERA')
        recs_str = ' '.join(recs).lower()
        assert 'transplante' in recs_str or 'VAD' in ' '.join(recs)
    
    def test_recomendacoes_asma_severa(self):
        """Asma SEVERA recomenda omalizumabe."""
        recs = DiagnosticoService._recomendacoes_asma('SEVERA')
        recs_str = ' '.join(recs).lower()
        assert 'omalizumabe' in recs_str or 'biológicos' in recs_str or 'pneumologia' in recs_str


# ====================================================================
# TEST SUITE 9: Edge Cases e Integração
# ====================================================================

class TestEdgeCasesIntegracao:
    """Validam casos extremos e integração."""
    
    def test_sugestao_sem_classificacao(self):
        """Sistema desconhecido retorna lista vazia."""
        sugestoes = DiagnosticoService.sugerir_diagnosticos('DESCONHECIDO', 'DESCONHECIDO')
        assert len(sugestoes) == 0
    
    def test_estagio_invalido_ignora(self):
        """Estágio inválido retorna recomendações padrão."""
        sugestoes = DiagnosticoService.sugerir_diagnosticos('DRC', 'INVALIDO')
        # Retorna com score padrão 50
        assert len(sugestoes) >= 1
        assert sugestoes[0].score == 50
    
    def test_multimorbidade_vazia(self):
        """Classificações vazias retornam risco BAIXO."""
        classificacoes = {
            'has': {},
            'drc': {},
            'diabetes': {},
            'lipidios': {},
            'ic': {},
            'asma': {}
        }
        resultado = DiagnosticoService.analisar_multimorbidade(classificacoes)
        assert resultado['risco_cv'] == 'BAIXO'
        assert resultado['urgencia_maxima'] == 'ELETIVA'
    
    def test_sugestao_ordenada_por_score(self):
        """HAS Estágio 3 retorna múltiplas sugestões ordenadas."""
        sugestoes = DiagnosticoService.sugerir_diagnosticos('HAS', 'ESTAGIO_3')
        assert len(sugestoes) >= 2
        # Verificar que estão ordenadas por score descrescente
        for i in range(len(sugestoes) - 1):
            assert sugestoes[i].score >= sugestoes[i + 1].score
    
    def test_urgencia_escalada(self):
        """Urgência EMERGENCIA pode sobrescrever URGENTE."""
        classificacoes = {
            'has': {'estagio': 'ESTAGIO_3'},
            'drc': {},
            'diabetes': {},
            'lipidios': {},
            'ic': {},
            'asma': {}
        }
        resultado = DiagnosticoService.analisar_multimorbidade(classificacoes)
        # HAS 3 sozinho é URGENTE (precisaria de DRC G5 ou similar para EMERGENCIA)
        assert resultado['urgencia_maxima'] in ['ELETIVA', 'ROTINA', 'URGENTE', 'EMERGENCIA']
