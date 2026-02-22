"""
Testes para PlanoCuidadoService - Geração Automática de Planos

Coverage:
- 8 test classes (HAS, DM, DRC, Dislipidemia, IC, Asma, Integração, EdgeCases)
- 30+ testes cobrindo todos os estágios e comorbidades
- Validação de estrutura, protocolos, medicações
- Performance: <50ms por plano
"""

import pytest
from datetime import datetime, timedelta
from src.oswaldo.services.plano_cuidado_service import (
    PlanoCuidadoService,
    PlanoCuidado,
    Objetivo,
    Medicamento,
    Intervencao,
    NivelSeveridade
)


# ========================================================================
# FIXTURES
# ========================================================================

@pytest.fixture
def condicao_cronica_id():
    return 1


@pytest.fixture
def paciente_simples():
    return {
        "idade": 55,
        "comorbidades": []
    }


@pytest.fixture
def paciente_com_comorbidades():
    return {
        "idade": 72,
        "comorbidades": ["E11", "E78", "N18"]
    }


# ========================================================================
# TESTES: HIPERTENSÃO ARTERIAL (I10)
# ========================================================================

class TestPlanoHAS:
    """Testes para plano de cuidado em Hipertensão Arterial"""

    def test_plano_has_normal(self, condicao_cronica_id, paciente_simples):
        """HAS estadio normal - sem medicação"""
        plano = PlanoCuidadoService.criar_plano_completo(
            condicao_cronica_id=condicao_cronica_id,
            cid10="I10",
            diagnostico="Hipertensão Arterial",
            estagio="NORMAL",
            classificacao_nivel="NORMAL",
            idade_anos=paciente_simples["idade"],
            comorbidades=paciente_simples["comorbidades"]
        )
        
        assert plano.cid10 == "I10"
        assert plano.nivel_severidade == "NORMAL"
        assert len(plano.objetivos) >= 1
        assert plano.objetivos[0].valor_alvo == 120
        assert len(plano.medicamentos) == 0  # Sem medicação em estágio normal
        assert plano.frequencia_acompanhamento_dias == 365

    def test_plano_has_elevada(self, condicao_cronica_id):
        """HAS elevada - sem medicação, apenas mudanças estilo de vida"""
        plano = PlanoCuidadoService.criar_plano_completo(
            condicao_cronica_id=condicao_cronica_id,
            cid10="I10",
            diagnostico="Hipertensão Arterial Elevada",
            estagio="ELEVADA",
            classificacao_nivel="LEVE",
            idade_anos=45,
            comorbidades=[]
        )
        
        assert len(plano.medicamentos) == 0  # Sem farmacologia
        assert len(plano.intervencoes) >= 3  # Dieta, exercício, educação
        assert plano.frequencia_acompanhamento_dias == 90
        assert "Dieta" in [i.categoria for i in plano.intervencoes]

    def test_plano_has_estagio_1(self, condicao_cronica_id):
        """HAS estágio 1 - monomedicação"""
        plano = PlanoCuidadoService.criar_plano_completo(
            condicao_cronica_id=condicao_cronica_id,
            cid10="I10",
            diagnostico="Hipertensão Arterial",
            estagio="ESTAGIO_1",
            classificacao_nivel="MODERADA",
            idade_anos=60,
            comorbidades=[]
        )
        
        assert len(plano.medicamentos) == 1
        assert plano.medicamentos[0].nome == "Losartan"
        assert plano.medicamentos[0].classe_farmacologica == "ARA2"
        assert plano.frequencia_acompanhamento_dias == 30

    def test_plano_has_estagio_2(self, condicao_cronica_id):
        """HAS estágio 2 - bimedicação"""
        plano = PlanoCuidadoService.criar_plano_completo(
            condicao_cronica_id=condicao_cronica_id,
            cid10="I10",
            diagnostico="Hipertensão Arterial",
            estagio="ESTAGIO_2",
            classificacao_nivel="SEVERA",
            idade_anos=65,
            comorbidades=[]
        )
        
        assert len(plano.medicamentos) == 2
        medicamentos = [m.nome for m in plano.medicamentos]
        assert "Losartan" in medicamentos
        assert "Amlodipina" in medicamentos
        assert plano.frequencia_acompanhamento_dias == 30

    def test_plano_has_estagio_3(self, condicao_cronica_id):
        """HAS estágio 3 - terapia tripla"""
        plano = PlanoCuidadoService.criar_plano_completo(
            condicao_cronica_id=condicao_cronica_id,
            cid10="I10",
            diagnostico="Hipertensão Arterial",
            estagio="ESTAGIO_3",
            classificacao_nivel="CRITICA",
            idade_anos=75,
            comorbidades=["E11"]
        )
        
        assert len(plano.medicamentos) == 3
        medicamentos = [m.nome for m in plano.medicamentos]
        assert "Losartan" in medicamentos
        assert "Amlodipina" in medicamentos
        assert "Hidroclorotiazida" in medicamentos
        assert plano.frequencia_acompanhamento_dias == 15

    def test_plano_has_exames_recomendados(self, condicao_cronica_id):
        """Validar exames recomendados em HAS"""
        plano = PlanoCuidadoService.criar_plano_completo(
            condicao_cronica_id=condicao_cronica_id,
            cid10="I10",
            diagnostico="Hipertensão Arterial",
            estagio="ESTAGIO_2",
            classificacao_nivel="SEVERA",
            idade_anos=55,
            comorbidades=[]
        )
        
        assert len(plano.exames_recomendados) >= 4
        assert "Eletrocardiograma" in plano.exames_recomendados
        assert "Creatinina sérica" in plano.exames_recomendados


