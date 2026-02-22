"""
Serviço de Classificação - Estadiamento clínico baseado em protocolos internacionais.

Protocolos suportados:
- HAS (Hipertensão): ESC/ESH 2018 e SBC
- DRC (Doença Renal Crônica): KDIGO 2012
- DM2 (Diabetes Mellitus): ADA 2024
"""

import logging
from typing import Dict

logger = logging.getLogger(__name__)


class ClassificacaoService:
    """
    Serviço responsável por estadiar/classificar doenças crônicas
    conforme protocolos internacionais.
    """
    
    @staticmethod
    def classificar_has(pa_sistolica: float, pa_diastolica: float) -> Dict:
        """
        Classifica Hipertensão Arterial Sistêmica (HAS) conforme ESC/ESH 2018 e SBC.
        
        Baseado em:
        - ESC/ESH 2018 Guidelines for hypertension
        - SBC (Sociedade Brasileira de Cardiologia) 2016
        
        Args:
            pa_sistolica: Pressão sistólica (mmHg)
            pa_diastolica: Pressão diastólica (mmHg)
        
        Returns:
            {
                'estagio': 'NORMAL|ELEVADA|ESTAGIO_1|ESTAGIO_2|ESTAGIO_3',
                'categoria_sbc': 'OTIMA|NORMAL|LIMÍTROFE|ESTAGIO_1|ESTAGIO_2|ESTAGIO_3',
                'faixa_sistolica': 'PA < 120' | '120-139' | '140-159' | '160-179' | '>= 180',
                'faixa_diastolica': 'PA < 80' | '80-89' | '90-99' | '100-109' | '>= 110',
                'criterios_met': {
                    'sistolica': True/False,
                    'diastolica': True/False
                }
            }
        """
        
        # Determina estágio conforme ESC/ESH 2018
        if pa_sistolica < 120 and pa_diastolica < 80:
            estagio = 'NORMAL'
            faixa_sys = 'PA < 120'
            faixa_dia = 'PA < 80'
        elif pa_sistolica < 140 and pa_diastolica < 90:
            estagio = 'ELEVADA'
            faixa_sys = '120-139'
            faixa_dia = 'PA < 80'
        elif pa_sistolica < 160 and pa_diastolica < 100:
            estagio = 'ESTAGIO_1'
            faixa_sys = '140-159'
            faixa_dia = '80-99'
        elif pa_sistolica < 180 and pa_diastolica < 110:
            estagio = 'ESTAGIO_2'
            faixa_sys = '160-179'
            faixa_dia = '100-109'
        else:
            estagio = 'ESTAGIO_3'
            faixa_sys = '>= 180'
            faixa_dia = '>= 110'
        
        # Mapeamento para categoria SBC
        categoria_sbc_map = {
            'NORMAL': 'OTIMA',
            'ELEVADA': 'NORMAL',
            'ESTAGIO_1': 'LIMÍTROFE',
            'ESTAGIO_2': 'ESTAGIO_1',
            'ESTAGIO_3': 'ESTAGIO_2',
        }
        
        return {
            'estagio': estagio,
            'categoria_sbc': categoria_sbc_map.get(estagio, 'DESCONHECIDA'),
            'faixa_sistolica': faixa_sys,
            'faixa_diastolica': faixa_dia,
            'criterios_met': {
                'sistolica': pa_sistolica >= 140,
                'diastolica': pa_diastolica >= 90
            },
            'pa_sistolica': pa_sistolica,
            'pa_diastolica': pa_diastolica,
        }
    
    @staticmethod
    def classificar_drc(tfge: float, acr: float = 0) -> Dict:
        """
        Classifica Doença Renal Crônica (DRC) conforme KDIGO 2012.
        
        Baseado em:
        - KDIGO Clinical Practice Guideline for the Evaluation and Management of CKD
        
        Args:
            tfge: Taxa de Filtração Glomerular (eGFR em mL/min/1.73m²)
            acr: Albuminuria-to-Creatinine Ratio (mg/g) - OPCIONAL
        
        Returns:
            {
                'estagio': 'G1|G2|G3a|G3b|G4|G5',
                'descricao': 'Normal to High|Mildly decreased|...',
                'significado_clinico': 'Função renal normal|...',
                'tfge': <valor>,
                'acr': <valor>,
                'albuminuria_categoria': 'A1|A2|A3' (se ACR fornecido)
            }
        """
        
        # Determina estágio G conforme TFGe
        if tfge >= 90:
            estagio_g = 'G1'
            desc = 'Normal to High'
            signif = 'Função renal normal'
        elif tfge >= 60:
            estagio_g = 'G2'
            desc = 'Mildly decreased'
            signif = 'Função renal mildly decreased'
        elif tfge >= 45:
            estagio_g = 'G3a'
            desc = 'Mildly to Moderately decreased'
            signif = 'Função renal mildly to moderately decreased'
        elif tfge >= 30:
            estagio_g = 'G3b'
            desc = 'Moderately to Severely decreased'
            signif = 'Função renal moderately to severely decreased'
        elif tfge >= 15:
            estagio_g = 'G4'
            desc = 'Severely decreased'
            signif = 'Função renal severely decreased'
        else:
            estagio_g = 'G5'
            desc = 'Kidney Failure'
            signif = 'Insuficiência renal terminal'
        
        # Determina categoria albumin ria se ACR fornecido
        albuminuria_categoria = None
        if acr > 0:
            if acr < 30:
                albuminuria_categoria = 'A1'
            elif acr < 300:
                albuminuria_categoria = 'A2'
            else:
                albuminuria_categoria = 'A3'
        
        return {
            'estagio': estagio_g,
            'descricao': desc,
            'significado_clinico': signif,
            'tfge': tfge,
            'acr': acr if acr > 0 else None,
            'albuminuria_categoria': albuminuria_categoria,
        }
    
    @staticmethod
    def classificar_diabetes(hba1c: float = None, glicemia_jejum: float = None, glicemia_acaso: float = None) -> Dict:
        """
        Classifica controle glicêmico em Diabetes conforme ADA 2024.
        
        Baseado em:
        - ADA Standards of Care in Diabetes 2024
        
        Args:
            hba1c: HbA1c (%) - PREFERENCIAL
            glicemia_jejum: Glicemia em jejum (mg/dL) - Fallback se HbA1c não disponível
            glicemia_acaso: Glicemia casual (mg/dL) - Fallback adicional
        
        Returns:
            {
                'controle_glicemico': 'BEM_CONTROLADO|MODERADO|MAL_CONTROLADO|CRITICO',
                'estagio_aida': 'A0|A1|A2|A3',
                'hba1c': <valor>,
                'glicemia_jejum': <valor>,
                'meta_hba1c': '< 7.0' (padrão),
                'status': 'NO_ALVO|ACIMA_ALVO|MUITO_ACIMA_ALVO'
            }
        """
        
        meta_hba1c = 7.0  # Padrão: < 7.0%
        controle = None
        status = None
        
        # Prioridade: HbA1c > glicemia_jejum > glicemia_acaso
        if hba1c is not None:
            if hba1c < 5.7:
                controle = 'BEM_CONTROLADO'
                status = 'NO_ALVO'
            elif hba1c < 7.0:
                controle = 'BEM_CONTROLADO'
                status = 'NO_ALVO'
            elif hba1c < 8.0:
                controle = 'MODERADO'
                status = 'ACIMA_ALVO'
            elif hba1c < 9.0:
                controle = 'MAL_CONTROLADO'
                status = 'MUITO_ACIMA_ALVO'
            else:
                controle = 'CRITICO'
                status = 'MUITO_ACIMA_ALVO'
        
        elif glicemia_jejum is not None:
            # Glicemia de jejum: normal < 100, pré-diabetes 100-125, diabetes >= 126
            if glicemia_jejum < 100:
                controle = 'BEM_CONTROLADO'
                status = 'NO_ALVO'
            elif glicemia_jejum < 126:
                controle = 'MODERADO'
                status = 'ACIMA_ALVO'
            elif glicemia_jejum < 160:
                controle = 'MAL_CONTROLADO'
                status = 'MUITO_ACIMA_ALVO'
            else:
                controle = 'CRITICO'
                status = 'MUITO_ACIMA_ALVO'
        
        elif glicemia_acaso is not None:
            # Glicemia casual: normal < 140, pré-diabetes 140-200, diabetes > 200
            if glicemia_acaso < 140:
                controle = 'BEM_CONTROLADO'
                status = 'NO_ALVO'
            elif glicemia_acaso < 200:
                controle = 'MODERADO'
                status = 'ACIMA_ALVO'
            else:
                controle = 'MAL_CONTROLADO'
                status = 'MUITO_ACIMA_ALVO'
        else:
            return {
                'controle_glicemico': 'DESCONHECIDO',
                'estagio_aida': None,
                'hba1c': None,
                'glicemia_jejum': None,
                'meta_hba1c': f'< {meta_hba1c}%',
                'status': None,
                'acima_meta_hba1c': None,
            }
        
        # Mapa ADA AIDA
        aida_map = {
            'BEM_CONTROLADO': 'A0',
            'MODERADO': 'A1',
            'MAL_CONTROLADO': 'A2',
            'CRITICO': 'A3'
        }
        
        return {
            'controle_glicemico': controle,
            'estagio_aida': aida_map.get(controle, 'A3'),
            'hba1c': hba1c,
            'glicemia_jejum': glicemia_jejum,
            'glicemia_acaso': glicemia_acaso,
            'meta_hba1c': f'< {meta_hba1c}%',
            'status': status,
            'acima_meta_hba1c': hba1c >= meta_hba1c if hba1c else None,
        }
    
    @staticmethod
    def detectar_mudanca_estadiamento(
        estagio_anterior: str,
        estagio_novo: str,
        sistema: str = 'KDIGO'
    ) -> Dict:
        """
        Detecta mudança de estágio entre duas classificações.
        
        Args:
            estagio_anterior: Ex: 'G3a'
            estagio_novo: Ex: 'G3b' ou 'G2'
            sistema: 'KDIGO', 'NYHA', 'SBC', etc
        
        Returns:
            {
                'mudou': True/False,
                'direcao': 'PIORA|MELHORA|ESTAVEL',
                'severidade_mudanca': 'LEVE|MODERADA|GRAVE',
                'requer_atualizacao': True/False
            }
        """
        
        if estagio_anterior == estagio_novo:
            return {
                'mudou': False,
                'direcao': 'ESTAVEL',
                'severidade_mudanca': None,
                'requer_atualizacao': False
            }
        
        # Mapa de progressão KDIGO (simplificado)
        progressao_kdigo = ['G1', 'G2', 'G3a', 'G3b', 'G4', 'G5']
        
        try:
            idx_ant = progressao_kdigo.index(estagio_anterior)
            idx_novo = progressao_kdigo.index(estagio_novo)
            
            if idx_novo > idx_ant:
                direcao = 'PIORA'
                dist = idx_novo - idx_ant
            else:
                direcao = 'MELHORA'
                dist = idx_ant - idx_novo
            
            if dist == 1:
                sev = 'LEVE'
            elif dist == 2:
                sev = 'MODERADA'
            else:
                sev = 'GRAVE'
            
        except ValueError:
            # Estágio desconhecido
            return {
                'mudou': True,
                'direcao': 'DESCONHECIDA',
                'severidade_mudanca': None,
                'requer_atualizacao': True
            }
        
        return {
            'mudou': True,
            'direcao': direcao,
            'severidade_mudanca': sev,
            'requer_atualizacao': True
        }
    
    @staticmethod
    def classificar_lipidios(colesterol_total: float = None,
                            ldl: float = None,
                            hdl: float = None,
                            triglicerideos: float = None) -> Dict:
        """
        Classifica Dislipidemia conforme ATP III / NCEP.
        
        Baseado em:
        - ATP III Classification (National Institutes of Health)
        
        Args:
            colesterol_total: Colesterol total (mg/dL, ideal < 200)
            ldl: LDL colesterol (mg/dL, ideal < 100)
            hdl: HDL colesterol (mg/dL, ideal > 40 homem, > 50 mulher)
            triglicerideos: Triglicerídeos (mg/dL, ideal < 150)
        
        Returns:
            {
                'categoria': 'OTIMA|DESEJAVEL|LIMÍTROFE|ELEVADA|MUITO_ELEVADA',
                'parametros_alterados': [...],
                'risco_cv': 'BAIXO|INTERMÉDIO|ALTO|MUITO_ALTO',
                'colesterol_total': <valor>,
                'ldl': <valor>,
                'hdl': <valor>,
                'triglicerideos': <valor>,
                'razao_colesterol_hdl': <valor>
            }
        """
        
        parametros_alterados = []
        score_risco = 0
        
        # Triglicerídeos
        if triglicerideos:
            if triglicerideos >= 500:
                parametros_alterados.append(f'TG {triglicerideos} (muito alto)')
                score_risco += 3
            elif triglicerideos >= 200:
                parametros_alterados.append(f'TG {triglicerideos} (alto)')
                score_risco += 2
            elif triglicerideos >= 150:
                parametros_alterados.append(f'TG {triglicerideos} (limítrofe)')
                score_risco += 1
        
        # LDL (mais importante)
        if ldl:
            if ldl >= 190:
                parametros_alterados.append(f'LDL {ldl} (muito alto)')
                score_risco += 3
            elif ldl >= 160:
                parametros_alterados.append(f'LDL {ldl} (alto)')
                score_risco += 2
            elif ldl >= 130:
                parametros_alterados.append(f'LDL {ldl} (limítrofe alto)')
                score_risco += 1
        
        # HDL (protetor)
        if hdl:
            if hdl < 40:
                parametros_alterados.append(f'HDL {hdl} (baixo)')
                score_risco += 2
        
        # Colesterol total
        if colesterol_total:
            if colesterol_total >= 240:
                parametros_alterados.append(f'CT {colesterol_total} (elevado)')
                score_risco += 1
            elif colesterol_total >= 200:
                parametros_alterados.append(f'CT {colesterol_total} (limítrofe)')
        
        # Determina categoria
        if not parametros_alterados:
            categoria = 'OTIMA'
            risco = 'BAIXO'
        elif score_risco <= 1:
            categoria = 'DESEJAVEL'
            risco = 'BAIXO'
        elif score_risco <= 2:
            categoria = 'LIMÍTROFE'
            risco = 'INTERMÉDIO'
        elif score_risco <= 4:
            categoria = 'ELEVADA'
            risco = 'ALTO'
        else:
            categoria = 'MUITO_ELEVADA'
            risco = 'MUITO_ALTO'
        
        # Razão CT/HDL
        razao = None
        if colesterol_total and hdl:
            razao = round(colesterol_total / hdl, 2)
        
        return {
            'categoria': categoria,
            'parametros_alterados': parametros_alterados,
            'risco_cv': risco,
            'colesterol_total': colesterol_total,
            'ldl': ldl,
            'hdl': hdl,
            'triglicerideos': triglicerideos,
            'razao_colesterol_hdl': razao,
        }
    
    @staticmethod
    def classificar_insuficiencia_cardiaca(classe_nyha: str = None,
                                          fej: float = None) -> Dict:
        """
        Classifica Insuficiência Cardíaca conforme NYHA (New York Heart Association).
        
        Baseado em:
        - NYHA Functional Classification
        - ACC/AHA Heart Failure Guidelines
        
        Args:
            classe_nyha: Classe I, II, III, IV (ou por extenso)
            fej: Fração de Ejeção (%) - suporte
        
        Returns:
            {
                'estagio_nyha': 'ASSINTOMATICA|LEVE|MODERADA|SEVERA|MUITO_SEVERA',
                'classe_nyha': 'I|II|III|IV',
                'fej_categoria': 'PRESERVADA|INTERMEDIARIA|REDUZIDA',
                'requer_medicacao': True/False,
                'requer_internacao': True/False,
                'descricao': '...'
            }
        """
        
        # Normalizar classe NYHA
        classe_map = {
            'I': 1, '1': 1, 'ASSINTOMATICA': 1,
            'II': 2, '2': 2, 'LEVE': 2,
            'III': 3, '3': 3, 'MODERADA': 3,
            'IV': 4, '4': 4, 'SEVERA': 4,
        }
        
        if not classe_nyha:
            return {
                'estagio_nyha': 'DESCONHECIDO',
                'classe_nyha': None,
                'fej_categoria': None,
                'requer_medicacao': None,
                'requer_internacao': None,
                'descricao': 'Classe NYHA não informada'
            }
        
        classe_str = str(classe_nyha).upper()
        classe_num = classe_map.get(classe_str, None)
        
        if classe_num is None:
            return {
                'estagio_nyha': 'INVALIDO',
                'classe_nyha': None,
                'fej_categoria': None,
                'requer_medicacao': None,
                'requer_internacao': None,
                'descricao': f'Classe NYHA inválida: {classe_nyha}'
            }
        
        # Mapear para estágio
        mapa_estagio = {
            1: 'ASSINTOMATICA',
            2: 'LEVE',
            3: 'MODERADA',
            4: 'SEVERA'
        }
        
        mapa_descricao = {
            1: 'Sem limitação na atividade física',
            2: 'Limitação leve na atividade habitual',
            3: 'Limitação importante na atividade habitual',
            4: 'Sintomas em repouso / desconfortável em qualquer atividade'
        }
        
        # FEJ categoria
        fej_categoria = None
        if fej:
            if fej >= 50:
                fej_categoria = 'PRESERVADA'
            elif fej >= 40:
                fej_categoria = 'INTERMEDIARIA'
            else:
                fej_categoria = 'REDUZIDA'
        
        return {
            'estagio_nyha': mapa_estagio[classe_num],
            'classe_nyha': f'Classe {classe_num}',
            'fej': fej,
            'fej_categoria': fej_categoria,
            'requer_medicacao': classe_num >= 2,
            'requer_internacao': classe_num >= 4,
            'descricao': mapa_descricao[classe_num],
        }
    
    @staticmethod
    def classificar_asma(frequencia_crises_mes: float = None,
                        necessita_resgate: bool = False,
                        limitacao_atividade: bool = False,
                        acordar_noite_semana: int = 0) -> Dict:
        """
        Classifica Asma conforme GINA 2023 (Global Initiative for Asthma).
        
        Baseado em:
        - GINA 2023 Global Strategy for Asthma Management (GINA)
        
        Args:
            frequencia_crises_mes: Número de episódios de asma por mês
            necessita_resgate: Bool - usa broncodilatador resgate > 2x/semana
            limitacao_atividade: Bool - limitação em atividades devida à asma
            acordar_noite_semana: Dias da semana que acorda à noite por asma
        
        Returns:
            {
                'controle_asma': 'CONTROLADO|PARCIALMENTE_CONTROLADO|NAO_CONTROLADO',
                'classificacao_persistencia': 'INTERMITENTE|LEVE|MODERADA|SEVERA',
                'frequencia_crises': <valor>,
                'necessita_controller': True/False,
                'necessita_revisao': True/False,
                'recomendacao': '...'
            }
        """
        
        if frequencia_crises_mes is None:
            return {
                'controle_asma': 'DESCONHECIDO',
                'classificacao_persistencia': None,
                'recomendacao': 'Frequência de crises não informada'
            }
        
        # Classificar persistência
        if frequencia_crises_mes < 1:  # < 1 crise/mês
            persistencia = 'INTERMITENTE'
            score_base = 1
        elif frequencia_crises_mes < 4:  # 1-3 crises/mês
            persistencia = 'LEVE'
            score_base = 2
        elif frequencia_crises_mes < 10:  # 4-9 crises/mês
            persistencia = 'MODERADA'
            score_base = 3
        else:  # >= 10 crises/mês
            persistencia = 'SEVERA'
            score_base = 4
        
        # Fator de controle (sintomas além da frequência)
        score_controle = score_base
        
        if necessita_resgate:
            score_controle = max(score_controle, 2)
        
        if limitacao_atividade:
            score_controle = max(score_controle, 2)
        
        if acordar_noite_semana >= 3:
            score_controle = max(score_controle, 3)
        
        # Determinar controle
        if score_controle <= 1:
            controle = 'CONTROLADO'
            necessita_controller = False
            revisao = False
        elif score_controle <= 2:
            controle = 'PARCIALMENTE_CONTROLADO'
            necessita_controller = True
            revisao = True
        else:
            controle = 'NAO_CONTROLADO'
            necessita_controller = True
            revisao = True
        
        # Recomendação
        if controle == 'CONTROLADO':
            rec = 'Manter terapia atual. Reavaliar em 3-6 meses'
        elif controle == 'PARCIALMENTE_CONTROLADO':
            rec = 'Aumentar dose ou adicionar novo controller. Reavaliar em 2-4 semanas'
        else:
            rec = 'Intensificar terapia / Investigar adesão / Referência especialista'
        
        return {
            'controle_asma': controle,
            'classificacao_persistencia': persistencia,
            'frequencia_crises': frequencia_crises_mes,
            'necessita_resgate': necessita_resgate,
            'limitacao_atividade': limitacao_atividade,
            'acordar_noite_dias_semana': acordar_noite_semana,
            'necessita_controller': necessita_controller,
            'necessita_revisao': revisao,
            'recomendacao': rec,
        }




