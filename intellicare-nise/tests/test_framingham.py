"""
Testes para Framingham Risk Score Calculator
"""

import pytest
from nise.services.framingham import FraminghamCalculator, FraminghamInput, FraminghamOutput


class TestFraminghamCalculator:
    """Testes para FraminghamCalculator"""
    
    def test_calcular_risco_baixo_homem(self):
        """Testa cálculo de risco baixo para homem"""
        # Homem jovem, sem fatores de risco
        input_data = FraminghamInput(
            sexo="M",
            idade=35,
            colesterol_total=180,
            hdl=55,
            pa_sistolica=115,
            tabagismo=False,
            diabetes=False,
        )
        
        resultado = FraminghamCalculator.calcular(input_data)
        
        assert resultado.risco_10_anos < 10
        assert resultado.classificacao == "baixo"
        assert resultado.pontos_totais < 10
        assert len(resultado.recomendacoes) > 0
        assert "RISCO BAIXO" in resultado.recomendacoes[0]
    
    def test_calcular_risco_intermediario_homem(self):
        """Testa cálculo de risco intermediário para homem"""
        # Homem meia-idade, alguns fatores de risco
        input_data = FraminghamInput(
            sexo="M",
            idade=60,
            colesterol_total=240,
            hdl=40,
            pa_sistolica=150,
            tabagismo=True,
            diabetes=False,
        )

        resultado = FraminghamCalculator.calcular(input_data)

        assert 10 <= resultado.risco_10_anos < 20
        assert resultado.classificacao == "intermediario"
        assert resultado.pontos_tabagismo == 2  # Homem fumante = 2 pontos
        assert len(resultado.recomendacoes) > 0
        assert "INTERMEDIÁRIO" in resultado.recomendacoes[0]
        assert any("CESSAÇÃO DO TABAGISMO" in r for r in resultado.recomendacoes)
    
    def test_calcular_risco_alto_homem(self):
        """Testa cálculo de risco alto para homem"""
        # Homem idoso, múltiplos fatores de risco
        input_data = FraminghamInput(
            sexo="M",
            idade=70,
            colesterol_total=280,
            hdl=30,
            pa_sistolica=165,
            tabagismo=True,
            diabetes=True,
        )
        
        resultado = FraminghamCalculator.calcular(input_data)
        
        assert resultado.risco_10_anos >= 20
        assert resultado.classificacao == "alto"
        assert resultado.pontos_tabagismo == 2
        assert resultado.pontos_diabetes == 2
        assert len(resultado.recomendacoes) > 0
        assert "RISCO ALTO" in resultado.recomendacoes[0]
        assert any("Estatina de alta intensidade" in r for r in resultado.recomendacoes)
    
    def test_calcular_risco_baixo_mulher(self):
        """Testa cálculo de risco baixo para mulher"""
        # Mulher jovem, sem fatores de risco
        input_data = FraminghamInput(
            sexo="F",
            idade=40,
            colesterol_total=170,
            hdl=60,
            pa_sistolica=110,
            tabagismo=False,
            diabetes=False,
        )
        
        resultado = FraminghamCalculator.calcular(input_data)
        
        assert resultado.risco_10_anos < 10
        assert resultado.classificacao == "baixo"
        assert resultado.pontos_hdl < 0  # HDL alto = pontos negativos
        assert len(resultado.recomendacoes) > 0
    
    def test_calcular_risco_alto_mulher(self):
        """Testa cálculo de risco alto para mulher"""
        # Mulher idosa, múltiplos fatores de risco
        input_data = FraminghamInput(
            sexo="F",
            idade=68,
            colesterol_total=270,
            hdl=32,
            pa_sistolica=160,
            tabagismo=True,
            diabetes=True,
        )
        
        resultado = FraminghamCalculator.calcular(input_data)
        
        assert resultado.risco_10_anos >= 10  # Mulheres geralmente têm risco menor
        assert resultado.pontos_tabagismo == 3  # Mulher fumante = 3 pontos
        assert resultado.pontos_diabetes == 4  # Mulher diabética = 4 pontos
        assert len(resultado.recomendacoes) > 0
    
    def test_pontos_idade(self):
        """Testa cálculo de pontos por idade"""
        # Homem 35 anos
        input_base = FraminghamInput(
            sexo="M",
            idade=35,
            colesterol_total=180,
            hdl=50,
            pa_sistolica=120,
            tabagismo=False,
            diabetes=False,
        )
        
        resultado = FraminghamCalculator.calcular(input_base)
        assert resultado.pontos_idade == 0  # 35-39 anos = 0 pontos
        
        # Homem 60 anos
        input_idoso = FraminghamInput(
            sexo="M",
            idade=60,
            colesterol_total=180,
            hdl=50,
            pa_sistolica=120,
            tabagismo=False,
            diabetes=False,
        )
        
        resultado_idoso = FraminghamCalculator.calcular(input_idoso)
        assert resultado_idoso.pontos_idade == 5  # 60-64 anos = 5 pontos
        assert resultado_idoso.pontos_totais > resultado.pontos_totais
    
    def test_pontos_colesterol(self):
        """Testa cálculo de pontos por colesterol"""
        # Colesterol baixo
        input_baixo = FraminghamInput(
            sexo="M",
            idade=50,
            colesterol_total=150,
            hdl=50,
            pa_sistolica=120,
            tabagismo=False,
            diabetes=False,
        )
        
        resultado_baixo = FraminghamCalculator.calcular(input_baixo)
        assert resultado_baixo.pontos_colesterol == -3  # < 160 = -3 pontos
        
        # Colesterol alto
        input_alto = FraminghamInput(
            sexo="M",
            idade=50,
            colesterol_total=290,
            hdl=50,
            pa_sistolica=120,
            tabagismo=False,
            diabetes=False,
        )
        
        resultado_alto = FraminghamCalculator.calcular(input_alto)
        assert resultado_alto.pontos_colesterol == 3  # >= 280 = 3 pontos
        assert resultado_alto.pontos_totais > resultado_baixo.pontos_totais

    def test_pontos_hdl(self):
        """Testa cálculo de pontos por HDL"""
        # HDL alto (protetor)
        input_hdl_alto = FraminghamInput(
            sexo="M",
            idade=50,
            colesterol_total=200,
            hdl=65,
            pa_sistolica=120,
            tabagismo=False,
            diabetes=False,
        )

        resultado_hdl_alto = FraminghamCalculator.calcular(input_hdl_alto)
        assert resultado_hdl_alto.pontos_hdl == -1  # >= 60 = -1 ponto

        # HDL baixo (risco)
        input_hdl_baixo = FraminghamInput(
            sexo="M",
            idade=50,
            colesterol_total=200,
            hdl=30,
            pa_sistolica=120,
            tabagismo=False,
            diabetes=False,
        )

        resultado_hdl_baixo = FraminghamCalculator.calcular(input_hdl_baixo)
        assert resultado_hdl_baixo.pontos_hdl == 2  # < 35 = 2 pontos
        assert resultado_hdl_baixo.pontos_totais > resultado_hdl_alto.pontos_totais

    def test_pontos_pressao_arterial(self):
        """Testa cálculo de pontos por pressão arterial"""
        # PA ótima
        input_pa_otima = FraminghamInput(
            sexo="M",
            idade=50,
            colesterol_total=200,
            hdl=50,
            pa_sistolica=115,
            tabagismo=False,
            diabetes=False,
        )

        resultado_pa_otima = FraminghamCalculator.calcular(input_pa_otima)
        assert resultado_pa_otima.pontos_pa == -2  # < 120 = -2 pontos

        # PA elevada
        input_pa_alta = FraminghamInput(
            sexo="M",
            idade=50,
            colesterol_total=200,
            hdl=50,
            pa_sistolica=165,
            tabagismo=False,
            diabetes=False,
        )

        resultado_pa_alta = FraminghamCalculator.calcular(input_pa_alta)
        assert resultado_pa_alta.pontos_pa == 3  # >= 160 = 3 pontos
        assert resultado_pa_alta.pontos_totais > resultado_pa_otima.pontos_totais

    def test_pontos_tabagismo(self):
        """Testa cálculo de pontos por tabagismo"""
        # Não fumante
        input_nao_fumante = FraminghamInput(
            sexo="M",
            idade=50,
            colesterol_total=200,
            hdl=50,
            pa_sistolica=120,
            tabagismo=False,
            diabetes=False,
        )

        resultado_nao_fumante = FraminghamCalculator.calcular(input_nao_fumante)
        assert resultado_nao_fumante.pontos_tabagismo == 0

        # Fumante homem
        input_fumante_m = FraminghamInput(
            sexo="M",
            idade=50,
            colesterol_total=200,
            hdl=50,
            pa_sistolica=120,
            tabagismo=True,
            diabetes=False,
        )

        resultado_fumante_m = FraminghamCalculator.calcular(input_fumante_m)
        assert resultado_fumante_m.pontos_tabagismo == 2

        # Fumante mulher
        input_fumante_f = FraminghamInput(
            sexo="F",
            idade=50,
            colesterol_total=200,
            hdl=50,
            pa_sistolica=120,
            tabagismo=True,
            diabetes=False,
        )

        resultado_fumante_f = FraminghamCalculator.calcular(input_fumante_f)
        assert resultado_fumante_f.pontos_tabagismo == 3  # Mulher fumante = 3 pontos

    def test_pontos_diabetes(self):
        """Testa cálculo de pontos por diabetes"""
        # Sem diabetes
        input_sem_dm = FraminghamInput(
            sexo="M",
            idade=50,
            colesterol_total=200,
            hdl=50,
            pa_sistolica=120,
            tabagismo=False,
            diabetes=False,
        )

        resultado_sem_dm = FraminghamCalculator.calcular(input_sem_dm)
        assert resultado_sem_dm.pontos_diabetes == 0

        # Com diabetes homem
        input_dm_m = FraminghamInput(
            sexo="M",
            idade=50,
            colesterol_total=200,
            hdl=50,
            pa_sistolica=120,
            tabagismo=False,
            diabetes=True,
        )

        resultado_dm_m = FraminghamCalculator.calcular(input_dm_m)
        assert resultado_dm_m.pontos_diabetes == 2

        # Com diabetes mulher
        input_dm_f = FraminghamInput(
            sexo="F",
            idade=50,
            colesterol_total=200,
            hdl=50,
            pa_sistolica=120,
            tabagismo=False,
            diabetes=True,
        )

        resultado_dm_f = FraminghamCalculator.calcular(input_dm_f)
        assert resultado_dm_f.pontos_diabetes == 4  # Mulher diabética = 4 pontos

    def test_recomendacoes_risco_alto(self):
        """Testa geração de recomendações para risco alto"""
        input_data = FraminghamInput(
            sexo="M",
            idade=65,
            colesterol_total=260,
            hdl=35,
            pa_sistolica=155,
            tabagismo=True,
            diabetes=True,
        )

        resultado = FraminghamCalculator.calcular(input_data)

        # Verificar recomendações específicas
        recomendacoes_str = " ".join(resultado.recomendacoes)

        assert "RISCO ALTO" in recomendacoes_str or "RISCO INTERMEDIÁRIO" in recomendacoes_str
        assert "Estatina" in recomendacoes_str
        assert "CESSAÇÃO DO TABAGISMO" in recomendacoes_str
        assert "Controle glicêmico" in recomendacoes_str or "diabetes" in recomendacoes_str.lower()
        assert "pressão arterial" in recomendacoes_str.lower()

    def test_validacao_idade_minima(self):
        """Testa validação de idade mínima"""
        with pytest.raises(ValueError):
            FraminghamInput(
                sexo="M",
                idade=25,  # Abaixo do mínimo (30)
                colesterol_total=200,
                hdl=50,
                pa_sistolica=120,
                tabagismo=False,
                diabetes=False,
            )

    def test_validacao_idade_maxima(self):
        """Testa validação de idade máxima"""
        with pytest.raises(ValueError):
            FraminghamInput(
                sexo="M",
                idade=80,  # Acima do máximo (74)
                colesterol_total=200,
                hdl=50,
                pa_sistolica=120,
                tabagismo=False,
                diabetes=False,
            )

    def test_validacao_colesterol(self):
        """Testa validação de colesterol"""
        with pytest.raises(ValueError):
            FraminghamInput(
                sexo="M",
                idade=50,
                colesterol_total=50,  # Abaixo do mínimo (100)
                hdl=50,
                pa_sistolica=120,
                tabagismo=False,
                diabetes=False,
            )

    def test_output_completo(self):
        """Testa que output contém todos os campos necessários"""
        input_data = FraminghamInput(
            sexo="M",
            idade=55,
            colesterol_total=220,
            hdl=45,
            pa_sistolica=140,
            tabagismo=True,
            diabetes=False,
        )

        resultado = FraminghamCalculator.calcular(input_data)

        # Verificar campos obrigatórios
        assert isinstance(resultado.risco_10_anos, float)
        assert resultado.classificacao in ["baixo", "intermediario", "alto"]
        assert isinstance(resultado.pontos_totais, int)
        assert isinstance(resultado.recomendacoes, list)
        assert len(resultado.recomendacoes) > 0

        # Verificar detalhamento de pontos
        assert isinstance(resultado.pontos_idade, int)
        assert isinstance(resultado.pontos_colesterol, int)
        assert isinstance(resultado.pontos_hdl, int)
        assert isinstance(resultado.pontos_pa, int)
        assert isinstance(resultado.pontos_tabagismo, int)
        assert isinstance(resultado.pontos_diabetes, int)

        # Verificar soma de pontos
        soma_pontos = (
            resultado.pontos_idade +
            resultado.pontos_colesterol +
            resultado.pontos_hdl +
            resultado.pontos_pa +
            resultado.pontos_tabagismo +
            resultado.pontos_diabetes
        )
        assert soma_pontos == resultado.pontos_totais