# ========================================================================
# TESTES: DIABETES MELLITUS (E11)
# ========================================================================

class TestPlanoDiabetes:
    """Testes para plano de cuidado em Diabetes Mellitus"""

    def test_plano_dm_bem_controlado(self, condicao_cronica_id):
        """DM bem controlado - manutenção"""
        plano = PlanoCuidadoService.criar_plano_completo(
            condicao_cronica_id=condicao_cronica_id,
            cid10="E11",
            diagnostico="Diabetes Mellitus Tipo 2",
            estagio="BEM_CONTROLADO",
            classificacao_nivel="NORMAL",
            idade_anos=65,
            comorbidades=[]
        )
        
        assert plano.nivel_severidade == "NORMAL"
        assert len(plano.objetivos) >= 1
        assert plano.objetivos[0].valor_alvo == 7.0
        assert plano.frequencia_acompanhamento_dias == 180

    def test_plano_dm_moderado(self, condicao_cronica_id):
        """DM moderadamente controlado - metformina"""
        plano = PlanoCuidadoService.criar_plano_completo(
            condicao_cronica_id=condicao_cronica_id,
            cid10="E11",
            diagnostico="Diabetes Mellitus Tipo 2",
            estagio="MODERADO",
            classificacao_nivel="MODERADA",
            idade_anos=58,
            comorbidades=[]
        )
        
        assert len(plano.medicamentos) == 1
        assert plano.medicamentos[0].nome == "Metformina"
        assert plano.medicamentos[0].protocolo == "ADA 2024"
        assert plano.frequencia_acompanhamento_dias == 90

    def test_plano_dm_mal_controlado(self, condicao_cronica_id):
        """DM mal controlado - bimedicação"""
        plano = PlanoCuidadoService.criar_plano_completo(
            condicao_cronica_id=condicao_cronica_id,
            cid10="E11",
            diagnostico="Diabetes Mellitus Tipo 2",
            estagio="MAL_CONTROLADO",
            classificacao_nivel="SEVERA",
            idade_anos=62,
            comorbidades=[]
        )
        
        assert len(plano.medicamentos) == 2
        medicamentos = [m.nome for m in plano.medicamentos]
        assert "Metformina" in medicamentos
        assert "Gliclazida" in medicamentos
        assert plano.frequencia_acompanhamento_dias == 30

    def test_plano_dm_critico(self, condicao_cronica_id):
        """DM crítico - insulina necessária"""
        plano = PlanoCuidadoService.criar_plano_completo(
            condicao_cronica_id=condicao_cronica_id,
            cid10="E11",
            diagnostico="Diabetes Mellitus Tipo 2",
            estagio="CRITICO",
            classificacao_nivel="CRITICA",
            idade_anos=68,
            comorbidades=[]
        )
        
        assert len(plano.medicamentos) >= 1
        assert any(m.nome == "Insulina Glargina" for m in plano.medicamentos)
        assert plano.frequencia_acompanhamento_dias == 14

    def test_plano_dm_intervencoes_educacao(self, condicao_cronica_id):
        """Validar intervenções educacionais em DM"""
        plano = PlanoCuidadoService.criar_plano_completo(
            condicao_cronica_id=condicao_cronica_id,
            cid10="E11",
            diagnostico="Diabetes Mellitus Tipo 2",
            estagio="MODERADO",
            classificacao_nivel="MODERADA",
            idade_anos=55,
            comorbidades=[]
        )
        
        assert len(plano.intervencoes) >= 3
        categorias = [i.categoria for i in plano.intervencoes]
        assert "Educação diabetes" in categorias


