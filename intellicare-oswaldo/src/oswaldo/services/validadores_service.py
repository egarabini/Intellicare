"""
Validadores Clínicos - Coerência Fisiológica e Detecção de Impossibilidades

Módulo responsável por:
1. Validar coerência fisiológica dos parâmetros
2. Detectar impossibilidades (valores fisiologicamente inviáveis)
3. Identificar inconsistências clínicas
4. Sugerir correções

Protocolos Internacionais:
- Hematologia: Normas de WBC diferenciais
- Bioquímica: Proporcionalidade de lipídios
- Cardiologia: Pressão sistólica >= diastólica
- Nefrologia: TFG baseado em idade
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Union
from datetime import datetime


@dataclass
class ValidacaoResult:
    """Resultado da validação clínica"""
    valido: bool
    erros: List[str] = field(default_factory=list)  # Críticos - falha validação
    avisos: List[str] = field(default_factory=list)  # Warnings notáveis
    sugestoes: List[str] = field(default_factory=list)  # Recomendações
    score_coerencia: int = 100  # 0-100
    detalhes: Dict[str, Union[str, float]] = field(default_factory=dict)


class ValidadoresClinicosService:
    """Serviço de validação de parâmetros clínicos"""

    # ========================================================================
    # 1. VALIDADORES DE COERÊNCIA
    # ========================================================================

    @staticmethod
    def validar_pressao_arterial(
        pressao_sistolica: float,
        pressao_diastolica: float,
        idade_anos: int = None
    ) -> ValidacaoResult:
        """
        Valida coerência da pressão arterial
        
        Regras:
        - Sistólica deve ser >= diastólica
        - Ambas devem estar em faixas fisiológicas
        - Diferença de pulso (sistóliga - diastólica) entre 30-60 mmHg (normal)
        
        Args:
            pressao_sistolica: Pressão sistólica em mmHg
            pressao_diastolica: Pressão diastólica em mmHg
            idade_anos: Idade do paciente (opcional)
            
        Returns:
            ValidacaoResult
        """
        resultado = ValidacaoResult(valido=True)
        score = 100

        # Verificar se sistólica >= diastólica
        if pressao_sistolica < pressao_diastolica:
            resultado.erros.append(
                f"PA sistólica ({pressao_sistolica}) não pode ser < diastólica ({pressao_diastolica})"
            )
            resultado.valido = False
            score -= 40

        # Faixas fisiológicas
        if pressao_sistolica < 50 or pressao_sistolica > 300:
            resultado.erros.append(
                f"PA sistólica {pressao_sistolica} fora da faixa fisiológica (50-300 mmHg)"
            )
            resultado.valido = False
            score -= 30

        if pressao_diastolica < 30 or pressao_diastolica > 200:
            resultado.erros.append(
                f"PA diastólica {pressao_diastolica} fora da faixa fisiológica (30-200 mmHg)"
            )
            resultado.valido = False
            score -= 30

        # Diferença de pulso (pulso = sistólica - diastólica)
        pulso = pressao_sistolica - pressao_diastolica
        if pulso < 20:
            resultado.avisos.append(f"Diferença de pulso muito baixa ({pulso} mmHg) - verificar precisão")
            score -= 10
        elif pulso > 80:
            resultado.avisos.append(f"Diferença de pulso elevada ({pulso} mmHg) - pode indicar esforço/ansiedade")
            score -= 5

        # Padrões hipertensivos por idade
        if idade_anos and idade_anos >= 65:
            if pressao_sistolica >= 140 and pulso > 70:
                resultado.sugestoes.append(
                    "Idoso (>=65a) com SPA isolada e pulso amplo - avaliar arterioesclerose"
                )

        resultado.score_coerencia = max(0, score)
        return resultado

    @staticmethod
    def validar_hemograma(
        wbc_total: float,
        leucocitos_seg: float = None,
        linfocitos: float = None,
        monocitos: float = None,
        eosinofilos: float = None,
        basofilos: float = None,
        hematocrito: float = None,
        hemoglobina: float = None
    ) -> ValidacaoResult:
        """
        Valida coerência dos parâmetros do hemograma
        
        Regras (conforme normas hematológicas):
        - Valores absolutos de leucócitos diferenciais devem somar 100%
        - Hemoglobina deve ser consistente com hematócrito (Hgb ≈ Hct/3)
        - Nenhum diferencial pode exceder 100% ou ser negativo
        
        Args:
            wbc_total: Leucócitos totais (mil/μL)
            leucocitos_seg: Segmentados (%)
            linfocitos: Linfócitos (%)
            monocitos: Monócitos (%)
            eosinofilos: Eosinófilos (%)
            basofilos: Basófilos (%)
            hematocrito: Hematócrito (%)
            hemoglobina: Hemoglobina (g/dL)
            
        Returns:
            ValidacaoResult
        """
        resultado = ValidacaoResult(valido=True)
        score = 100

        # Validar WBC total
        if wbc_total < 0 or wbc_total > 300:
            resultado.erros.append(f"WBC total {wbc_total} fora da faixa (0-300 mil/μL)")
            resultado.valido = False
            score -= 40

        # Validar diferenciais se fornecidos
        diferenciais = []
        if leucocitos_seg is not None:
            diferenciais.append(("Segmentados", leucocitos_seg))
        if linfocitos is not None:
            diferenciais.append(("Linfócitos", linfocitos))
        if monocitos is not None:
            diferenciais.append(("Monócitos", monocitos))
        if eosinofilos is not None:
            diferenciais.append(("Eosinófilos", eosinofilos))
        if basofilos is not None:
            diferenciais.append(("Basófilos", basofilos))

        # Validar que nenhum diferencial é negativo ou > 100%
        for nome, valor in diferenciais:
            if valor < 0:
                resultado.erros.append(f"{nome} não pode ser negativo ({valor}%)")
                resultado.valido = False
                score -= 25
            if valor > 100:
                resultado.erros.append(f"{nome} não pode exceder 100% ({valor}%)")
                resultado.valido = False
                score -= 25

        # Validar soma dos diferenciais = 100% (+/- 2% para arredondamento)
        if len(diferenciais) >= 4:
            soma = sum(v for _, v in diferenciais)
            if abs(soma - 100) > 2:
                resultado.avisos.append(
                    f"Soma de diferenciais = {soma}% (esperado 100% ±2%)"
                )
                score -= 15

        # Validar coerência hemoglobina/hematócrito (regra: Hgb ≈ Hct/3)
        if hemoglobina is not None and hematocrito is not None:
            hgb_esperado = hematocrito / 3
            desvio = abs(hemoglobina - hgb_esperado)
            if desvio > 3:
                resultado.avisos.append(
                    f"Hemoglobina ({hemoglobina}) inconsistente com hematócrito ({hematocrito}) - "
                    f"esperado ~{hgb_esperado:.1f}"
                )
                score -= 10

        resultado.score_coerencia = max(0, score)
        return resultado

    @staticmethod
    def validar_lipidios(
        colesterol_total: float,
        ldl: float = None,
        hdl: float = None,
        triglicerideos: float = None
    ) -> ValidacaoResult:
        """
        Valida coerência dos lipídios (regra de Friedewald)
        
        Regra: CT = LDL + HDL + (TG/5)
        Portanto: LDL + HDL deve ser <= CT
        
        Args:
            colesterol_total: Colesterol total (mg/dL)
            ldl: LDL colesterol (mg/dL)
            hdl: HDL colesterol (mg/dL)
            triglicerideos: Triglicerídeos (mg/dL)
            
        Returns:
            ValidacaoResult
        """
        resultado = ValidacaoResult(valido=True)
        score = 100

        # Validar CT fora de faixa
        if colesterol_total < 0 or colesterol_total > 1000:
            resultado.erros.append(f"Colesterol total {colesterol_total} fora da faixa (0-1000 mg/dL)")
            resultado.valido = False
            score -= 40

        # Se LDL e HDL fornecidos
        if ldl is not None and hdl is not None:
            ldl_hdl_sum = ldl + hdl
            if ldl_hdl_sum > colesterol_total * 1.05:  # 5% de margem
                resultado.avisos.append(
                    f"LDL ({ldl}) + HDL ({hdl}) = {ldl_hdl_sum} > CT ({colesterol_total}) - "
                    "valores inconsistentes (Friedewald)"
                )
                score -= 15

        # Validar proporção HDL
        if hdl is not None:
            if hdl < 0 or hdl > colesterol_total:
                resultado.erros.append(f"HDL {hdl} incoerente com CT {colesterol_total}")
                resultado.valido = False
                score -= 20
            if hdl < 30:
                resultado.avisos.append(f"HDL muito baixo ({hdl} mg/dL) - fator CV importante")
                score -= 10

        # Validar proporção LDL
        if ldl is not None:
            if ldl < 0 or ldl > colesterol_total:
                resultado.erros.append(f"LDL {ldl} incoerente com CT {colesterol_total}")
                resultado.valido = False
                score -= 20

        # Validar triglicerídeos (Friedewald: LDL = CT - HDL - TG/5)
        if triglicerideos is not None:
            if triglicerideos > 5000:
                resultado.erros.append(f"Triglicerídeos {triglicerideos} > 5000 mg/dL (impossível)")
                resultado.valido = False
                score -= 30
            elif triglicerideos > 400:
                resultado.avisos.append(f"Triglicerídeos muito elevados ({triglicerideos})")
                score -= 10

        resultado.score_coerencia = max(0, score)
        return resultado

    # ========================================================================
    # 2. DETECÇÃO DE IMPOSSIBILIDADES
    # ========================================================================

    @staticmethod
    def detectar_impossibilidades(parametros: Dict[str, Union[float, int]]) -> ValidacaoResult:
        """
        Detecta valores fisiologicamente impossíveis
        
        Impossibilidades verificadas:
        - Frequência cardíaca < 20 ou > 300 bpm
        - Temperatura < 35°C ou > 43°C
        - SpO2 > 100% ou < 50%
        - Idade > 150 anos
        - Valores negativos onde não permitido
        
        Args:
            parametros: Dict com pares chave-valor de parâmetros clínicos
            
        Returns:
            ValidacaoResult
        """
        resultado = ValidacaoResult(valido=True)
        score = 100

        # Frequência cardíaca
        if "frequencia_cardiaca" in parametros:
            fc = parametros["frequencia_cardiaca"]
            if fc < 20:
                resultado.erros.append(f"FC {fc} bpm - impossível (morte cerebral?)")
                resultado.valido = False
                score -= 50
            elif fc > 300:
                resultado.erros.append(f"FC {fc} bpm > 300 - impossível")
                resultado.valido = False
                score -= 50
            elif fc > 180:
                resultado.avisos.append(f"FC {fc} bpm - taquicardia severa")
                score -= 15

        # Temperatura
        if "temperatura_c" in parametros:
            temp = parametros["temperatura_c"]
            if temp < 35:
                resultado.erros.append(f"Temperatura {temp}°C < 35 - hipotermia crítica")
                resultado.valido = False
                score -= 50
            elif temp > 43:
                resultado.erros.append(f"Temperatura {temp}°C > 43 - impossível")
                resultado.valido = False
                score -= 50
            elif temp > 40:
                resultado.avisos.append(f"Febre alta ({temp}°C) - investigar infecção")
                score -= 10

        # SpO2
        if "spo2_perc" in parametros:
            spo2 = parametros["spo2_perc"]
            if spo2 > 100:
                resultado.erros.append(f"SpO2 {spo2}% > 100 - impossível")
                resultado.valido = False
                score -= 40
            elif spo2 < 50:
                resultado.erros.append(f"SpO2 {spo2}% < 50 - incompatível com vida")
                resultado.valido = False
                score -= 50
            elif spo2 < 88:
                resultado.avisos.append(f"SpO2 {spo2}% - hipoxemia significativa")
                score -= 20

        # Idade
        if "idade_anos" in parametros:
            idade = parametros["idade_anos"]
            if idade > 150:
                resultado.erros.append(f"Idade {idade} anos > 150 - impossível")
                resultado.valido = False
                score -= 40
            elif idade < 0:
                resultado.erros.append(f"Idade {idade} anos < 0 - impossível")
                resultado.valido = False
                score -= 40

        # Valores que não podem ser negativos
        campos_nao_negativos = [
            "peso_kg", "altura_cm", "imc", "glicemia", "creatinina",
            "ureia", "bilirubina_total", "albumina", "hemoglobina",
            "hematocrito", "plaquetas"
        ]
        for campo in campos_nao_negativos:
            if campo in parametros:
                valor = parametros[campo]
                if valor < 0:
                    resultado.erros.append(f"{campo} = {valor} - não pode ser negativo")
                    resultado.valido = False
                    score -= 25

        resultado.score_coerencia = max(0, score)
        return resultado

    # ========================================================================
    # 3. DETECÇÃO DE INCONSISTÊNCIAS CLÍNICAS
    # ========================================================================

    @staticmethod
    def detectar_inconsistencias_clinicas(
        classificacoes: Dict[str, str],  # Ex: {"HAS": "NORMAL", "DRC": "G1", ...}
        medicamentos_ativos: List[str],
        laboratorio: Dict[str, float]
    ) -> ValidacaoResult:
        """
        Detecta inconsistências lógicas entre classificações e medicações
        
        Exemplos:
        - HAS NORMAL mas em 4 anti-hipertensivos
        - Creatinina muito elevada (>3) mas GFR normal
        - HDL muito baixo (<30) mas não em estatinas
        - DM mal controlado (HbA1c >9) mas sem insulina
        
        Args:
            classificacoes: Dict com diagnósticos/estadiamentos
            medicamentos_ativos: Lista de medicamentos em uso
            laboratorio: Dict com parâmetros laboratoriais
            
        Returns:
            ValidacaoResult
        """
        resultado = ValidacaoResult(valido=True)
        score = 100

        # Flag 1: HAS NORMAL mas usando múltiplos anti-hipertensivos
        anti_htas = [
            m for m in medicamentos_ativos
            if any(x in m.lower() for x in ["losartan", "enalapril", "nifedipina", "atenolol"])
        ]
        if classificacoes.get("HAS") == "NORMAL" and len(anti_htas) >= 3:
            resultado.avisos.append(
                f"PA normal mas usando {len(anti_htas)} anti-hipertensivos - "
                "possível sub-dosagem ou super-tratamento"
            )
            score -= 15

        # Flag 2: Creatinina muito elevada mas GFR normal
        if laboratorio.get("creatinina", 0) > 3 and classificacoes.get("DRC") in ["G1", "G2"]:
            resultado.avisos.append(
                "Creatinina >3 mg/dL mas GFR normal (G1/G2) - "
                "possível erro de coleta ou paciente com pouca massa muscular"
            )
            score -= 10

        # Flag 3: HDL muito baixo mas não em estatinas
        em_estatina = any("estatina" in m.lower() for m in medicamentos_ativos)
        hdl = laboratorio.get("hdl", 50)
        if hdl < 30 and not em_estatina and classificacoes.get("LIPIDIO") in ["ELEVADA", "MUITO_ELEVADA"]:
            resultado.sugestoes.append(
                f"HDL {hdl} muito baixo com dislipidemia e sem estatina - "
                "considerar iniciar terapia"
            )

        # Flag 4: Diabetes mal controlado mas sem insulina
        em_insulina = any("insulina" in m.lower() for m in medicamentos_ativos)
        hba1c = laboratorio.get("hba1c", 6)
        if hba1c > 9 and not em_insulina and classificacoes.get("DIABETES") == "CRITICO":
            resultado.sugestoes.append(
                f"HbA1c {hba1c} crítica mas sem insulina - "
                "julgar escalação para terapia intensiva"
            )
            score -= 10

        # Flag 5: IC severa mas sem IECA/ARA2
        iecaras = [
            m for m in medicamentos_ativos
            if any(x in m.lower() for x in ["enalapril", "losartan", "valsartan"])
        ]
        if classificacoes.get("IC") == "SEVERA" and len(iecaras) == 0:
            resultado.sugestoes.append(
                "IC severa sem IECA/ARA2 - verificar contr-indicações"
            )
            score -= 15

        resultado.score_coerencia = max(0, score)
        return resultado

    # ========================================================================
    # 4. VALIDAÇÃO INTEGRADA
    # ========================================================================

    @staticmethod
    def validar_paciente_completo(
        dados_vitais: Dict[str, float],
        laboratorio: Dict[str, float],
        classificacoes: Dict[str, str],
        medicamentos_ativos: List[str],
        idade_anos: int
    ) -> ValidacaoResult:
        """
        Validation integrada de todos os parâmetros do paciente
        
        Combina:
        1. Detecção de impossibilidades
        2. Validação de coerência PA
        3. Validação de hemograma (se disponível)
        4. Validação de lipídios (se disponível)
        5. Detecção de inconsistências clínicas
        
        Args:
            dados_vitais: PA, FC, temp, SpO2
            laboratorio: Glicemia, creatinina, lipídios, hemograma
            classificacoes: HAS, DRC, DIABETES, etc
            medicamentos_ativos: Lista de medicamentos
            idade_anos: Idade do paciente
            
        Returns:
            ValidacaoResult unificado
        """
        resultado_final = ValidacaoResult(valido=True)
        scores = []

        # 1. Detecção de impossibilidades
        todos_parametros = {**dados_vitais, **laboratorio, "idade_anos": idade_anos}
        r1 = ValidadoresClinicosService.detectar_impossibilidades(todos_parametros)
        resultado_final.erros.extend(r1.erros)
        resultado_final.avisos.extend(r1.avisos)
        scores.append(r1.score_coerencia)
        if not r1.valido:
            resultado_final.valido = False

        # 2. Validação PA
        if "pressao_sistolica" in dados_vitais and "pressao_diastolica" in dados_vitais:
            r2 = ValidadoresClinicosService.validar_pressao_arterial(
                dados_vitais["pressao_sistolica"],
                dados_vitais["pressao_diastolica"],
                idade_anos
            )
            resultado_final.avisos.extend(r2.avisos)
            resultado_final.sugestoes.extend(r2.sugestoes)
            scores.append(r2.score_coerencia)

        # 3. Validação hemograma
        hemograma_campos = ["wbc_total", "leucocitos_seg", "linfocitos", "monocitos",
                           "eosinofilos", "basofilos", "hematocrito", "hemoglobina"]
        if any(campo in laboratorio for campo in hemograma_campos):
            r3 = ValidadoresClinicosService.validar_hemograma(
                laboratorio.get("wbc_total", 0),
                laboratorio.get("leucocitos_seg"),
                laboratorio.get("linfocitos"),
                laboratorio.get("monocitos"),
                laboratorio.get("eosinofilos"),
                laboratorio.get("basofilos"),
                laboratorio.get("hematocrito"),
                laboratorio.get("hemoglobina")
            )
            resultado_final.erros.extend(r3.erros)
            resultado_final.avisos.extend(r3.avisos)
            scores.append(r3.score_coerencia)
            if not r3.valido:
                resultado_final.valido = False

        # 4. Validação lipídios
        if "colesterol_total" in laboratorio:
            r4 = ValidadoresClinicosService.validar_lipidios(
                laboratorio["colesterol_total"],
                laboratorio.get("ldl"),
                laboratorio.get("hdl"),
                laboratorio.get("triglicerideos")
            )
            resultado_final.avisos.extend(r4.avisos)
            scores.append(r4.score_coerencia)
            if not r4.valido:
                resultado_final.valido = False

        # 5. Inconsistências clínicas
        r5 = ValidadoresClinicosService.detectar_inconsistencias_clinicas(
            classificacoes,
            medicamentos_ativos,
            laboratorio
        )
        resultado_final.avisos.extend(r5.avisos)
        resultado_final.sugestoes.extend(r5.sugestoes)
        scores.append(r5.score_coerencia)

        # Score final = média dos scores
        resultado_final.score_coerencia = int(sum(scores) / len(scores)) if scores else 100

        return resultado_final
