"""
DiagnosticoService - Sugestão Automática de Diagnósticos

Pattern matching engine que interpreta resultados dos 6 classificadores
e sugere diagnósticos com score de confiança e recomendações.

Protocolos:
- CID-10 (Classificação Internacional de Doenças)
- Regras clínicas baseadas em guidelines (SBC, KDIGO, ADA, etc)
- Scoring 0-100 com nível de confiança
"""

from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class SuggestaoClinica:
    """Resposta de sugestão de diagnóstico."""
    cid10: str
    nome_condicao: str
    score: int  # 0-100
    nivel_confianca: int  # 0-100
    evidencias: List[str]  # Parâmetros que levaram à sugestão
    recomendacoes: List[str]  # Ações clínicas sugeridas
    urgencia: str  # ELETIVA, ROTINA, URGENTE, EMERGENCIA


class DiagnosticoService:
    """
    Engine de diagnóstico automático baseado em classificadores clínicos.
    
    Padrões reconhecidos:
    1. HAS está em estágio 2-3 → diagnóstico/reclassificação
    2. DRC em G4-G5 + proteinúria → encaminhar nefrologia
    3. Diabetes MAL_CONTROLADO + DRC → aumentar frequência consultas
    4. Dislipidemia + HAS + Diabetes → alto risco cardiovascular
    5. IC SEVERA + Diabetes → avaliar função renal
    """
    
    @staticmethod
    def sugerir_diagnosticos(
        sistema: str,
        estagio: str,
        score: Optional[int] = None,
        parametros: Optional[Dict] = None
    ) -> List[SuggestaoClinica]:
        """
        Sugere diagnósticos baseado em classificação e parâmetros.
        
        Args:
            sistema: 'HAS' | 'DRC' | 'DIABETES' | 'LIPIDIO' | 'IC' | 'ASMA'
            estagio: Estágio da classificação (ex: 'ESTAGIO_2', 'G3b', 'MAL_CONTROLADO')
            score: Score numérico opcional
            parametros: Parâmetros adicionais para contexto
        
        Returns:
            Lista de sugestões ordenadas por score
        """
        
        sugestoes = []
        
        # ====================================================================
        # PADRÕES HAS
        # ====================================================================
        if sistema == 'HAS':
            if estagio == 'NORMAL':
                sugestoes.append(SuggestaoClinica(
                    cid10='R03.0',  # PA normal
                    nome_condicao='Sem Hipertensão Arterial',
                    score=0,
                    nivel_confianca=98,
                    evidencias=['PA < 120/80 mmHg'],
                    recomendacoes=['Manter estilo de vida saudável', 'Avaliar anualmente'],
                    urgencia='ELETIVA'
                ))
            
            elif estagio == 'ELEVADA':
                sugestoes.append(SuggestaoClinica(
                    cid10='R03.0',
                    nome_condicao='PA Elevada - Pré-HAS',
                    score=30,
                    nivel_confianca=92,
                    evidencias=['PA 130-139 sistólica'],
                    recomendacoes=['Mudanças estilo de vida', 'Reavaliação em 3 meses'],
                    urgencia='ROTINA'
                ))
            
            elif estagio in ['ESTAGIO_1', 'ESTAGIO_2']:
                sugestoes.append(SuggestaoClinica(
                    cid10='I10',
                    nome_condicao='Hipertensão Arterial Essencial',
                    score=85 if estagio == 'ESTAGIO_2' else 75,
                    nivel_confianca=95,
                    evidencias=[f'PA em {estagio}'],
                    recomendacoes=[
                        'Iniciar farmacoterapia conforme protocolo SBC',
                        'Monitorar PA domiciliar',
                        'Avaliar órgãos-alvo'
                    ],
                    urgencia='ROTINA' if estagio == 'ESTAGIO_1' else 'URGENTE'
                ))
            
            elif estagio == 'ESTAGIO_3':
                sugestoes.extend([
                    SuggestaoClinica(
                        cid10='I10',
                        nome_condicao='Hipertensão Arterial com Lesão de Órgão-alvo',
                        score=95,
                        nivel_confianca=98,
                        evidencias=['PA ≥ 180/110 mmHg', 'Estágio 3 SBC'],
                        recomendacoes=[
                            'Emergência hipertensiva - avaliar rápido',
                            'ECG obrigatório',
                            'Avaliar insuficiência cardíaca',
                            'Considerar IC intensivo'
                        ],
                        urgencia='EMERGENCIA'
                    ),
                    SuggestaoClinica(
                        cid10='I11',
                        nome_condicao='Considerar HAS Secundária',
                        score=40,
                        nivel_confianca=50,
                        evidencias=['HAS refratária estágio 3'],
                        recomendacoes=['Investigar causa secundária'],
                        urgencia='URGENTE'
                    )
                ])
        
        # ====================================================================
        # PADRÕES DRC
        # ====================================================================
        elif sistema == 'DRC':
            stages_map = {
                'G1': {'nome': 'Normal', 'score': 0, 'urgencia': 'ROTINA'},
                'G2': {'nome': 'Levemente diminuída', 'score': 20, 'urgencia': 'ROTINA'},
                'G3a': {'nome': 'Leve-moderada', 'score': 40, 'urgencia': 'ROTINA'},
                'G3b': {'nome': 'Moderada-severa', 'score': 60, 'urgencia': 'URGENTE'},
                'G4': {'nome': 'Severamente diminuída', 'score': 80, 'urgencia': 'URGENTE'},
                'G5': {'nome': 'Falência renal', 'score': 95, 'urgencia': 'EMERGENCIA'},
            }
            
            stage_info = stages_map.get(estagio, {})
            
            sugestoes.append(SuggestaoClinica(
                cid10='N18' if estagio in ['G1', 'G2'] else 'N18.3' if estagio == 'G3a' else 'N18.4' if estagio == 'G4' else 'N18.5',
                nome_condicao=f"Doença Renal Crônica - {stage_info.get('nome', estagio)}",
                score=stage_info.get('score', 50),
                nivel_confianca=94,
                evidencias=[f'KDIGO {estagio}'],
                recomendacoes=DiagnosticoService._recomendacoes_drc(estagio, parametros),
                urgencia=stage_info.get('urgencia', 'ROTINA')
            ))
        
        # ====================================================================
        # PADRÕES DIABETES
        # ====================================================================
        elif sistema == 'DIABETES':
            control_map = {
                'BEM_CONTROLADO': {'score': 15, 'urgencia': 'ROTINA'},
                'MODERADO': {'score': 40, 'urgencia': 'ROTINA'},
                'MAL_CONTROLADO': {'score': 70, 'urgencia': 'URGENTE'},
                'CRITICO': {'score': 95, 'urgencia': 'EMERGENCIA'},
            }
            
            control_info = control_map.get(estagio, {})
            
            sugestoes.append(SuggestaoClinica(
                cid10='E11',
                nome_condicao=f"Diabetes Mellitus Tipo 2 - {estagio}",
                score=control_info.get('score', 50),
                nivel_confianca=92 if 'CONTROLADO' in estagio else 85,
                evidencias=[f'Controle glicêmico: {estagio}'],
                recomendacoes=DiagnosticoService._recomendacoes_diabetes(estagio),
                urgencia=control_info.get('urgencia', 'ROTINA')
            ))
        
        # ====================================================================
        # PADRÕES DISLIPIDEMIA
        # ====================================================================
        elif sistema == 'LIPIDIO':
            category_map = {
                'OTIMA': {'score': 5, 'urgencia': 'ELETIVA'},
                'DESEJAVEL': {'score': 15, 'urgencia': 'ROTINA'},
                'LIMÍTROFE': {'score': 40, 'urgencia': 'ROTINA'},
                'ELEVADA': {'score': 65, 'urgencia': 'URGENTE'},
                'MUITO_ELEVADA': {'score': 85, 'urgencia': 'URGENTE'},
            }
            
            cat_info = category_map.get(estagio, {})
            
            sugestoes.append(SuggestaoClinica(
                cid10='E78.5' if 'ELEVADA' in estagio else 'E78',
                nome_condicao=f"Dislipidemia - {estagio}",
                score=cat_info.get('score', 50),
                nivel_confianca=88,
                evidencias=[f'Classificação ATP III: {estagio}'],
                recomendacoes=DiagnosticoService._recomendacoes_lipidios(estagio),
                urgencia=cat_info.get('urgencia', 'ROTINA')
            ))
        
        # ====================================================================
        # PADRÕES IC
        # ====================================================================
        elif sistema == 'IC':
            nyha_map = {
                'ASSINTOMATICA': {'score': 10, 'urgencia': 'ROTINA'},
                'LEVE': {'score': 35, 'urgencia': 'ROTINA'},
                'MODERADA': {'score': 60, 'urgencia': 'URGENTE'},
                'SEVERA': {'score': 90, 'urgencia': 'EMERGENCIA'},
            }
            
            nyha_info = nyha_map.get(estagio, {})
            
            sugestoes.append(SuggestaoClinica(
                cid10='I50',
                nome_condicao=f"Insuficiência Cardíaca - {estagio}",
                score=nyha_info.get('score', 50),
                nivel_confianca=91,
                evidencias=[f'NYHA: {estagio}'],
                recomendacoes=DiagnosticoService._recomendacoes_ic(estagio),
                urgencia=nyha_info.get('urgencia', 'ROTINA')
            ))
        
        # ====================================================================
        # PADRÕES ASMA
        # ====================================================================
        elif sistema == 'ASMA':
            asma_map = {
                'INTERMITENTE': {'score': 20, 'urgencia': 'ROTINA'},
                'LEVE': {'score': 40, 'urgencia': 'ROTINA'},
                'MODERADA': {'score': 65, 'urgencia': 'URGENTE'},
                'SEVERA': {'score': 90, 'urgencia': 'EMERGENCIA'},
            }
            
            asma_info = asma_map.get(estagio, {})
            
            sugestoes.append(SuggestaoClinica(
                cid10='J45',
                nome_condicao=f"Asma - {estagio}",
                score=asma_info.get('score', 50),
                nivel_confianca=89,
                evidencias=[f'Controlabilidade: {estagio}'],
                recomendacoes=DiagnosticoService._recomendacoes_asma(estagio),
                urgencia=asma_info.get('urgencia', 'ROTINA')
            ))
        
        return sorted(sugestoes, key=lambda x: x.score, reverse=True)

    @staticmethod
    def analisar_multimorbidade(
        classificacoes: Dict[str, Dict]
    ) -> Dict:
        """
        Analisa combinações de condições para risco aumentado.
        
        Args:
            classificacoes: Dict com resultados de todos os classificadores
            {
                'has': {'estagio': 'ESTAGIO_2'},
                'drc': {'estagio': 'G3b'},
                'diabetes': {'controle_glicemico': 'MAL_CONTROLADO'},
                'lipidios': {'categoria': 'ELEVADA'}
            }
        
        Returns:
            {
                'risco_cv': 'BAIXO|INTERMÉDIO|ALTO|MUITO_ALTO',
                'urgencia_maxima': 'ELETIVA|ROTINA|URGENTE|EMERGENCIA',
                'padroes_detectados': [...],
                'encaminhamentos_recomendados': [...]
            }
        """
        
        padroes = []
        score_risco_cv = 0
        urgencia_maxima = 'ELETIVA'
        encaminhamentos = []
        
        # ====================================================================
        # PADRÃO 1: HAS + DRC (Alto Risco)
        # ====================================================================
        has = classificacoes.get('has', {})
        drc = classificacoes.get('drc', {})
        
        if has.get('estagio') in ['ESTAGIO_2', 'ESTAGIO_3'] and drc.get('estagio') in ['G3b', 'G4', 'G5']:
            padroes.append('HAS Stage 2-3 + DRC Stage 3b-5: Alto risco')
            score_risco_cv += 40
            encaminhamentos.append('Cardiologia (HAS refratária)')
            encaminhamentos.append('Nefrologia (CKD progressiva)')
            urgencia_maxima = 'URGENTE'
        
        # ====================================================================
        # PADRÃO 2: Diabetes + DRC (Progressão Diabética)
        # ====================================================================
        diabetes = classificacoes.get('diabetes', {})
        
        if diabetes.get('controle_glicemico') in ['MAL_CONTROLADO', 'CRITICO'] and \
           drc.get('estagio') in ['G3b', 'G4', 'G5']:
            padroes.append('Diabetes mal controlado + DRC avançada: Síndrome metabólica')
            score_risco_cv += 35
            encaminhamentos.append('Endocrinologia (Otimizar glicemia)')
            encaminhamentos.append('Nefrologia (Proteção renal)')
            urgencia_maxima = 'URGENTE'
        
        # ====================================================================
        # PADRÃO 3: Dislipidemia + HAS + Diabetes (Síndrome Cardiometabólica)
        # ====================================================================
        lipidios = classificacoes.get('lipidios', {})
        
        if lipidios.get('categoria') in ['ELEVADA', 'MUITO_ELEVADA'] and \
           has.get('estagio') in ['ESTAGIO_1', 'ESTAGIO_2', 'ESTAGIO_3'] and \
           diabetes.get('controle_glicemico') in ['MODERADO', 'MAL_CONTROLADO', 'CRITICO']:
            padroes.append('Síndrome Cardiometabólica: DLP + HAS + Diabetes')
            score_risco_cv += 45  # Muito alto risco CV
            encaminhamentos.append('Cardiologia (Avaliação CV)')
            encaminhamentos.append('Clínica geral (Intensificar prevenção)')
            urgencia_maxima = 'URGENTE'
        
        # ====================================================================
        # PADRÃO 4: IC + Diabetes (Compatibilidade Farmacológica)
        # ====================================================================
        ic = classificacoes.get('ic', {})
        
        if ic.get('estagio_nyha') in ['MODERADA', 'SEVERA'] and \
           diabetes.get('controle_glicemico') in ['MAL_CONTROLADO', 'CRITICO']:
            padroes.append('IC + Diabetes descompensado: Risco de descompensação')
            score_risco_cv += 30
            encaminhamentos.append('Cardiologia (Ajuste medicamentos)')
            if ic.get('estagio_nyha') == 'SEVERA':
                urgencia_maxima = 'EMERGENCIA'
        
        # ====================================================================
        # PADRÃO 5: DRC G5 (Necessita Dializador ou Transplante)
        # ====================================================================
        if drc.get('estagio') == 'G5':
            padroes.append('DRC G5: Provável necessidade de substituição renal')
            score_risco_cv = 100
            encaminhamentos.append('Nefrologia urgente')
            urgencia_maxima = 'EMERGENCIA'
        
        # ====================================================================
        # PADRÃO 6: Asma SEVERA (Pode descompensarem minutos)
        # ====================================================================
        asma = classificacoes.get('asma', {})
        
        if asma.get('persistencia') == 'SEVERA':
            padroes.append('Asma severa persistente: Risco de crise')
            score_risco_cv += 25
            encaminhamentos.append('Pneumologia (Otimizar controle)')
            urgencia_maxima = 'URGENTE'
        
        # ====================================================================
        # Classificar Risco Cardiovascular Geral
        # ====================================================================
        if score_risco_cv >= 80:
            risco_cv = 'MUITO_ALTO'
        elif score_risco_cv >= 60:
            risco_cv = 'ALTO'
        elif score_risco_cv >= 30:
            risco_cv = 'INTERMÉDIO'
        else:
            risco_cv = 'BAIXO'
        
        return {
            'risco_cv': risco_cv,
            'score_risco': score_risco_cv,
            'urgencia_maxima': urgencia_maxima,
            'padroes_detectados': padroes,
            'encaminhamentos_recomendados': list(set(encaminhamentos)),  # Remove duplicatas
            'necessita_internacao': urgencia_maxima == 'EMERGENCIA',
            'necessita_icu': urgencia_maxima == 'EMERGENCIA' and score_risco_cv >= 90
        }

    # ====================================================================
    # RECOMENDAÇÕES ESPECÍFICAS
    # ====================================================================

    @staticmethod
    def _recomendacoes_drc(estagio: str, parametros: Optional[Dict] = None) -> List[str]:
        """Recomendações específicas por estágio DRC."""
        recomendacoes_base = {
            'G1': [
                'Manter estilo de vida saudável',
                'Avaliar anualmente',
                'Controlar fatores de risco'
            ],
            'G2': [
                'Avaliar a cada 1-2 anos',
                'Avaliar órgãos-alvo',
                'Intensificar controle HAS'
            ],
            'G3a': [
                'Avaliar a cada 6-12 meses',
                'Solicitar ecografia renal',
                'Considerar nefrologia'
            ],
            'G3b': [
                'Avaliar a cada 3-4 meses',
                'Referência para nefrologia',
                'Avaliar progressão DRC'
            ],
            'G4': [
                'Avaliar mensal',
                'Orientação pré-renal',
                'Preparar acesso vascular',
                'Anemia (avaliar EPO)'
            ],
            'G5': [
                'Terapia renal substitutiva (diálise/transplante)',
                'Acompanhamento nefrologia intensivo',
                'Cuidados nutricionais específicos'
            ]
        }
        
        return recomendacoes_base.get(estagio, ['Avaliar conforme protocolo KDIGO'])

    @staticmethod
    def _recomendacoes_diabetes(estagio: str) -> List[str]:
        """Recomendações específicas por controle glicêmico."""
        recomendacoes_base = {
            'BEM_CONTROLADO': [
                'Manter regime atual',
                'Avaliar a cada 3 meses',
                'Rastreamento complicações anuais'
            ],
            'MODERADO': [
                'Intensificar educação',
                'Avaliar adesão medicamentosa',
                'Avaliar a cada 1-2 meses'
            ],
            'MAL_CONTROLADO': [
                'Aumentar dose/adicionar medicamento',
                'Avaliar a cada 2-4 semanas',
                'Referência endocrinologia',
                'Rastreamento de complicações'
            ],
            'CRITICO': [
                'Emergência metabólica: avaliar DKA/HHS',
                'Internação hospitalar',
                'Insulina se não em uso',
                'Monitoramento em UTI se necessário'
            ]
        }
        
        return recomendacoes_base.get(estagio, ['Otimizar controle glicêmico'])

    @staticmethod
    def _recomendacoes_lipidios(estagio: str) -> List[str]:
        """Recomendações específicas por nível de risco lipídico."""
        recomendacoes_base = {
            'OTIMA': [
                'Manter estilo de vida',
                'Reavaliação anual'
            ],
            'DESEJAVEL': [
                'Reforçar mudanças estilo de vida',
                'Reavaliação em 6 meses'
            ],
            'LIMÍTROFE': [
                'Mudanças estilo de vida intensas',
                'Considerar estatina conforme risco CV',
                'Avaliar em 3 meses'
            ],
            'ELEVADA': [
                'Iniciar estatina (primeira linha)',
                'Avaliar em 4-12 semanas',
                'Alcance meta LDL < 100'
            ],
            'MUITO_ELEVADA': [
                'Estatina de alta potência',
                'Considerar ezetimiba ou PCSK9',
                'Meta LDL < 70 (alto risco CV)',
                'Avaliar em 2-4 semanas'
            ]
        }
        
        return recomendacoes_base.get(estagio, ['Otimizar perfil lipídico'])

    @staticmethod
    def _recomendacoes_ic(estagio: str) -> List[str]:
        """Recomendações específicas por classe NYHA."""
        recomendacoes_base = {
            'ASSINTOMATICA': [
                'Acompanhamento clínico periódico',
                'Avaliar função ecocardiográfica anualmente',
                'Orientações de estilo de vida'
            ],
            'LEVE': [
                'IECA/ARB obrigatório',
                'Beta-bloqueador conforme tolerância',
                'Avaliação cardiológica a cada 3 meses'
            ],
            'MODERADA': [
                'Dupla terapia: IECA + Beta-bloqueador',
                'Diurético conforme retenção',
                'Avaliação cardiológica mensal'
            ],
            'SEVERA': [
                'Tripla terapia + possível transplante',
                'Consideração de VAD',
                'Hospitalização e monitoramento contínuo',
                'Reabilitação cardíaca'
            ]
        }
        
        return recomendacoes_base.get(estagio, ['Otimizar manejo de IC'])

    @staticmethod
    def _recomendacoes_asma(estagio: str) -> List[str]:
        """Recomendações específicas por controlabilidade asmática."""
        recomendacoes_base = {
            'INTERMITENTE': [
                'Usar beta-2 agonista conforme necessário',
                'Acompanhamento anual',
                'Evitar disparadores'
            ],
            'LEVE': [
                'Corticoide inalado de baixa dose',
                'Beta-2 conforme necessário',
                'Acompanhamento a cada 3-4 meses'
            ],
            'MODERADA': [
                'Corticoide inalado dose média',
                'Adicionar beta-agonista LABA',
                'Acompanhamento mensal',
                'Considerar montelucaste'
            ],
            'SEVERA': [
                'Corticoide inalado alta dose + LABA',
                'Considerar omalizumabe/biológicos',
                'Pneumologia de referência',
                'Plano de crise atualizado'
            ]
        }
        
        return recomendacoes_base.get(estagio, ['Otimizar controle asmático'])