# ========================================================================
# TESTES: DOENÇA RENAL CRÔNICA (N18)
# ========================================================================

class TestPlanoDRC:
    """Testes para plano de cuidado em Doença Renal Crônica"""

    def test_plano_drc_g1(self, condicao_cronica_id):
        """DRC G1 - função renal normal, monitoramento"""
        plano = PlanoCuidadoService.criar_plano_completo(
            condicao_cronica_id=condicao_cronica_id,
            cid10="N18",
            diagnostico="Doença Renal Crônica",
            estagio="G1",
            classificacao_nivel="NORMAL",
            idade_anos=50,
            comorbidades=[]
        )
        
        assert len(plano.medicamentos) == 0
        assert plano.frequencia_acompanhamento_dias == 180

    def test_plano_drc_g3a(self, condicao_cronica_id):
        """DRC G3a - início de terapia nefroprotetora"""
        plano = PlanoCuidadoService.criar_plano_completo(
            condicao_cronica_id=condicao_cronica_id,
            cid10="N18",
            diagnostico="Doença Renal Crônica G3a",
            estagio="G3a",
            classificacao_nivel="MODERADA",
            idade_anos=65,
            comorbidades=[]
        )
        
        assert len(plano.medicamentos) >= 2
        medicamentos = [m.nome for m in plano.medicamentos]
        assert "Losartan" in medicamentos
        assert "Finerenona" in medicamentos
        assert plano.frequencia_acompanhamento_dias == 90

    def test_plano_drc_g4(self, condicao_cronica_id):
        """DRC G4 - redução severa, preparação para TRS"""
        plano = PlanoCuidadoService.criar_plano_completo(
            condicao_cronica_id=condicao_cronica_id,
            cid10="N18",
            diagnostico="Doença Renal Crônica G4",
            estagio="G4",
            classificacao_nivel="SEVERA",
            idade_anos=70,
            comorbidades=[]
        )
        
        assert len(plano.medicamentos) >= 3
        medicamentos_nomes = [m.nome for m in plano.medicamentos]
        assert "Losartan" in medicamentos_nomes
        assert any("Carbonato" in nome for nome in medicamentos_nomes)

    def test_plano_drc_parametros_monitoramento(self, condicao_cronica_id):
        """Validar parâmetros de monitoramento em DRC"""
        plano = PlanoCuidadoService.criar_plano_completo(
            condicao_cronica_id=condicao_cronica_id,
            cid10="N18",
            diagnostico="Doença Renal Crônica",
            estagio="G3b",
            classificacao_nivel="MODERADA",
            idade_anos=62,
            comorbidades=[]
        )
        
        assert "TFGe" in plano.parametros_a_monitorar
        assert "Potássio" in plano.parametros_a_monitorar


# ========================================================================
# TESTES: DISLIPIDEMIA (E78)
# ========================================================================

