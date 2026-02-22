"""
Day 6.4: E2E Integration Tests - Pipeline Clínico Completo

Valida o fluxo clínico de ponta a ponta:
PlanoCuidadoService → AlertaService → AcompanhamentoService
"""

import pytest
from datetime import datetime, timedelta
from src.oswaldo.services.plano_cuidado_service import PlanoCuidadoService
from src.oswaldo.services.alerta_service import AlertaService
from src.oswaldo.services.acompanhamento_service import AcompanhamentoService


class TestE2EIntegration:
    """Testes E2E validando integração entre os 3 serviços"""

    def test_has_pipeline_completo(self):
        """Pipeline completo: Plano → Alerta → Acompanhamento para HAS"""
        # Passo 1: Criar plano para HAS
        plano = PlanoCuidadoService.criar_plano_completo(
            condicao_cronica_id=1,
            cid10="I10",
            diagnostico="HAS",
            estagio="CONTROLADA",
            classificacao_nivel="LEVE",
            idade_anos=65,
            comorbidades=[]
        )
        
        assert plano is not None
        assert plano.diagnostico == "HAS"
        assert plano.cid10 == "I10"

        # Passo 2: Simular monitoramento e criar alerta
        dados_pa = [
            {"data": datetime.now() - timedelta(days=i), "valor": 135 + i}
            for i in range(5, 0, -1)
        ]
        
        alerta = AlertaService.avaliar_progresso_objetivo(
            objetivo_descricao="PA < 140",
            parametro="PA sistólica",
            valor_atual=dados_pa[-1]["valor"],
            valor_objetivo=140,
            unidade="mmHg",
            dados_historicos=dados_pa,
            dias_desde_inicio=30
        )
        
        assert alerta is not None
        assert alerta.nivel in ["BAIXO", "MEDIO", "ALTO", "CRITICO"]

        # Passo 3: Gerar plano de acompanhamento baseado no alerta
        plano_acomp = AcompanhamentoService.gerar_plano_acompanhamento(
            condicao_cronica_id=1,
            cid10="I10",
            diagnostico="HAS",
            nivel_alerta=alerta.nivel,
            score_controle=75,
            parametro_principal="PA sistólica",
            valor_atual=dados_pa[-1]["valor"],
            valor_objetivo=140,
            medicacoes_atuais=["Losartan 50mg"],
            aderencia_medicacao=85.0
        )
        
        # Validações de integração
        assert plano_acomp is not None
        assert plano_acomp.diagnostico == "HAS"
        assert plano_acomp.frequencia_dias > 0
        assert plano_acomp.score_aderencia_geral >= 0

    def test_diabetes_pipeline_completo(self):
        """Pipeline para DM2"""
        # Plano
        plano = PlanoCuidadoService.criar_plano_completo(
            condicao_cronica_id=2,
            cid10="E11",
            diagnostico="Diabetes Mellitus II",
            estagio="CONTROLADA",
            classificacao_nivel="MODERADA",
            idade_anos=60,
            comorbidades=[]
        )
        
        assert plano is not None

        # Alerta
        dados_glicemia = [
            {"data": datetime.now() - timedelta(days=i), "valor": 120}
            for i in range(5, 0, -1)
        ]
        
        alerta = AlertaService.avaliar_progresso_objetivo(
            objetivo_descricao="Glicemia < 130",
            parametro="Glicemia",
            valor_atual=dados_glicemia[-1]["valor"],
            valor_objetivo=130,
            unidade="mg/dL",
            dados_historicos=dados_glicemia,
            dias_desde_inicio=30
        )
        
        assert alerta is not None

        # Acompanhamento
        plano_acomp = AcompanhamentoService.gerar_plano_acompanhamento(
            condicao_cronica_id=2,
            cid10="E11",
            diagnostico="DM2",
            nivel_alerta=alerta.nivel,
            score_controle=80,
            parametro_principal="Glicemia",
            valor_atual=dados_glicemia[-1]["valor"],
            valor_objetivo=130,
            medicacoes_atuais=["Metformina"],
            aderencia_medicacao=90.0
        )
        
        assert plano_acomp is not None
        assert plano_acomp.diagnostico == "DM2"

    def test_crisis_hipertensiva_intensificacao(self):
        """Cenário: Crise hipertensiva com intensificação de acompanhamento"""
        # Plano inicial
        plano = PlanoCuidadoService.criar_plano_completo(
            condicao_cronica_id=1,
            cid10="I10",
            diagnostico="HAS",
            estagio="DESCOMPENSADA",
            classificacao_nivel="CRITICA",
            idade_anos=70,
            comorbidades=[]
        )

        # PA muito elevada (crise)
        dados_crisis = [
            {"data": datetime.now() - timedelta(days=i), "valor": 180 + i*5}
            for i in range(5, 0, -1)
        ]
        
        # Alerta deve indicar severidade
        alerta = AlertaService.avaliar_progresso_objetivo(
            objetivo_descricao="PA < 140",
            parametro="PA sistólica",
            valor_atual=dados_crisis[-1]["valor"],
            valor_objetivo=140,
            unidade="mmHg",
            dados_historicos=dados_crisis,
            dias_desde_inicio=20
        )
        
        # Pode ser MEDIO, ALTO ou CRITICO dependendo da lógica
        assert alerta.nivel in ["MEDIO", "ALTO", "CRITICO"]

        # Acompanhamento deve ser intensivo
        plano_intensivo = AcompanhamentoService.gerar_plano_acompanhamento(
            condicao_cronica_id=1,
            cid10="I10",
            diagnostico="HAS",
            nivel_alerta=alerta.nivel,
            score_controle=20,
            parametro_principal="PA sistólica",
            valor_atual=dados_crisis[-1]["valor"],
            valor_objetivo=140,
            medicacoes_atuais=["Losartan"],
            aderencia_medicacao=15.0
        )
        
        # Deve ter frequência mais alta (dias menores)
        assert plano_intensivo.frequencia_dias <= 30

    def test_multiplas_condicoes_pipeline(self):
        """Multiplas condições em paralelo: HAS + DM"""
        # Dois planos
        plano_has = PlanoCuidadoService.criar_plano_completo(
            condicao_cronica_id=1,
            cid10="I10",
            diagnostico="HAS",
            estagio="CONTROLADA",
            classificacao_nivel="LEVE",
            idade_anos=65,
            comorbidades=["E11"]
        )
        
        plano_dm = PlanoCuidadoService.criar_plano_completo(
            condicao_cronica_id=2,
            cid10="E11",
            diagnostico="Diabetes Mellitus II",
            estagio="DESCONTROLADA",
            classificacao_nivel="SEVERA",
            idade_anos=65,
            comorbidades=["I10"]
        )
        
        assert plano_has is not None
        assert plano_dm is not None
        
        # Alertas para ambas
        alerta_has = AlertaService.avaliar_progresso_objetivo(
            objetivo_descricao="PA < 140",
            parametro="PA sistólica",
            valor_atual=135,
            valor_objetivo=140,
            unidade="mmHg",
            dados_historicos=[{"data": datetime.now(), "valor": 135}],
            dias_desde_inicio=10
        )
        
        alerta_dm = AlertaService.avaliar_progresso_objetivo(
            objetivo_descricao="Glicemia < 130",
            parametro="Glicemia",
            valor_atual=200,
            valor_objetivo=130,
            unidade="mg/dL",
            dados_historicos=[{"data": datetime.now(), "valor": 200}],
            dias_desde_inicio=10
        )
        
        assert alerta_has is not None
        assert alerta_dm is not None
        
        # Acompanhamento de ambas
        acomp_has = AcompanhamentoService.gerar_plano_acompanhamento(
            condicao_cronica_id=1,
            cid10="I10",
            diagnostico="HAS",
            nivel_alerta=alerta_has.nivel,
            score_controle=75,
            parametro_principal="PA sistólica",
            valor_atual=135,
            valor_objetivo=140,
            medicacoes_atuais=[],
            aderencia_medicacao=0.0
        )
        
        acomp_dm = AcompanhamentoService.gerar_plano_acompanhamento(
            condicao_cronica_id=2,
            cid10="E11",
            diagnostico="DM2",
            nivel_alerta=alerta_dm.nivel,
            score_controle=25,
            parametro_principal="Glicemia",
            valor_atual=200,
            valor_objetivo=130,
            medicacoes_atuais=[],
            aderencia_medicacao=0.0
        )
        
        assert acomp_has is not None
        assert acomp_dm is not None

    def test_data_consistency_across_services(self):
        """Validar consistência de dados entre serviços"""
        # Criar plano
        plano = PlanoCuidadoService.criar_plano_completo(
            condicao_cronica_id=123,
            cid10="I10",
            diagnostico="HAS",
            estagio="CONTROLADA",
            classificacao_nivel="LEVE",
            idade_anos=65,
            comorbidades=[]
        )
        
        assert plano.condicao_cronica_id == 123
        assert plano.cid10 == "I10"

        # Criar alerta com mesmo ID
        alerta = AlertaService.avaliar_progresso_objetivo(
            objetivo_descricao="PA < 140",
            parametro="PA sistólica",
            valor_atual=145,
            valor_objetivo=140,
            unidade="mmHg",
            dados_historicos=[{"data": datetime.now(), "valor": 145}],
            dias_desde_inicio=5
        )

        # Criar acompanhamento preservando dados
        acomp = AcompanhamentoService.gerar_plano_acompanhamento(
            condicao_cronica_id=123,
            cid10="I10",
            diagnostico="HAS",
            nivel_alerta=alerta.nivel,
            score_controle=70,
            parametro_principal="PA sistólica",
            valor_atual=145,
            valor_objetivo=140,
            medicacoes_atuais=[],
            aderencia_medicacao=0.0
        )
        
        # Validar que dados foram preservados
        assert acomp.condicao_cronica_id == 123
        assert acomp.cid10 == "I10"
        assert acomp.diagnostico == "HAS"

    def test_performance_service_calls(self):
        """Validar que cada serviço responde em tempo razoável"""
        import time
        
        # PlanoCuidadoService
        start = time.perf_counter()
        plano = PlanoCuidadoService.criar_plano_completo(
            condicao_cronica_id=1,
            cid10="I10",
            diagnostico="HAS",
            estagio="CONTROLADA",
            classificacao_nivel="LEVE",
            idade_anos=65,
            comorbidades=[]
        )
        plano_time = (time.perf_counter() - start) * 1000
        assert plano_time < 500, f"PlanoCuidadoService lento: {plano_time:.2f}ms"

        # AlertaService
        start = time.perf_counter()
        alerta = AlertaService.avaliar_progresso_objetivo(
            objetivo_descricao="PA < 140",
            parametro="PA sistólica",
            valor_atual=145,
            valor_objetivo=140,
            unidade="mmHg",
            dados_historicos=[{"data": datetime.now(), "valor": 145}],
            dias_desde_inicio=5
        )
        alerta_time = (time.perf_counter() - start) * 1000
        assert alerta_time < 200, f"AlertaService lento: {alerta_time:.2f}ms"

        # AcompanhamentoService
        start = time.perf_counter()
        acomp = AcompanhamentoService.gerar_plano_acompanhamento(
            condicao_cronica_id=1,
            cid10="I10",
            diagnostico="HAS",
            nivel_alerta="BAIXO",
            score_controle=75,
            parametro_principal="PA sistólica",
            valor_atual=145,
            valor_objetivo=140,
            medicacoes_atuais=[],
            aderencia_medicacao=0.0
        )
        acomp_time = (time.perf_counter() - start) * 1000
        assert acomp_time < 200, f"AcompanhamentoService lento: {acomp_time:.2f}ms"


