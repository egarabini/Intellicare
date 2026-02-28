"""
Serviço de Acompanhamento - Monitoramento de Aderência e Planejamento de Seguimento

Responsável por:
1. Calcular aderência a medicações (%) e comportamento
2. Planejar próximas medições baseado em severidade do alerta
3. Sugerir ajustes de medicação (aumentar/remover/trocar)
4. Detectar padrões (melhora vs piora)
5. Gerar recomendações personalizadas
6. Rastrear cumprimento de recomendações

Flow:
AlertaService (detecta desvio) → AcompanhamentoService (planeja ação)
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from enum import Enum


class FrecuenciaAcompanhamento(str, Enum):
    """Frequência recomendada de acompanhamento"""
    SEMANAL = "SEMANAL"           # Crítico
    QUINZENAL = "QUINZENAL"       # Alto
    MENSAL = "MENSAL"             # Médio
    TRIMESTRAL = "TRIMESTRAL"     # Baixo
    SEMESTRAL = "SEMESTRAL"       # Bem controlado


class TipoAjusteMedicacao(str, Enum):
    """Tipo de ajuste de medicação recomendado"""
    MANTER = "MANTER"             # Sem alteração
    AUMENTAR_DOSE = "AUMENTAR_DOSE"
    DIMINUIR_DOSE = "DIMINUIR_DOSE"
    ADICIONAR_MEDICACAO = "ADICIONAR_MEDICACAO"
    REMOVER_MEDICACAO = "REMOVER_MEDICACAO"
    TROCAR_MEDICACAO = "TROCAR_MEDICACAO"
    EDITAR_HORARIO = "EDITAR_HORARIO"


@dataclass
class MetricaAderencia:
    """Métrica de aderência a tratamento"""
    # Identificação
    medicacao_nome: str            # "Losartan"
    dose_prescrita: str            # "100mg"
    
    # Aderência
    dias_aderentes: int            # Dias tomou medicação corretamente
    dias_totais: int               # Total de dias da prescrição
    percentual_aderencia: float    # 85%
    
    # Temporal
    data_ultima_tomada: Optional[datetime]  # Última vez que tomou
    data_proxima_tomada: datetime          # Próxima dose esperada
    
    # Observações
    motivo_nao_aderencia: Optional[str] = None  # "Esquecimento", "Efeito colateral", etc
    notas: str = ""


@dataclass
class PadraoProgressao:
    """Padrão de evolução da condição"""
    # Identificação
    parametro: str                 # "PA sistólica"
    cid10: str                     # "I10"
    
    # Histórico
    valor_inicial: float           # PA inicial: 220
    valor_atual: float             # PA agora: 180
    valor_objetivo: float          # PA alvo: 140
    
    # Tendência
    dias_acompanhamento: int       # Quantos dias sendo acompanhado
    mudanca_percentual: float      # Mudança % (+20%, -15%, etc)
    tendencia: str                 # "MELHORA", "PIORA", "ESTAVEL"
    prognose: str                  # "Em bom caminho", "Piora acelerada", etc
    
    # Recomendação
    recomendacao_acao: str         # "Manter estratégia", "Aumentar medicação"
    urgencia: str = "ROTINA"       # "ROTINA", "URGENTE"


@dataclass
class AjusteMedicacao:
    """Recomendação de ajuste de medicação"""
    medicacao_nome: str            # "Losartan"
    ajuste_tipo: str               # TipoAjusteMedicacao.value
    dose_atual: str                # "50mg"
    dose_recomendada: Optional[str] = None  # "100mg"
    
    # Contexto
    motivo: str = ""               # "PA sistólica 180 vs obj 140"
    evidencia: List[str] = field(default_factory=list)  # ["SBC 2020", "PA persistentemente alta"]
    
    # Efeitos esperados
    efeito_esperado_parametro: str = ""  # "Redução PA em 20-30 mmHg"
    efeitos_secundarios_potenciais: List[str] = field(default_factory=list)  # ["Tonteira", "Tosse"]
    
    # Monitoramento
    parametros_monitorar: List[str] = field(default_factory=list)  # ["PA", "Creatinina"]
    prazo_avaliacao_dias: int = 30  # Reavalia em 30 dias
    
    # Status
    aceito: bool = False
    data_aceito: Optional[datetime] = None
    motivo_recusa: Optional[str] = None


@dataclass
class PlanoAcompanhamento:
    """Plano de acompanhamento personalizado para paciente"""
    # Identificação
    condicao_cronica_id: int
    cid10: str
    diagnostico: str
    
    # Próximas medições
    proxima_medicao: datetime      # Data da próxima medição
    frequencia_dias: int           # Intervalo até próxima medição
    parametros_medir: List[str] = field(default_factory=list)  # ["PA", "Peso", "Glicemia"]
    
    # Aderência & Padrões
    metricas_aderencia: List[MetricaAderencia] = field(default_factory=list)
    padroes_progressao: List[PadraoProgressao] = field(default_factory=list)
    score_aderencia_geral: float = 0.0  # 0-100%
    
    # Ajustes Recomendados
    ajustes_medicacao: List[AjusteMedicacao] = field(default_factory=list)
    
    # Recomendações Comportamentais
    recomendacoes_comportamento: List[str] = field(default_factory=list)
    # Ex: ["Reduzir ingestão de sódio", "Aumentar atividade física"]
    
    # Educação & Suporte
    topicos_educacao_necessarios: List[str] = field(default_factory=list)
    # Ex: ["Hipertensão: sintomas de alerta", "Técnica correta PA"]
    
    # Status
    status: str = "PLANEJADO"       # PLANEJADO|EM_EXECUÇÃO|CONCLUÍDO
    data_criacao: datetime = field(default_factory=datetime.now)
    data_proxima_revisao: Optional[datetime] = None
    
    # Observações clínicas
    notas_clinico: str = ""


class AcompanhamentoService:
    """Serviço de acompanhamento e monitoramento de aderência"""

    # ========================================================================
    # MÉTODO 1: CALCULAR ADERÊNCIA À MEDICAÇÃO
    # ========================================================================

    @staticmethod
    def calcular_aderencia_medicacao(
        medicacao_nome: str,
        dose_prescrita: str,
        data_prescricao: datetime,
        registros_tomada: List[Dict] = None  # [{"data": date, "tomou": True}, ...]
    ) -> MetricaAderencia:
        """
        Calcula aderência a uma medicação específica.
        
        Args:
            medicacao_nome: "Losartan"
            dose_prescrita: "100mg 1x ao dia"
            data_prescricao: Quando começou a tomar
            registros_tomada: Histórico de se tomou ou não
            
        Returns:
            MetricaAderencia com % aderência
        """
        
        if registros_tomada is None:
            registros_tomada = []
        
        # Calcular dias desde prescrição
        dias_prescricao = (datetime.now() - data_prescricao).days
        if dias_prescricao <= 0:
            dias_prescricao = 1
        
        # Contar dias com aderência
        dias_aderentes = sum(1 for r in registros_tomada if r.get("tomou", False))
        
        percentual = (dias_aderentes / dias_prescricao * 100) if dias_prescricao > 0 else 0
        
        # Detectar motivo de não aderência (heurístico)
        motivo = None
        registros_ordenados = sorted(
            registros_tomada, 
            key=lambda x: x.get("data", datetime.now())
        )
        
        if registros_ordenados:
            # Se houver padrão de não tomar (ex: finais de semana)
            nao_aderentes = [r for r in registros_ordenados if not r.get("tomou", True)]
            if len(nao_aderentes) >= 3:
                motivo = "Falta de adesão recorrente - investigar causa"
        
        # Data última tomada
        ultima_tomada = None
        for r in reversed(registros_ordenados):
            if r.get("tomou", False):
                ultima_tomada = r.get("data")
                break
        
        return MetricaAderencia(
            medicacao_nome=medicacao_nome,
            dose_prescrita=dose_prescrita,
            dias_aderentes=dias_aderentes,
            dias_totais=dias_prescricao,
            percentual_aderencia=percentual,
            data_ultima_tomada=ultima_tomada,
            data_proxima_tomada=datetime.now() + timedelta(days=1),
            motivo_nao_aderencia=motivo
        )

    # ========================================================================
    # MÉTODO 2: PLANEJAR FREQUÊNCIA DE ACOMPANHAMENTO
    # ========================================================================

    @staticmethod
    def planejar_frequencia_acompanhamento(
        nivel_alerta: str,           # "CRÍTICO", "ALTO", "MÉDIO", "BAIXO"
        dias_sem_progresso: Optional[int] = None,
        tendencia: Optional[str] = None,  # "PIORA", "ESTAVEL", "MELHORA"
        score_controle: int = 75     # Score 0-100
    ) -> FrecuenciaAcompanhamento:
        """
        Recomenda frequência de acompanhamento baseado em severidade.
        
        Args:
            nivel_alerta: Nível do alerta (de AlertaService)
            dias_sem_progresso: Se hovver NENHUM_PROGRESSO por N dias
            tendencia: Tendência da condição
            score_controle: Score de controle (0-100)
            
        Returns:
            FrecuenciaAcompanhamento recomendada
        """
        
        # CRÍTICO → Semanal (máxima frequência)
        if nivel_alerta == "CRITICO":
            return FrecuenciaAcompanhamento.SEMANAL
        
        # ALTO → Quinzenal
        if nivel_alerta == "ALTO":
            return FrecuenciaAcompanhamento.QUINZENAL
        
        # MÉDIO com PIORA → Quinzenal
        if nivel_alerta == "MEDIO" and tendencia == "PIORA":
            return FrecuenciaAcompanhamento.QUINZENAL
        
        # MÉDIO estável/melhora → Mensal
        if nivel_alerta == "MEDIO":
            return FrecuenciaAcompanhamento.MENSAL
        
        # BAIXO com MELHORA → Trimestral
        if nivel_alerta == "BAIXO" and tendencia == "MELHORA":
            return FrecuenciaAcompanhamento.TRIMESTRAL
        
        # BAIXO estável → Trimestral a Semestral
        if nivel_alerta == "BAIXO" and score_controle >= 80:
            return FrecuenciaAcompanhamento.SEMESTRAL
        
        return FrecuenciaAcompanhamento.TRIMESTRAL

    # ========================================================================
    # MÉTODO 3: ANALISAR PADRÃO DE PROGRESSÃO
    # ========================================================================

    @staticmethod
    def analisar_padrao_progressao(
        parametro: str,              # "PA sistólica"
        cid10: str,                  # "I10"
        valor_inicial: float,        # 220
        valor_atual: float,          # 180
        valor_objetivo: float,       # 140
        dias_acompanhamento: int,    # 30 dias
        historico: List[Dict] = None # [{"data": date, "valor": 200}, ...]
    ) -> PadraoProgressao:
        """
        Analisa padrão de progressão e faz prognóstico.
        
        Args:
            historico: [{"data": datetime, "valor": 220}, ...]
            
        Returns:
            PadraoProgressao com tendência e prognose
        """
        
        if historico is None:
            historico = []
        
        # Calcular mudança percentual
        if valor_inicial != 0:
            mudanca_percent = ((valor_atual - valor_inicial) / abs(valor_inicial)) * 100
        else:
            mudanca_percent = 0
        
        # Determinar tendência
        tendencia = "ESTAVEL"
        if historico and len(historico) >= 3:
            valores = sorted(historico, key=lambda x: x.get("data", datetime.now()))
            if len(valores) >= 3:
                v1 = valores[-3].get("valor", valor_inicial)
                v2 = valores[-2].get("valor", valor_atual)
                v3 = valores[-1].get("valor", valor_atual)
                
                if v3 > v2 > v1:
                    tendencia = "PIORA"
                elif v3 < v2 < v1:
                    tendencia = "MELHORA"
        
        # Prognose (heurística)
        prognose = "Sem dados suficientes"
        if tendencia == "MELHORA":
            if valor_atual <= valor_objetivo:
                prognose = "Excelente - Objetivo atingido!"
            else:
                dias_restantes = dias_acompanhamento + 30  # Projeção
                prognose = f"Muito bom - Deve atingir objetivo em ~{dias_restantes} dias"
        elif tendencia == "PIORA":
            prognose = "Alerta - Condição piorando, aumentar medicação urgentemente"
        else:
            prognose = "Estável - Manter estratégia ou pequenos ajustes"
        
        # Recomendação de ação
        acao = "Manter estratégia"
        if tendencia == "PIORA":
            acao = "Aumentar medicação ou investigar aderência"
        elif tendencia == "MELHORA" and valor_atual > valor_objetivo:
            acao = "Manter dose atual, acompanhar"
        
        return PadraoProgressao(
            parametro=parametro,
            cid10=cid10,
            valor_inicial=valor_inicial,
            valor_atual=valor_atual,
            valor_objetivo=valor_objetivo,
            dias_acompanhamento=dias_acompanhamento,
            mudanca_percentual=mudanca_percent,
            tendencia=tendencia,
            prognose=prognose,
            recomendacao_acao=acao,
            urgencia="URGENTE" if tendencia == "PIORA" else "ROTINA"
        )

    # ========================================================================
    # MÉTODO 4: SUGERIR AJUSTES DE MEDICAÇÃO
    # ========================================================================

    @staticmethod
    def sugerir_ajuste_medicacao(
        medicacao_nome: str,
        dose_atual: str,
        parametro_atual: float,
        parametro_objetivo: float,
        parametro_tipo: str,         # "PA sistólica", "Glicemia", etc
        cid10: str = "",
        nivel_alerta: str = "MEDIO"
    ) -> AjusteMedicacao:
        """
        Sugere ajuste de medicação baseado em parâmetro vs objetivo.
        
        Args:
            medicacao_nome: "Losartan"
            dose_atual: "50mg"
            parametro_atual: 180 (PA sistólica)
            parametro_objetivo: 140
            parametro_tipo: "PA sistólica"
            
        Returns:
            AjusteMedicacao com recomendação
        """
        
        # Calcular desvio
        desvio = parametro_atual - parametro_objetivo
        desvio_percent = (desvio / abs(parametro_objetivo) * 100) if parametro_objetivo != 0 else 0
        
        # Determinar tipo de ajuste
        ajuste_tipo = TipoAjusteMedicacao.MANTER
        dose_recomendada = None
        motivo = ""
        efeito_esperado = ""
        
        # AUMENTAR: Parâmetro >= objetivo
        if desvio_percent > 15:
            ajuste_tipo = TipoAjusteMedicacao.AUMENTAR_DOSE
            motivo = f"{parametro_tipo} = {parametro_atual} vs objetivo {parametro_objetivo} (desvio +{desvio_percent:.1f}%)"
            
            # Sugerir novo dose (heurístico: aumentar em 50%)
            if "mg" in dose_atual:
                try:
                    dose_num = int(dose_atual.split("mg")[0])
                    nova_dose = int(dose_num * 1.5)
                    dose_recomendada = f"{nova_dose}mg"
                    efeito_esperado = f"Redução {parametro_tipo} de ~{desvio_percent * 0.5:.0f}%"
                except:
                    pass
        
        # DIMINUIR: Parâmetro muito abaixo (hipotensão em PA, hipoglicemia, etc)
        elif desvio < -20:
            ajuste_tipo = TipoAjusteMedicacao.DIMINUIR_DOSE
            motivo = f"{parametro_tipo} = {parametro_atual} (muito abaixo do objetivo)"
            if "mg" in dose_atual:
                try:
                    dose_num = int(dose_atual.split("mg")[0])
                    nova_dose = max(int(dose_num * 0.75), dose_num // 2)
                    dose_recomendada = f"{nova_dose}mg"
                except:
                    pass
        
        # MANTÉM: Próximo ao objetivo
        else:
            ajuste_tipo = TipoAjusteMedicacao.MANTER
            motivo = f"{parametro_tipo} controlado"
        
        return AjusteMedicacao(
            medicacao_nome=medicacao_nome,
            ajuste_tipo=ajuste_tipo.value,
            dose_atual=dose_atual,
            dose_recomendada=dose_recomendada,
            motivo=motivo,
            efeito_esperado_parametro=efeito_esperado,
            prazo_avaliacao_dias=30
        )

    # ========================================================================
    # MÉTODO 5: GERAR PLANO ACOMPANHAMENTO COMPLETO
    # ========================================================================

    @staticmethod
    def gerar_plano_acompanhamento(
        condicao_cronica_id: int,
        cid10: str,
        diagnostico: str,
        nivel_alerta: str,
        score_controle: int,
        parametro_principal: str,    # "PA sistólica"
        valor_atual: float,
        valor_objetivo: float,
        medicacoes_atuais: List[str] = None,
        aderencia_medicacao: float = 85.0
    ) -> PlanoAcompanhamento:
        """
        Gera plano de acompanhamento completo para paciente.
        
        Args:
            Todos os parâmetros necessários
            
        Returns:
            PlanoAcompanhamento pronto para implementação
        """
        
        if medicacoes_atuais is None:
            medicacoes_atuais = []
        
        # 1. Planejar frequência
        frequencia = AcompanhamentoService.planejar_frequencia_acompanhamento(
            nivel_alerta=nivel_alerta,
            score_controle=score_controle
        )
        
        # Converter frequência para dias
        freq_dias = {
            FrecuenciaAcompanhamento.SEMANAL.value: 7,
            FrecuenciaAcompanhamento.QUINZENAL.value: 15,
            FrecuenciaAcompanhamento.MENSAL.value: 30,
            FrecuenciaAcompanhamento.TRIMESTRAL.value: 90,
            FrecuenciaAcompanhamento.SEMESTRAL.value: 180,
        }
        
        dias_frequencia = freq_dias.get(frequencia.value, 30)
        
        # 2. Próxima medição
        proxima_medicao = datetime.now() + timedelta(days=dias_frequencia)
        
        # 3. Sugerir ajuste
        ajustes = []
        for med in medicacoes_atuais[:1]:  # Focar na principal por agora
            ajuste = AcompanhamentoService.sugerir_ajuste_medicacao(
                medicacao_nome=med,
                dose_atual="100mg",  # Simplificado
                parametro_atual=valor_atual,
                parametro_objetivo=valor_objetivo,
                parametro_tipo=parametro_principal,
                cid10=cid10,
                nivel_alerta=nivel_alerta
            )
            ajustes.append(ajuste)
        
        # 4. Parâmetros a medir
        parametros_medir = [parametro_principal]
        if "PA" in parametro_principal:
            parametros_medir = ["PA sistólica", "PA diastólica"]
        
        # 5. Recomendações comportamentais
        recomendacoes = []
        if cid10 == "I10":  # HAS
            recomendacoes = [
                "Reduzir ingestão de sódio (<5g/dia)",
                "Aumentar atividade física (150min/semana)",
                "Manter peso saudável",
                "Evitar bebidas alcoólicas"
            ]
        elif cid10 == "E11":  # DM
            recomendacoes = [
                "Manter rotina de refeições",
                "Evitar açúcares simples",
                "Atividade física regular",
                "Monitorar glicemia conforme prescrição"
            ]
        
        # 6. Tópicos educação
        topicos_educacao = []
        if nivel_alerta in ["ALTO", "CRITICO"]:
            topicos_educacao = [
                f"Sintomas de alerta da {diagnostico}",
                "Quando procurar emergência",
                "Técnica correta de medição"
            ]
        
        return PlanoAcompanhamento(
            condicao_cronica_id=condicao_cronica_id,
            cid10=cid10,
            diagnostico=diagnostico,
            proxima_medicao=proxima_medicao,
            frequencia_dias=dias_frequencia,
            parametros_medir=parametros_medir,
            ajustes_medicacao=ajustes,
            recomendacoes_comportamento=recomendacoes,
            topicos_educacao_necessarios=topicos_educacao,
            score_aderencia_geral=aderencia_medicacao
        )

    # ========================================================================
    # MÉTODO 6: CALCULAR SCORE ADERÊNCIA GERAL
    # ========================================================================

    @staticmethod
    def calcular_score_aderencia_geral(
        metricas_aderencia: List[MetricaAderencia],
        comparecimento_consultas: int = 0,  # Consultas que compareceu
        consultas_agendadas: int = 1  # Total agendadas
    ) -> float:
        """
        Calcula score agregado de aderência (0-100).
        
        Args:
            metricas_aderencia: Lista de aderência por medicação
            comparecimento_consultas: Quantas consultas foram
            consultas_agendadas: Total agendadas
            
        Returns:
            Score 0-100
        """
        
        if not metricas_aderencia:
            return 0.0
        
        # Média de aderência medicações
        aderencia_med = sum(m.percentual_aderencia for m in metricas_aderencia) / len(metricas_aderencia)
        
        # Aderência consultas
        aderencia_consultas = (comparecimento_consultas / consultas_agendadas * 100) if consultas_agendadas > 0 else 100
        
        # Score final (70% medicação, 30% consultas)
        score = (aderencia_med * 0.7) + (aderencia_consultas * 0.3)
        
        return min(100, max(0, score))