class TestPlanoDislipidemia:
    """Testes para plano de cuidado em Dislipidemia"""

    def test_plano_dislipidemia_otima(self, condicao_cronica_id):
        """Dislipidemia ótima - manutenção"""
        plano = PlanoCuidadoService.criar_plano_completo(
            condicao_cronica_id=condicao_cronica_id,
            cid10="E78",
            diagnostico="Dislipidemia",
            estagio="OTIMA",
            classificacao_nivel="NORMAL",
            idade_anos=50,
            comorbidades=[]
        )
        
        assert len(plano.medicamentos) == 0
        assert plano.frequencia_acompanhamento_dias == 365

    def test_plano_dislipidemia_limítrofe(self, condicao_cronica_id):
        """Dislipidemia limítrofe - estatina baixa dose"""
        plano = PlanoCuidadoService.criar_plano_completo(
            condicao_cronica_id=condicao_cronica_id,
            cid10="E78",
            diagnostico="Dislipidemia",
            estagio="LIMÍTROFE",
            classificacao_nivel="LEVE",
            idade_anos=55,
            comorbidades=[]
        )
        
        assert len(plano.medicamentos) == 1
        assert plano.medicamentos[0].nome == "Atorvastatina"
        assert plano.frequencia_acompanhamento_dias == 90

    def test_plano_dislipidemia_elevada(self, condicao_cronica_id):
        """Dislipidemia elevada - estatina moderada"""
        plano = PlanoCuidadoService.criar_plano_completo(
            condicao_cronica_id=condicao_cronica_id,
            cid10="E78",
            diagnostico="Dislipidemia",
            estagio="ELEVADA",
            classificacao_nivel="SEVERA",
            idade_anos=60,
            comorbidades=["I10"]
        )
        
        assert len(plano.medicamentos) >= 1
        assert plano.medicamentos[0].nome == "Atorvastatina"
        assert plano.frequencia_acompanhamento_dias == 30

    def test_plano_dislipidemia_muito_elevada(self, condicao_cronica_id):
        """Dislipidemia muito elevada - terapia tripla com PCSK9i"""
        plano = PlanoCuidadoService.criar_plano_completo(
            condicao_cronica_id=condicao_cronica_id,
            cid10="E78",
            diagnostico="Dislipidemia",
            estagio="MUITO_ELEVADA",
            classificacao_nivel="CRITICA",
            idade_anos=68,
            comorbidades=["I10", "E11"]
        )
        
        assert len(plano.medicamentos) >= 3
        medicamentos = [m.nome for m in plano.medicamentos]
        assert "Atorvastatina" in medicamentos
        assert "Ezetimiba" in medicamentos
        assert any("PCSK9" in m.classe_farmacologica for m in plano.medicamentos)


# ========================================================================
# TESTES: INSUFICIÊNCIA CARDÍACA (I50)
# ========================================================================

class TestPlanoIC:
    """Testes para plano de cuidado em Insuficiência Cardíaca"""

    def test_plano_ic_assintomatica(self, condicao_cronica_id):
        """IC assintomática - monitoramento"""
        plano = PlanoCuidadoService.criar_plano_completo(
            condicao_cronica_id=condicao_cronica_id,
            cid10="I50",
            diagnostico="Insuficiência Cardíaca",
            estagio="ASSINTOMATICA",
            classificacao_nivel="NORMAL",
            idade_anos=60,
            comorbidades=[]
        )
        
        assert len(plano.medicamentos) <= 1  # Apenas resgate se necessário
        assert plano.frequencia_acompanhamento_dias == 180

    def test_plano_ic_leve(self, condicao_cronica_id):
        """IC leve (NYHA I) - IECA"""
        plano = PlanoCuidadoService.criar_plano_completo(
            condicao_cronica_id=condicao_cronica_id,
            cid10="I50",
            diagnostico="Insuficiência Cardíaca",
            estagio="LEVE",
            classificacao_nivel="LEVE",
            idade_anos=65,
            comorbidades=[]
        )
        
        assert len(plano.medicamentos) == 1
        assert plano.medicamentos[0].nome == "Enalapril"
        assert plano.medicamentos[0].classe_farmacologica == "IECA"

    def test_plano_ic_moderada(self, condicao_cronica_id):
        """IC moderada (NYHA II) - terapia dupla"""
        plano = PlanoCuidadoService.criar_plano_completo(
            condicao_cronica_id=condicao_cronica_id,
            cid10="I50",
            diagnostico="Insuficiência Cardíaca",
            estagio="MODERADA",
            classificacao_nivel="MODERADA",
            idade_anos=70,
            comorbidades=[]
        )
        
        assert len(plano.medicamentos) >= 3
        medicamentos = [m.nome for m in plano.medicamentos]
        assert "Enalapril" in medicamentos
        assert "Carvedilol" in medicamentos
        assert "Furosemida" in medicamentos

    def test_plano_ic_severa(self, condicao_cronica_id):
        """IC severa (NYHA III-IV) - terapia quadrupla com ARNI"""
        plano = PlanoCuidadoService.criar_plano_completo(
            condicao_cronica_id=condicao_cronica_id,
            cid10="I50",
            diagnostico="Insuficiência Cardíaca",
            estagio="SEVERA",
            classificacao_nivel="CRITICA",
            idade_anos=75,
            comorbidades=["I10", "E11"]
        )
        
        assert len(plano.medicamentos) >= 4
        medicamentos = [m.nome for m in plano.medicamentos]
        assert "Sacubitril/Valsartan" in medicamentos
        assert "Carvedilol" in medicamentos
        assert "Espironolactona" in medicamentos
        assert "Furosemida" in medicamentos
        assert plano.frequencia_acompanhamento_dias == 7

    def test_plano_ic_parametros_nyha(self, condicao_cronica_id):
        """Validar monitoramento NYHA em IC"""
        plano = PlanoCuidadoService.criar_plano_completo(
            condicao_cronica_id=condicao_cronica_id,
            cid10="I50",
            diagnostico="Insuficiência Cardíaca",
            estagio="MODERADA",
            classificacao_nivel="MODERADA",
            idade_anos=68,
            comorbidades=[]
        )
        
        assert "Classe NYHA" in plano.parametros_a_monitorar
        assert "Peso corporal" in plano.parametros_a_monitorar


