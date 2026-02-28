"""
Framingham Risk Score Calculator

Implementação do algoritmo Framingham para cálculo de risco cardiovascular em 10 anos.

Referência: Framingham Heart Study (D'Agostino et al., 2008)
"""

from typing import Dict, Tuple, List
from .models import FraminghamInput, FraminghamOutput


class FraminghamCalculator:
    """Calculadora de risco cardiovascular Framingham"""
    
    # ========================================================================
    # TABELAS DE PONTOS - HOMENS
    # ========================================================================
    
    PONTOS_IDADE_M: Dict[Tuple[int, int], int] = {
        (30, 34): -1,
        (35, 39): 0,
        (40, 44): 1,
        (45, 49): 2,
        (50, 54): 3,
        (55, 59): 4,
        (60, 64): 5,
        (65, 69): 6,
        (70, 74): 7,
    }
    
    PONTOS_COLESTEROL_M: Dict[Tuple[int, int], int] = {
        (0, 159): -3,
        (160, 199): 0,
        (200, 239): 1,
        (240, 279): 2,
        (280, 400): 3,
    }
    
    PONTOS_HDL_M: Dict[Tuple[int, int], int] = {
        (0, 34): 2,
        (35, 44): 1,
        (45, 49): 0,
        (50, 59): 0,
        (60, 100): -1,
    }
    
    PONTOS_PA_M: Dict[Tuple[int, int], int] = {
        (0, 119): -2,
        (120, 129): 0,
        (130, 139): 1,
        (140, 159): 2,
        (160, 200): 3,
    }
    
    PONTOS_TABAGISMO_M: int = 2
    PONTOS_DIABETES_M: int = 2
    
    # Conversão de pontos para risco % (homens)
    RISCO_M: Dict[int, float] = {
        -3: 1.1, -2: 1.4, -1: 1.6, 0: 1.9, 1: 2.3,
        2: 2.8, 3: 3.3, 4: 3.9, 5: 4.7, 6: 5.6,
        7: 6.7, 8: 7.9, 9: 9.4, 10: 11.2, 11: 13.2,
        12: 15.6, 13: 18.4, 14: 21.6, 15: 25.3, 16: 29.4,
        17: 30.0,  # >= 17 pontos
    }
    
    # ========================================================================
    # TABELAS DE PONTOS - MULHERES
    # ========================================================================
    
    PONTOS_IDADE_F: Dict[Tuple[int, int], int] = {
        (30, 34): -9,
        (35, 39): -4,
        (40, 44): 0,
        (45, 49): 3,
        (50, 54): 6,
        (55, 59): 7,
        (60, 64): 8,
        (65, 69): 8,
        (70, 74): 8,
    }
    
    PONTOS_COLESTEROL_F: Dict[Tuple[int, int], int] = {
        (0, 159): -2,
        (160, 199): 0,
        (200, 239): 1,
        (240, 279): 1,
        (280, 400): 3,
    }
    
    PONTOS_HDL_F: Dict[Tuple[int, int], int] = {
        (0, 34): 5,
        (35, 44): 2,
        (45, 49): 1,
        (50, 59): 0,
        (60, 100): -2,
    }
    
    PONTOS_PA_F: Dict[Tuple[int, int], int] = {
        (0, 119): -3,
        (120, 129): 0,
        (130, 139): 0,
        (140, 149): 2,
        (150, 159): 4,
        (160, 200): 5,
    }
    
    PONTOS_TABAGISMO_F: int = 3
    PONTOS_DIABETES_F: int = 4
    
    # Conversão de pontos para risco % (mulheres)
    RISCO_F: Dict[int, float] = {
        -2: 1.0, -1: 1.2, 0: 1.5, 1: 1.7, 2: 2.0,
        3: 2.4, 4: 2.8, 5: 3.3, 6: 3.9, 7: 4.5,
        8: 5.3, 9: 6.3, 10: 7.3, 11: 8.6, 12: 10.0,
        13: 11.7, 14: 13.7, 15: 15.9, 16: 18.5, 17: 21.5,
        18: 24.8, 19: 27.5, 20: 30.0,  # >= 20 pontos
    }
    
    # ========================================================================
    # MÉTODOS PRINCIPAIS
    # ========================================================================
    
    @classmethod
    def calcular(cls, input_data: FraminghamInput) -> FraminghamOutput:
        """
        Calcula risco cardiovascular Framingham
        
        Args:
            input_data: Dados do paciente
            
        Returns:
            FraminghamOutput com risco calculado e recomendações
        """
        # Selecionar tabelas baseado no sexo
        if input_data.sexo == "M":
            pontos_idade_tabela = cls.PONTOS_IDADE_M
            pontos_col_tabela = cls.PONTOS_COLESTEROL_M
            pontos_hdl_tabela = cls.PONTOS_HDL_M
            pontos_pa_tabela = cls.PONTOS_PA_M
            pontos_tabagismo = cls.PONTOS_TABAGISMO_M
            pontos_diabetes = cls.PONTOS_DIABETES_M
            risco_tabela = cls.RISCO_M
        else:
            pontos_idade_tabela = cls.PONTOS_IDADE_F
            pontos_col_tabela = cls.PONTOS_COLESTEROL_F
            pontos_hdl_tabela = cls.PONTOS_HDL_F
            pontos_pa_tabela = cls.PONTOS_PA_F
            pontos_tabagismo = cls.PONTOS_TABAGISMO_F
            pontos_diabetes = cls.PONTOS_DIABETES_F
            risco_tabela = cls.RISCO_F
        
        # Calcular pontos por fator
        pts_idade = cls._buscar_pontos(input_data.idade, pontos_idade_tabela)
        pts_colesterol = cls._buscar_pontos(input_data.colesterol_total, pontos_col_tabela)
        pts_hdl = cls._buscar_pontos(input_data.hdl, pontos_hdl_tabela)
        pts_pa = cls._buscar_pontos(input_data.pa_sistolica, pontos_pa_tabela)
        pts_tabagismo = pontos_tabagismo if input_data.tabagismo else 0
        pts_diabetes = pontos_diabetes if input_data.diabetes else 0
        
        # Total de pontos
        pontos_totais = pts_idade + pts_colesterol + pts_hdl + pts_pa + pts_tabagismo + pts_diabetes
        
        # Converter pontos em risco %
        risco_10_anos = cls._pontos_para_risco(pontos_totais, risco_tabela)
        
        # Classificar risco
        if risco_10_anos < 10:
            classificacao = "baixo"
        elif risco_10_anos < 20:
            classificacao = "intermediario"
        else:
            classificacao = "alto"
        
        # Gerar recomendações
        recomendacoes = cls._gerar_recomendacoes(input_data, risco_10_anos, classificacao)
        
        return FraminghamOutput(
            risco_10_anos=round(risco_10_anos, 1),
            classificacao=classificacao,
            pontos_totais=pontos_totais,
            recomendacoes=recomendacoes,
            pontos_idade=pts_idade,
            pontos_colesterol=pts_colesterol,
            pontos_hdl=pts_hdl,
            pontos_pa=pts_pa,
            pontos_tabagismo=pts_tabagismo,
            pontos_diabetes=pts_diabetes,
        )

    # ========================================================================
    # MÉTODOS AUXILIARES
    # ========================================================================

    @staticmethod
    def _buscar_pontos(valor: float, tabela: Dict[Tuple[int, int], int]) -> int:
        """
        Busca pontos na tabela baseado no valor

        Args:
            valor: Valor a buscar (idade, colesterol, etc.)
            tabela: Tabela de pontos

        Returns:
            Pontos correspondentes
        """
        for (min_val, max_val), pontos in tabela.items():
            if min_val <= valor <= max_val:
                return pontos

        # Se não encontrou, retornar 0 (não deveria acontecer com validação)
        return 0

    @staticmethod
    def _pontos_para_risco(pontos: int, tabela_risco: Dict[int, float]) -> float:
        """
        Converte pontos totais em risco percentual

        Args:
            pontos: Pontos totais calculados
            tabela_risco: Tabela de conversão pontos -> risco

        Returns:
            Risco em percentual (0-100)
        """
        # Se pontos está na tabela, retornar direto
        if pontos in tabela_risco:
            return tabela_risco[pontos]

        # Se pontos é menor que o mínimo, retornar risco mínimo
        min_pontos = min(tabela_risco.keys())
        if pontos < min_pontos:
            return tabela_risco[min_pontos]

        # Se pontos é maior que o máximo, retornar risco máximo
        max_pontos = max(tabela_risco.keys())
        if pontos > max_pontos:
            return tabela_risco[max_pontos]

        # Interpolação linear entre pontos adjacentes
        pontos_inferior = max(p for p in tabela_risco.keys() if p < pontos)
        pontos_superior = min(p for p in tabela_risco.keys() if p > pontos)

        risco_inferior = tabela_risco[pontos_inferior]
        risco_superior = tabela_risco[pontos_superior]

        # Interpolação
        fator = (pontos - pontos_inferior) / (pontos_superior - pontos_inferior)
        risco = risco_inferior + fator * (risco_superior - risco_inferior)

        return risco

    @staticmethod
    def _gerar_recomendacoes(
        input_data: FraminghamInput,
        risco: float,
        classificacao: str
    ) -> List[str]:
        """
        Gera recomendações clínicas baseadas no risco e fatores

        Args:
            input_data: Dados do paciente
            risco: Risco calculado (%)
            classificacao: Classificação do risco

        Returns:
            Lista de recomendações
        """
        recomendacoes = []

        # Recomendações baseadas na classificação de risco
        if classificacao == "alto":
            recomendacoes.append("⚠️ RISCO ALTO: Prevenção primária urgente necessária")
            recomendacoes.append("Estatina de alta intensidade (Atorvastatina 40-80mg ou Rosuvastatina 20-40mg)")
            recomendacoes.append("Meta LDL < 70 mg/dL")
            recomendacoes.append("Considerar AAS 100mg/dia para prevenção primária")
        elif classificacao == "intermediario":
            recomendacoes.append("⚠️ RISCO INTERMEDIÁRIO: Acompanhamento intensivo recomendado")
            recomendacoes.append("Estatina de intensidade moderada (Atorvastatina 10-20mg)")
            recomendacoes.append("Meta LDL < 100 mg/dL")
        else:
            recomendacoes.append("✅ RISCO BAIXO: Manter estilo de vida saudável")
            recomendacoes.append("Reavaliação anual do risco cardiovascular")

        # Recomendações específicas por fator de risco

        # Pressão arterial
        if input_data.pa_sistolica >= 140:
            recomendacoes.append("🩺 Controle rigoroso da pressão arterial (meta < 130/80 mmHg)")
            recomendacoes.append("Considerar anti-hipertensivo (IECA ou BRA)")
        elif input_data.pa_sistolica >= 130:
            recomendacoes.append("🩺 Monitorar pressão arterial (pré-hipertensão)")

        # Tabagismo
        if input_data.tabagismo:
            recomendacoes.append("🚭 CESSAÇÃO DO TABAGISMO URGENTE - reduz risco em 50% em 1 ano")
            recomendacoes.append("Encaminhar para programa de cessação tabágica")
            recomendacoes.append("Considerar terapia de reposição de nicotina ou Bupropiona/Vareniclina")

        # Diabetes
        if input_data.diabetes:
            recomendacoes.append("💉 Controle glicêmico rigoroso (HbA1c < 7%)")
            recomendacoes.append("Considerar Metformina + SGLT2i ou GLP-1 RA (proteção cardiovascular)")

        # HDL baixo
        if input_data.hdl < 40:
            recomendacoes.append("📊 HDL muito baixo - aumentar atividade física (150 min/semana)")
            recomendacoes.append("Considerar Fenofibrato se triglicerídeos > 200 mg/dL")

        # Colesterol alto
        if input_data.colesterol_total >= 240:
            recomendacoes.append("📊 Colesterol total elevado - dieta DASH + estatina")

        # Idade
        if input_data.idade >= 65:
            recomendacoes.append("👴 Idade avançada - rastreamento anual de doença cardiovascular")

        # Recomendações gerais
        recomendacoes.append("🏃 Atividade física regular: 150 min/semana de exercício moderado")
        recomendacoes.append("🥗 Dieta mediterrânea ou DASH (rica em frutas, vegetais, grãos integrais)")
        recomendacoes.append("⚖️ Manter peso saudável (IMC 18.5-24.9)")

        return recomendacoes

