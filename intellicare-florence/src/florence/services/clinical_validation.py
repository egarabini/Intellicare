"""
Clinical Algorithm Validation Service for Florence

Validadores clínicos que garantem coerência entre resultados de exames
e detectam simulções ou erros de equipamento
"""

import logging
from typing import Tuple, Dict, Any, Optional
from decimal import Decimal

logger = logging.getLogger(__name__)


class ClinicaAlgorithmValidator:
    """
    Validadores clínicos para garantir coerência de exames
    
    Valida:
    1. Hemograma: Coerência entre Hemoglobina, Hematócrito, Plaquetas
    2. Lipidograma: Equação de Friedewald para LDL
    3. Hepatograma: Proporção entre enzimas hepáticas
    4. Glicemia: Valores fisiológicos por tipo de paciente
    5. Função renal: Coerência entre Ureia e Creatinina
    """
    
    # Ranges fisiológicos por parâmetro
    RANGES_NORMAIS = {
        # Hemograma
        "hemoglobina_h": (13.5, 17.5),  # g/dL homem
        "hemoglobina_m": (12.0, 15.5),  # g/dL mulher
        "hematocrito_h": (40.0, 54.0),  # % homem
        "hematocrito_m": (36.0, 46.0),  # % mulher
        "plaquetas": (150, 400),  # mil/μL
        "leucócitos": (4.5, 11.0),  # mil/μL
        "neutrófilos": (50, 70),  # %
        "linfócitos": (20, 40),  # %
        "monócitos": (2, 10),  # %
        "eosinófilos": (1, 4),  # %
        "basófilos": (0, 1),  # %
        
        # Lipidograma
        "colesterol_total": (0, 200),  # mg/dL desejável
        "triglicérides": (0, 150),  # mg/dL desejável
        "hdl": (40, 100),  # mg/dL
        "ldl": (0, 100),  # mg/dL ótimo
        
        # Glicemia
        "glicemia_jejum": (70, 99),  # mg/dL normal
        "glicemia_aleatorio": (70, 140),  # mg/dL
        
        # Hepatograma
        "ast": (10, 40),  # U/L (ALT)
        "alt": (7, 56),  # U/L (AST)
        "bilirrubina_total": (0.3, 1.2),  # mg/dL
        "bilirrubina_direta": (0.0, 0.3),  # mg/dL
        "fosfatase_alcalina": (44, 147),  # U/L
        
        # Função renal
        "creatinina": (0.7, 1.3),  # mg/dL
        "ureia": (7, 20),  # mg/dL
    }
    
    @classmethod
    def validar_hemograma(
        cls,
        hemoglobina: float,
        hematocrito: float,
        plaquetas: float,
        leucócitos: float,
        diferenciais: Dict[str, float],
        sexo: str = "M",
    ) -> Tuple[bool, str]:
        """
        Valida coerência do hemograma
        
        Regras clínicas:
        1. Hemoglobina vs. Hematócrito: Relação esperada ~1:3
        2. Diferencial leucocitário: Soma deve ser 100%
        3. Plaquetas em range fisiológico
        4. Valores individuais coerentes
        
        Args:
            hemoglobina: Hemoglobina em g/dL
            hematocrito: Hematócrito em %
            plaquetas: Plaquetas em mil/μL
            leucócitos: Leucócitos em mil/μL
            diferenciais: Dict com neutrófilos, linfócitos, monócitos, etc (%)
            sexo: "M" ou "F" para ranges específicos
            
        Returns:
            Tuple (válido, mensagem)
        """
        
        erros = []
        
        # 1. Validar ranges individuais
        if sexo == "M":
            hemo_min, hemo_max = cls.RANGES_NORMAIS["hemoglobina_h"]
            hema_min, hema_max = cls.RANGES_NORMAIS["hematocrito_h"]
        else:
            hemo_min, hemo_max = cls.RANGES_NORMAIS["hemoglobina_m"]
            hema_min, hema_max = cls.RANGES_NORMAIS["hematocrito_m"]
        
        if not (hemo_min <= hemoglobina <= hemo_max):
            erros.append(
                f"Hemoglobina {hemoglobina} fora do range {hemo_min}-{hemo_max}"
            )
        
        if not (hema_min <= hematocrito <= hema_max):
            erros.append(
                f"Hematócrito {hematocrito} fora do range {hema_min}-{hema_max}"
            )
        
        # 2. Validar relação Hemoglobina/Hematócrito
        # Relação esperada: Ht ≈ Hb × 3 (±5%)
        razao_esperada = hemoglobina * 3
        tolerancia = razao_esperada * 0.05  # 5%
        
        if not (razao_esperada - tolerancia <= hematocrito <= razao_esperada + tolerancia):
            erros.append(
                f"Proporção Hb/Ht anormal: Hb={hemoglobina}, "
                f"Ht={hematocrito}, esperado ~{razao_esperada:.1f}±{tolerancia:.1f}"
            )
        
        # 3. Validar plaquetas
        pq_min, pq_max = cls.RANGES_NORMAIS["plaquetas"]
        if not (pq_min <= plaquetas <= pq_max):
            erros.append(f"Plaquetas {plaquetas} fora do range {pq_min}-{pq_max}")
        
        # 4. Validar leucócitos
        lc_min, lc_max = cls.RANGES_NORMAIS["leucócitos"]
        if not (lc_min <= leucócitos <= lc_max):
            erros.append(f"Leucócitos {leucócitos} fora do range {lc_min}-{lc_max}")
        
        # 5. Validar diferencial leucocitário soma 100%
        soma_diferenciais = sum(diferenciais.values())
        if not (98 <= soma_diferenciais <= 102):  # Permitir 2% de erro
            erros.append(
                f"Diferencial leucocitário soma {soma_diferenciais:.1f}% "
                f"(deve ser ~100%): {diferenciais}"
            )
        
        # 6. Validar ranges do diferencial
        for tipo, percentual in diferenciais.items():
            if tipo in cls.RANGES_NORMAIS:
                min_val, max_val = cls.RANGES_NORMAIS[tipo]
                if not (min_val <= percentual <= max_val):
                    erros.append(
                        f"{tipo.capitalize()} {percentual}% fora do range "
                        f"{min_val}-{max_val}%"
                    )
        
        if erros:
            return False, " | ".join(erros)
        
        return True, "Hemograma válido ✅"
    
    @classmethod
    def validar_lipidograma(
        cls,
        colesterol_total: float,
        triglicérides: float,
        hdl: float,
        ldl: Optional[float] = None,
    ) -> Tuple[bool, str]:
        """
        Valida lipidograma usando equação de Friedewald
        
        Equação de Friedewald: LDL = CT - HDL - TG/5
        
        Args:
            colesterol_total: mg/dL
            triglicérides: mg/dL
            hdl: mg/dL
            ldl: mg/dL (se fornecido, será validado contra Friedewald)
            
        Returns:
            Tuple (válido, mensagem)
        """
        
        erros = []
        
        # 1. Validar ranges individuais
        ct_min, ct_max = cls.RANGES_NORMAIS["colesterol_total"]
        if colesterol_total > ct_max:
            erros.append(f"Colesterol total {colesterol_total} > {ct_max} (alto)")
        
        tg_min, tg_max = cls.RANGES_NORMAIS["triglicérides"]
        if triglicérides > tg_max:
            erros.append(f"Triglicérides {triglicérides} > {tg_max} (alto)")
        
        hdl_min, hdl_max = cls.RANGES_NORMAIS["hdl"]
        if hdl < hdl_min:
            erros.append(f"HDL {hdl} < {hdl_min} (baixo)")
        
        # 2. Calcular LDL por Friedewald (se TG < 400)
        if triglicérides < 400:
            ldl_calculado = colesterol_total - hdl - (triglicérides / 5)
            
            # Validar se LDL foi fornecido
            if ldl is not None:
                # Permitir 5% de diferença (lab error)
                diferenca_percentual = abs(ldl - ldl_calculado) / ldl_calculado * 100
                
                if diferenca_percentual > 5:
                    erros.append(
                        f"LDL {ldl} não corresponde a Friedewald "
                        f"{ldl_calculado:.1f} (diferença {diferenca_percentual:.1f}%)"
                    )
        
        # 3. Validar relação CT vs componentes
        # CT ≈ LDL + HDL + TG/5
        soma_componentes = ldl_calculado + hdl + (triglicérides / 5)
        if soma_componentes != 0:
            diferenca_percentual = abs(colesterol_total - soma_componentes) / soma_componentes * 100
            if diferenca_percentual > 10:
                erros.append(
                    f"Colesterol total não corresponde soma dos componentes "
                    f"(diferença {diferenca_percentual:.1f}%)"
                )
        
        if erros:
            return False, " | ".join(erros)
        
        return True, "Lipidograma válido ✅"
    
    @classmethod
    def validar_hepatograma(
        cls,
        ast: float,
        alt: float,
        bilirrubina_total: float,
        bilirrubina_direta: float,
        fosfatase_alcalina: float,
    ) -> Tuple[bool, str]:
        """
        Valida hepatograma verificando coerência entre enzimas
        
        Regras:
        1. AST e ALT em ranges normais
        2. Bilirrubina direta <= Bilirrubina total
        3. Proporção de aumento proporcional
        
        Args:
            ast: U/L (ALT)
            alt: U/L (AST)
            bilirrubina_total: mg/dL
            bilirrubina_direta: mg/dL
            fosfatase_alcalina: U/L
            
        Returns:
            Tuple (válido, mensagem)
        """
        
        erros = []
        
        # 1. Validar ranges
        ast_min, ast_max = cls.RANGES_NORMAIS["alt"]
        if not (ast_min <= ast <= ast_max):
            erros.append(f"AST {ast} fora do range {ast_min}-{ast_max}")
        
        alt_min, alt_max = cls.RANGES_NORMAIS["ast"]
        if not (alt_min <= alt <= alt_max):
            erros.append(f"ALT {alt} fora do range {alt_min}-{alt_max}")
        
        # 2. Validar bilirrubinas
        if bilirrubina_direta > bilirrubina_total:
            erros.append(
                f"Bilirrubina direta {bilirrubina_direta} "
                f"> total {bilirrubina_total}"
            )
        
        bil_total_min, bil_total_max = cls.RANGES_NORMAIS["bilirrubina_total"]
        if bilirrubina_total > bil_total_max * 2:  # Permitir leve aumento
            erros.append(f"Bilirrubina total muito elevada: {bilirrubina_total}")
        
        # 3. Validar fosfatase alcalina
        fa_min, fa_max = cls.RANGES_NORMAIS["fosfatase_alcalina"]
        if not (fa_min <= fosfatase_alcalina <= fa_max * 1.5):
            erros.append(
                f"Fosfatase alcalina {fosfatase_alcalina} "
                f"fora do range esperado {fa_min}-{fa_max}"
            )
        
        if erros:
            return False, " | ".join(erros)
        
        return True, "Hepatograma válido ✅"
    
    @classmethod
    def validar_funcao_renal(
        cls,
        creatinina: float,
        ureia: float,
        idade: int = 50,
    ) -> Tuple[bool, str]:
        """
        Valida função renal por razão ureia/creatinina
        
        Razão normal: 10-20
        - Insuficiência pré-renal: > 20
        - Insuficiência renal: < 10
        
        Args:
            creatinina: mg/dL
            ureia: mg/dL
            idade: Idade do paciente (afeta range esperado)
            
        Returns:
            Tuple (válido, mensagem)
        """
        
        erros = []
        
        # 1. Validar ranges individuais
        cr_min, cr_max = cls.RANGES_NORMAIS["creatinina"]
        if creatinina > cr_max * 2:  # Permitir até 2x normal
            erros.append(f"Creatinina {creatinina} muito elevada (> {cr_max*2})")
        
        ur_min, ur_max = cls.RANGES_NORMAIS["ureia"]
        if ureia > ur_max * 2:
            erros.append(f"Ureia {ureia} muito elevada (> {ur_max*2})")
        
        # 2. Validar razão ureia/creatinina
        if creatinina != 0:
            razao = ureia / creatinina
            
            if razao > 20:
                erros.append(
                    f"Razão ureia/creatinina {razao:.1f} > 20 "
                    f"(sugere insuficiência pré-renal)"
                )
            elif razao < 10:
                erros.append(
                    f"Razão ureia/creatinina {razao:.1f} < 10 "
                    f"(sugere insuficiência renal ou hemodiálise)"
                )
        
        if erros:
            return False, " | ".join(erros)
        
        return True, "Função renal válida ✅"
    
    @classmethod
    def validar_glicemia(
        cls,
        glicemia: float,
        tipo_amostra: str = "jejum",
        paciente_diabetico: bool = False,
    ) -> Tuple[bool, str]:
        """
        Valida glicemia conforme contexto clínico
        
        Args:
            glicemia: mg/dL
            tipo_amostra: "jejum", "aleatório", "pos_prandial"
            paciente_diabetico: Se paciente tem diagnóstico de diabete
            
        Returns:
            Tuple (válido, mensagem)
        """
        
        erros = []
        
        if tipo_amostra == "jejum":
            if glicemia > 125:
                erros.append(f"Glicemia em jejum {glicemia} > 125 (suspeita diabete)")
            elif glicemia < 70:
                erros.append(f"Glicemia em jejum {glicemia} < 70 (hipoglicemia)")
        
        elif tipo_amostra == "aleatorio":
            if glicemia > 200:
                erros.append(f"Glicemia aleatória {glicemia} > 200 (crítica)")
            elif glicemia < 70:
                erros.append(f"Glicemia aleatória {glicemia} < 70 (hipoglicemia)")
        
        # Pacientes diabéticos têm ranges diferentes
        if paciente_diabetico and glicemia > 250:
            erros.append(
                f"Glicemia {glicemia} em paciente diabético "
                f"(considerar ajuste medicação)"
            )
        
        if erros:
            return False, " | ".join(erros)
        
        return True, "Glicemia válida ✅"
    
    @classmethod
    def validar_exame_completo(
        cls,
        exame_data: Dict[str, Any],
        sexo: str = "M",
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Valida exame completo com todas as regras clínicas
        
        Args:
            exame_data: Dicionário com todos os parâmetros
            sexo: "M" ou "F"
            
        Returns:
            Tuple (válido, resultado_validação)
        """
        
        resultado = {
            "válido": True,
            "validações": {},
            "avisos": [],
            "erros": [],
        }
        
        # Hemograma
        if all(k in exame_data for k in ["hemoglobina", "hematocrito", "plaquetas"]):
            valido, msg = cls.validar_hemograma(
                exame_data.get("hemoglobina"),
                exame_data.get("hematocrito"),
                exame_data.get("plaquetas"),
                exame_data.get("leucócitos", 0),
                exame_data.get("diferenciais", {}),
                sexo=sexo,
            )
            resultado["validações"]["hemograma"] = msg
            if not valido:
                resultado["erros"].append(f"Hemograma: {msg}")
                resultado["válido"] = False
        
        # Lipidograma
        if all(k in exame_data for k in ["colesterol_total", "triglicérides", "hdl"]):
            valido, msg = cls.validar_lipidograma(
                exame_data.get("colesterol_total"),
                exame_data.get("triglicérides"),
                exame_data.get("hdl"),
                exame_data.get("ldl"),
            )
            resultado["validações"]["lipidograma"] = msg
            if not valido:
                resultado["erros"].append(f"Lipidograma: {msg}")
                resultado["válido"] = False
        
        # Hepatograma
        if all(k in exame_data for k in ["ast", "alt", "bilirrubina_total"]):
            valido, msg = cls.validar_hepatograma(
                exame_data.get("ast"),
                exame_data.get("alt"),
                exame_data.get("bilirrubina_total"),
                exame_data.get("bilirrubina_direta", 0),
                exame_data.get("fosfatase_alcalina", 0),
            )
            resultado["validações"]["hepatograma"] = msg
            if not valido:
                resultado["erros"].append(f"Hepatograma: {msg}")
                resultado["válido"] = False
        
        # Função renal
        if all(k in exame_data for k in ["creatinina", "ureia"]):
            valido, msg = cls.validar_funcao_renal(
                exame_data.get("creatinina"),
                exame_data.get("ureia"),
                exame_data.get("idade", 50),
            )
            resultado["validações"]["funcao_renal"] = msg
            if not valido:
                resultado["erros"].append(f"Função renal: {msg}")
                resultado["válido"] = False
        
        # Glicemia
        if "glicemia" in exame_data:
            valido, msg = cls.validar_glicemia(
                exame_data.get("glicemia"),
                exame_data.get("tipo_amostra", "jejum"),
                exame_data.get("paciente_diabetico", False),
            )
            resultado["validações"]["glicemia"] = msg
            if not valido:
                resultado["erros"].append(f"Glicemia: {msg}")
                resultado["válido"] = False
        
        return resultado["válido"], resultado


__all__ = [
    "ClinicaAlgorithmValidator",
]