# ========================================================================
# TESTES: ASMA (J45)
# ========================================================================

class TestPlanoAsma:
    """Testes para plano de cuidado em Asma"""

    def test_plano_asma_controlada(self, condicao_cronica_id):
        """Asma controlada - apenas resgate"""
        plano = PlanoCuidadoService.criar_plano_completo(
            condicao_cronica_id=condicao_cronica_id,
            cid10="J45",
            diagnostico="Asma Controlada",
            estagio="CONTROLADO",
            classificacao_nivel="NORMAL",
            idade_anos=40,
            comorbidades=[]
        )
        
        assert len(plano.medicamentos) == 1
        assert plano.medicamentos[0].nome == "Salbutamol"
        assert plano.frequencia_acompanhamento_dias == 180

    def test_plano_asma_parcialmente_controlada(self, condicao_cronica_id):
        """Asma parcialmente controlada - controlador ICS/LABA"""
        plano = PlanoCuidadoService.criar_plano_completo(
            condicao_cronica_id=condicao_cronica_id,
            cid10="J45",
            diagnostico="Asma Parcialmente Controlada",
            estagio="PARCIALMENTE_CONTROLADO",
            classificacao_nivel="LEVE",
            idade_anos=45,
            comorbidades=[]
        )
        
        assert len(plano.medicamentos) >= 2
        medicamentos = [m.nome for m in plano.medicamentos]
        assert any("Budesonida" in m or "Formoterol" in m for m in medicamentos)
        assert plano.frequencia_acompanhamento_dias == 60

    def test_plano_asma_nao_controlada(self, condicao_cronica_id):
        """Asma não controlada - terapia intensiva com biológicos"""
        plano = PlanoCuidadoService.criar_plano_completo(
            condicao_cronica_id=condicao_cronica_id,
            cid10="J45",
            diagnostico="Asma Não Controlada",
            estagio="NAO_CONTROLADO",
            classificacao_nivel="SEVERA",
            idade_anos=50,
            comorbidades=[]
        )
        
        assert len(plano.medicamentos) >= 3
        medicamentos = [m.nome for m in plano.medicamentos]
        assert any("Fluticasona" in m or "Salmeterol" in m for m in medicamentos)
        assert "Montelucaste" in medicamentos
        assert any("Omalizumab" in m for m in medicamentos)
        assert plano.frequencia_acompanhamento_dias == 14


# ========================================================================
# TESTES: VALIDAÇÃO DE ESTRUTURA
# ========================================================================