class TestE2EEdgeCases:
    """Casos extremos da integração"""

    def test_valores_extremos_no_pipeline(self):
        """Pipeline aguenta valores extremos sem quebrar"""
        # Valor muito alto
        alerta_alto = AlertaService.avaliar_progresso_objetivo(
            objetivo_descricao="PA < 140",
            parametro="PA sistólica",
            valor_atual=250,
            valor_objetivo=140,
            unidade="mmHg",
            dados_historicos=[
                {"data": datetime.now() - timedelta(days=i), "valor": 240 + i}
                for i in range(5)
            ],
            dias_desde_inicio=30
        )
        
        assert alerta_alto is not None
        
        # Valor muito baixo
        alerta_baixo = AlertaService.avaliar_progresso_objetivo(
            objetivo_descricao="PA < 140",
            parametro="PA sistólica",
            valor_atual=70,
            valor_objetivo=140,
            unidade="mmHg",
            dados_historicos=[{"data": datetime.now(), "valor": 70}],
            dias_desde_inicio=1
        )
        
        assert alerta_baixo is not None

        # Acompanhamento com extremos
        acomp = AcompanhamentoService.gerar_plano_acompanhamento(
            condicao_cronica_id=1,
            cid10="I10",
            diagnostico="HAS",
            nivel_alerta="CRITICO",
            score_controle=0,
            parametro_principal="PA sistólica",
            valor_atual=250,
            valor_objetivo=140,
            medicacoes_atuais=[],
            aderencia_medicacao=0.0
        )
        
        assert acomp is not None
        assert acomp.frequencia_dias > 0

    def test_dados_minimos(self):
        """Pipeline funciona com dados mínimos"""
        # Plano simples
        plano = PlanoCuidadoService.criar_plano_completo(
            condicao_cronica_id=1,
            cid10="I10",
            diagnostico="HAS",
            estagio="CONTROLADA",
            classificacao_nivel="LEVE",
            idade_anos=65,
            comorbidades=[]
        )
        
        assert plano is not None

        # Uma medição
        alerta = AlertaService.avaliar_progresso_objetivo(
            objetivo_descricao="PA < 140",
            parametro="PA sistólica",
            valor_atual=145,
            valor_objetivo=140,
            unidade="mmHg",
            dados_historicos=[{"data": datetime.now(), "valor": 145}],
            dias_desde_inicio=0
        )
        
        assert alerta is not None

        # Acompanhamento vazio
        acomp = AcompanhamentoService.gerar_plano_acompanhamento(
            condicao_cronica_id=1,
            cid10="I10",
            diagnostico="HAS",
            nivel_alerta=alerta.nivel,
            score_controle=50,
            parametro_principal="PA sistólica",
            valor_atual=145,
            valor_objetivo=140,
            medicacoes_atuais=[],
            aderencia_medicacao=0.0
        )
        
        assert acomp is not None