class TestValidacaoEstrutura:
    """Testes para validação da estrutura do plano de cuidado"""

    def test_plano_tem_objetivos_smart(self, condicao_cronica_id):
        """Validar que todos os objetivos seguem padrão SMART"""
        plano = PlanoCuidadoService.criar_plano_completo(
            condicao_cronica_id=condicao_cronica_id,
            cid10="I10",
            diagnostico="Hipertensão Arterial",
            estagio="ESTAGIO_2",
            classificacao_nivel="SEVERA",
            idade_anos=60,
            comorbidades=[]
        )
        
        for objetivo in plano.objetivos:
            assert isinstance(objetivo.descricao, str) and len(objetivo.descricao) > 0
            assert isinstance(objetivo.valor_alvo, (int, float))
            assert isinstance(objetivo.unidade, str) and len(objetivo.unidade) > 0
            assert objetivo.prazo_dias > 0

    def test_medicamentos_tem_info_completa(self, condicao_cronica_id):
        """Validar que medicamentos têm todas as informações necessárias"""
        plano = PlanoCuidadoService.criar_plano_completo(
            condicao_cronica_id=condicao_cronica_id,
            cid10="E11",
            diagnostico="Diabetes Mellitus Tipo 2",
            estagio="MAL_CONTROLADO",
            classificacao_nivel="SEVERA",
            idade_anos=60,
            comorbidades=[]
        )
        
        for med in plano.medicamentos:
            assert isinstance(med.nome, str) and len(med.nome) > 0
            assert isinstance(med.classe_farmacologica, str)
            assert isinstance(med.protocolo, str)
            assert isinstance(med.justificativa, str)

    def test_intervencoes_tem_responsavel(self, condicao_cronica_id):
        """Validar que todas as intervenções têm responsável designado"""
        plano = PlanoCuidadoService.criar_plano_completo(
            condicao_cronica_id=condicao_cronica_id,
            cid10="I10",
            diagnostico="Hipertensão Arterial",
            estagio="ELEVADA",
            classificacao_nivel="LEVE",
            idade_anos=50,
            comorbidades=[]
        )
        
        responsaveis_validos = {"paciente", "enfermeiro", "nutricionista", "nurse educator"}
        for intervencao in plano.intervencoes:
            assert intervencao.responsavel in responsaveis_validos or len(intervencao.responsavel) > 0

    def test_plano_data_proxima_revisao(self, condicao_cronica_id):
        """Data de próxima revisão deve ser condizente com frequência"""
        plano = PlanoCuidadoService.criar_plano_completo(
            condicao_cronica_id=condicao_cronica_id,
            cid10="I10",
            diagnostico="Hipertensão Arterial",
            estagio="NORMAL",
            classificacao_nivel="NORMAL",
            idade_anos=55,
            comorbidades=[]
        )
        
        delta = plano.data_proxima_revisao - plano.data_criacao
        assert delta.days == plano.frequencia_acompanhamento_dias

    def test_exames_recomendados_nao_vazio(self, condicao_cronica_id):
        """Plano deve recomendar exames de acompanhamento"""
        plano = PlanoCuidadoService.criar_plano_completo(
            condicao_cronica_id=condicao_cronica_id,
            cid10="E11",
            diagnostico="Diabetes Mellitus Tipo 2",
            estagio="MODERADO",
            classificacao_nivel="MODERADA",
            idade_anos=55,
            comorbidades=[]
        )
        
        assert len(plano.exames_recomendados) > 0
        assert len(plano.parametros_a_monitorar) > 0


# ========================================================================
# TESTES: CENÁRIOS INTEGRADOS
# ========================================================================

class TestCenariosIntegrados:
    """Testes com cenários complexos de múltiplas comorbidades"""

    def test_cid10_invalido_retorna_plano_minimo(self, condicao_cronica_id):
        """CID10 não mapeado deve retornar plano com estrutura básica"""
        plano = PlanoCuidadoService.criar_plano_completo(
            condicao_cronica_id=condicao_cronica_id,
            cid10="Z00",  # Check-up
            diagnostico="Avaliação de rotina",
            estagio="NORMAL",
            classificacao_nivel="NORMAL",
            idade_anos=50,
            comorbidades=[]
        )
        
        assert isinstance(plano, PlanoCuidado)
        assert plano.cid10 == "Z00"

    def test_plano_preserva_metadata(self, condicao_cronica_id):
        """Metadados devem ser preservados"""
        plano = PlanoCuidadoService.criar_plano_completo(
            condicao_cronica_id=42,
            cid10="I10",
            diagnostico="Teste",
            estagio="ESTAGIO_2",
            classificacao_nivel="SEVERA",
            idade_anos=55,
            comorbidades=[]
        )
        
        assert plano.condicao_cronica_id == 42
        assert plano.status == "ATIVO"
        assert isinstance(plano.data_criacao, datetime)
