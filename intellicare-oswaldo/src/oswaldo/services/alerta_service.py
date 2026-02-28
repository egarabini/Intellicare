"""
Serviço de Alertas - Monitoramento e Escalação de Desvios Clínicos

Responsável por:
1. Monitorar desvios vs objetivos do plano
2. Escalar alertas (BAIXO → MÉDIO → ALTO → CRÍTICO)
3. Disparar notificações ao clínico
4. Gerar recomendações de ajuste
5. Rastrear histórico de alertas

Lógica:
- Simples: Objetivo não atingido em prazo → Alerta
- Avançada: Detecta tendência piorando, risco de descompensação
- Urgência: ELETIVA (ajuste rotina) → EMERGÊNCIA (internação)
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from enum import Enum


class NivelAlerta(str, Enum):
    """Nível de severidade do alerta"""
    BAIXO = "BAIXO"
    MEDIO = "MEDIO"
    ALTO = "ALTO"
    CRITICO = "CRITICO"


class TipoAlerta(str, Enum):
    """Tipo/Categoria de alerta"""
    NENHUM_PROGRESSO = "NENHUM_PROGRESSO"           # Objetivo não alterou em 4 semanas
    PIORA_PROGRESSIVA = "PIORA_PROGRESSIVA"         # Tendência piorando
    PARAMETRO_CRITICO = "PARAMETRO_CRITICO"         # Fora do range seguro
    NAO_ADERENCIA = "NAO_ADERENCIA"                 # Não tomando medicação?
    COMPLICACAO_SUSPEITA = "COMPLICACAO_SUSPEITA"   # Sintoma novo/alarmante
    EFEITO_COLATERAL = "EFEITO_COLATERAL"           # Efeito adverso relatado
    INTERACAO_MEDICAMENTO = "INTERACAO_MEDICAMENTO" # Medicações incompatíveis
    DESCOMPENSACAO = "DESCOMPENSACAO"               # Falha terapêutica iminente


class UrgenciaIntervencao(str, Enum):
    """Urgência da intervenção recomendada"""
    ELETIVA = "ELETIVA"           # Ajuste na próxima consulta (~30 dias)
    ROTINA = "ROTINA"             # Próximos 7 dias
    URGENTE = "URGENTE"           # Próximas 24-48 horas
    EMERGENCIA = "EMERGENCIA"      # Imediatamente / Internação


@dataclass
class Recomendacao:
    """Recomendação de ação clínica"""
    titulo: str                    # Ex: "Aumentar Losartan para 100mg"
    descricao: str                 # Detalhamento
    acao: str                      # AUMENTAR_MEDICACAO|ADICIONAR|REMOVER|INVESTIGAR|MONITORAR
    parametro_alvo: Optional[str]  # Ex: "PA sistólica"
    valor_alvo: Optional[float]    # 140
    urgencia: str                  # ELETIVA|ROTINA|URGENTE|EMERGENCIA
    evidencia: List[str] = field(default_factory=list)  # Ex: ["SBC 2020", "Piora PA"]
    conflitos: List[str] = field(default_factory=list)  # Medicações/contra-indicações


@dataclass
class Alerta:
    """Alerta clínico individual"""
    # Identificação
    alerta_id: int
    condicao_cronica_id: int
    cid10: str
    
    # Conteúdo
    tipo: str                      # TipoAlerta enum
    nivel: str                     # NivelAlerta enum
    titulo: str                    # "PA Sistólica Elevada"
    descricao: str                 # "PA 165 mmHg, acima do objetivo <140"
    
    # Métricas
    parametro_monitorado: str      # "PA sistólica"
    valor_observado: float         # 165
    valor_objetivo: float          # 140
    unidade: str                   # "mmHg"
    desvio_percentual: float       # 17.9% (acima)
    
    # Contexto temporal
    data_alerta: datetime = field(default_factory=datetime.now)
    dias_sem_progresso: Optional[int] = None  # Se NENHUM_PROGRESSO
    tendencia: Optional[str] = None            # ESTAVEL|PIORA|MELHORA
    
    # Recomendações
    recomendacoes: List[Recomendacao] = field(default_factory=list)
    
    # Status
    status: str = "ATIVO"          # ATIVO|RESOLVIDO|IGNORADO
    data_resolucao: Optional[datetime] = None
    nota_resolucao: str = ""
    
    # Notificação
    notificado_em: Optional[datetime] = None
    lido_por_clinico: bool = False


@dataclass
class GrupoAlerta:
    """Agrupa alertas relacionados do mesmo paciente"""
    condicao_cronica_id: int
    cid10: str
    diagnostico: str
    
    alertas_criticos: List[Alerta] = field(default_factory=list)
    alertas_altos: List[Alerta] = field(default_factory=list)
    alertas_medios: List[Alerta] = field(default_factory=list)
    alertas_baixos: List[Alerta] = field(default_factory=list)
    
    data_criacao: datetime = field(default_factory=datetime.now)
    urgencia_maxima: str = ""      # NivelAlerta mais grave
    
    @property
    def total_alertas(self) -> int:
        return len(self.alertas_criticos) + len(self.alertas_altos) + \
               len(self.alertas_medios) + len(self.alertas_baixos)
    
    @property
    def requer_acao_imediata(self) -> bool:
        return len(self.alertas_criticos) > 0


class AlertaService:
    """Serviço de monitoramento e escalação de alertas clínicos"""

    # ========================================================================
    # MÉTODOS PRINCIPAIS
    # ========================================================================

    @staticmethod
    def avaliar_progresso_objetivo(
        objetivo_descricao: str,
        parametro: str,
        valor_atual: float,
        valor_objetivo: float,
        unidade: str,
        dados_historicos: List[Dict] = None,
        dias_desde_inicio: int = 0
    ) -> Alerta:
        """
        Avalia se objetivo está sendo atingido.
        
        Args:
            objetivo_descricao: "Reduzir PA sistólica p/ <140"
            parametro: "PA sistólica"
            valor_atual: 155
            valor_objetivo: 140
            unidade: "mmHg"
            dados_historicos: [{"data": date, "valor": 160}, ...]
            dias_desde_inicio: Dias desde início do tratamento
            
        Returns:
            Alerta com nível determinado
        """
        
        # Calcular desvio
        if valor_objetivo == 0:
            desvio_percentual = 0
        else:
            desvio_percentual = ((valor_atual - valor_objetivo) / abs(valor_objetivo)) * 100
        
        # Determinar se acima ou abaixo do objetivo
        acima_objetivo = valor_atual > valor_objetivo
        
        # Analisar tendência (se houver histórico)
        tendencia = "ESTAVEL"
        dias_sem_progresso = None
        
        if dados_historicos and len(dados_historicos) >= 2:
            valores_ordenados = sorted(dados_historicos, key=lambda x: x["data"])
            
            if len(valores_ordenados) >= 3:
                # Últimas 3 medições
                v1 = valores_ordenados[-3]["valor"]
                v2 = valores_ordenados[-2]["valor"]
                v3 = valores_ordenados[-1]["valor"]
                
                if v3 > v2 > v1:
                    tendencia = "PIORA"
                elif v3 < v2 < v1:
                    tendencia = "MELHORA"
                else:
                    tendencia = "ESTAVEL"
            
            # Contar dias sem progresso
            primeira_medicao = valores_ordenados[0]["data"]
            dias_corridos = (datetime.now() - primeira_medicao).days
            
            if dias_corridos >= 28:  # 4 semanas
                if abs(valores_ordenados[-1]["valor"] - valores_ordenados[0]["valor"]) < 5:
                    dias_sem_progresso = dias_corridos
        
        # Determinar nível do alerta
        nivel = AlertaService._determinar_nivel_alerta(
            acima_objetivo=acima_objetivo,
            desvio_percentual=desvio_percentual,
            tendencia=tendencia,
            dias_sem_progresso=dias_sem_progresso,
            dias_desde_inicio=dias_desde_inicio
        )
        
        # Determinar tipo de alerta
        if dias_sem_progresso and dias_sem_progresso >= 28:
            tipo_alerta = TipoAlerta.NENHUM_PROGRESSO
        elif tendencia == "PIORA":
            tipo_alerta = TipoAlerta.PIORA_PROGRESSIVA
        else:
            tipo_alerta = TipoAlerta.PARAMETRO_CRITICO
        
        # Criar alerta
        alerta = Alerta(
            alerta_id=0,  # Será atribuído por BDD
            condicao_cronica_id=0,
            cid10="",
            tipo=tipo_alerta.value,
            nivel=nivel,
            titulo=f"{parametro} não atingiu objetivo",
            descricao=f"{parametro}: {valor_atual} {unidade} (objetivo: {valor_objetivo}, desvio: +{desvio_percentual:.1f}%)" if acima_objetivo else f"{parametro}: {valor_atual} {unidade} (objetivo: >{valor_objetivo})",
            parametro_monitorado=parametro,
            valor_observado=valor_atual,
            valor_objetivo=valor_objetivo,
            unidade=unidade,
            desvio_percentual=abs(desvio_percentual),
            dias_sem_progresso=dias_sem_progresso,
            tendencia=tendencia
        )
        
        return alerta

    @staticmethod
    def _determinar_nivel_alerta(
        acima_objetivo: bool,
        desvio_percentual: float,
        tendencia: str,
        dias_sem_progresso: Optional[int] = None,
        dias_desde_inicio: int = 0
    ) -> str:
        """
        Business logic para determinar severidade.
        
        Regras:
        - CRÍTICO: Fora do range por >20% EM PIORA ou sem progresso >4 semanas
        - ALTO: Fora do range por 10-20% com piora progressiva
        - MÉDIO: Fora do range por 5-10% ou tendência instável
        - BAIXO: Fora do range por <5% ou em melhora mas ainda acima
        """
        
        # CRÍTICO
        if dias_sem_progresso and dias_sem_progresso >= 28:
            return NivelAlerta.CRITICO.value
        
        if desvio_percentual > 20 and tendencia == "PIORA":
            return NivelAlerta.CRITICO.value
        
        # ALTO
        if 10 < desvio_percentual <= 20 and tendencia == "PIORA":
            return NivelAlerta.ALTO.value
        
        if desvio_percentual > 20:
            return NivelAlerta.ALTO.value
        
        # MÉDIO
        if 5 < desvio_percentual <= 10:
            return NivelAlerta.MEDIO.value
        
        if tendencia == "PIORA" and 3 < desvio_percentual <= 10:
            return NivelAlerta.MEDIO.value
        
        # BAIXO
        if desvio_percentual > 0 and desvio_percentual <= 5:
            return NivelAlerta.BAIXO.value
        
        if tendencia == "MELHORA" and desvio_percentual <= 10:
            return NivelAlerta.BAIXO.value
        
        return NivelAlerta.BAIXO.value

    @staticmethod
    def gerar_recomendacoes(
        tipo_alerta: str,
        cid10: str,
        nivel_alerta: str,
        parametro: str,
        valor_atual: float,
        valor_objetivo: float
    ) -> List[Recomendacao]:
        """
        Gera recomendações baseado no tipo e nível de alerta.
        
        Args:
            tipo_alerta: TipoAlerta enum value
            cid10: Para contexto (I10=HAS, E11=DM, etc)
            nivel_alerta: NivelAlerta enum value
            parametro: "PA sistólica", "HbA1c", etc
            valor_atual: Valor observado
            valor_objetivo: Meta clínica
            
        Returns:
            Lista de recomendações estruturadas
        """
        
        recomendacoes = []
        
        # HAS (I10)
        if cid10.startswith("I10"):
            if parametro == "PA sistólica" and valor_atual > valor_objetivo:
                if nivel_alerta == NivelAlerta.CRITICO:
                    recomendacoes.extend([
                        Recomendacao(
                            titulo="Aumentar dose de anti-hipertensivo",
                            descricao=f"PA {valor_atual} mmHg. Considerar aumento de ARA2/IECA para dose máxima",
                            acao="AUMENTAR_MEDICACAO",
                            parametro_alvo="PA sistólica",
                            valor_alvo=140,
                            urgencia=UrgenciaIntervencao.URGENTE.value,
                            evidencia=["SBC 2020", f"PA acima objetivo em {valor_atual - valor_objetivo} mmHg"],
                            conflitos=[]
                        ),
                        Recomendacao(
                            titulo="Adicionar segunda classe farmacológica",
                            descricao="Se monotherapy já em dose máxima, considerar BCC ou diurético",
                            acao="ADICIONAR",
                            parametro_alvo="PA sistólica",
                            valor_alvo=130,
                            urgencia=UrgenciaIntervencao.URGENTE.value,
                            evidencia=["SBC 2020 - combinação terapêutica"],
                            conflitos=["Avaliar K+ se diurético"]
                        )
                    ])
                elif nivel_alerta == NivelAlerta.ALTO:
                    recomendacoes.append(
                        Recomendacao(
                            titulo="Aumentar dose de anti-hipertensivo",
                            descricao="PA acima objetivo. Aumentar para dose intermediária",
                            acao="AUMENTAR_MEDICACAO",
                            parametro_alvo="PA sistólica",
                            valor_alvo=140,
                            urgencia=UrgenciaIntervencao.ROTINA.value,
                            evidencia=["SBC 2020"],
                            conflitos=[]
                        )
                    )
        
        # Diabetes (E11)
        elif cid10.startswith("E11"):
            if parametro == "HbA1c" and valor_atual > valor_objetivo:
                if nivel_alerta == NivelAlerta.CRITICO:
                    recomendacoes.extend([
                        Recomendacao(
                            titulo="Escalar terapia antidiabética",
                            descricao=f"HbA1c {valor_atual}%. Iniciar segunda classe (GLP-1 ou SGLT2i)",
                            acao="ADICIONAR",
                            parametro_alvo="HbA1c",
                            valor_alvo=7.0,
                            urgencia=UrgenciaIntervencao.URGENTE.value,
                            evidencia=["ADA 2024", "HbA1c crítico"],
                            conflitos=["GLP-1: risco pancreatite", "SGLT2i: DKA"]
                        )
                    ])
                elif nivel_alerta == NivelAlerta.ALTO:
                    recomendacoes.append(
                        Recomendacao(
                            titulo="Aumentar Metformina",
                            descricao=f"HbA1c {valor_atual}%. Se não em dose máxima, escalar para 2000mg",
                            acao="AUMENTAR_MEDICACAO",
                            parametro_alvo="HbA1c",
                            valor_alvo=7.5,
                            urgencia=UrgenciaIntervencao.ROTINA.value,
                            evidencia=["ADA 2024"],
                            conflitos=["GI intolerance"]
                        )
                    )
        
        # IC (I50)
        elif cid10.startswith("I50"):
            if parametro == "Classe NYHA" and valor_atual > valor_objetivo:
                recomendacoes.append(
                    Recomendacao(
                        titulo="Aumentar dose de diurético",
                        descricao="Aumentar congestão. Titular Furosemida para melhor controle",
                        acao="AUMENTAR_MEDICACAO",
                        parametro_alvo="Congestão",
                        valor_alvo=0.0,
                        urgencia=UrgenciaIntervencao.URGENTE.value,
                        evidencia=["ACC/AHA 2022"],
                        conflitos=["Monitorar K+ e Creatinina"]
                    )
                )
        
        # Se nenhuma recomendação foi gerada, adicionar genérica
        if not recomendacoes:
            recomendacoes.append(
                Recomendacao(
                    titulo="Monitorar e reavalia próxima consulta",
                    descricao=f"{parametro}: {valor_atual} (meta: {valor_objetivo}). Reavalie em 4 semanas",
                    acao="MONITORAR",
                    parametro_alvo=parametro,
                    valor_alvo=valor_objetivo,
                    urgencia=UrgenciaIntervencao.ELETIVA.value,
                    evidencia=["Recomendação padrão"],
                    conflitos=[]
                )
            )
        
        return recomendacoes

    @staticmethod
    def agrupar_alertas_paciente(
        condicao_cronica_id: int,
        cid10: str,
        diagnostico: str,
        alertas: List[Alerta]
    ) -> GrupoAlerta:
        """
        Agrupa alertas relacionados e determina urgência máxima.
        
        Args:
            condicao_cronica_id: ID da condição
            cid10: Código diagnóstico
            diagnostico: Nome do diagnóstico
            alertas: Lista de alertas individual
            
        Returns:
            GrupoAlerta com alertas categorizados por nível
        """
        
        grupo = GrupoAlerta(
            condicao_cronica_id=condicao_cronica_id,
            cid10=cid10,
            diagnostico=diagnostico
        )
        
        for alerta in alertas:
            if alerta.nivel == NivelAlerta.CRITICO.value:
                grupo.alertas_criticos.append(alerta)
            elif alerta.nivel == NivelAlerta.ALTO.value:
                grupo.alertas_altos.append(alerta)
            elif alerta.nivel == NivelAlerta.MEDIO.value:
                grupo.alertas_medios.append(alerta)
            else:
                grupo.alertas_baixos.append(alerta)
        
        # Determinar urgência máxima
        if grupo.alertas_criticos:
            grupo.urgencia_maxima = NivelAlerta.CRITICO.value
        elif grupo.alertas_altos:
            grupo.urgencia_maxima = NivelAlerta.ALTO.value
        elif grupo.alertas_medios:
            grupo.urgencia_maxima = NivelAlerta.MEDIO.value
        else:
            grupo.urgencia_maxima = NivelAlerta.BAIXO.value
        
        return grupo

    @staticmethod
    def marcar_alerta_resolvido(
        alerta: Alerta,
        nota_resolucao: str
    ) -> Alerta:
        """
        Marca alerta como resolvido (ex: após aumento de medicação e melhora).
        
        Args:
            alerta: Alerta a ser resolvido
            nota_resolucao: Ex: "PA normalizada após aumento Losartan"
            
        Returns:
            Alerta com status RESOLVIDO
        """
        
        alerta.status = "RESOLVIDO"
        alerta.data_resolucao = datetime.now()
        alerta.nota_resolucao = nota_resolucao
        
        return alerta

    @staticmethod
    def detectar_descompensacao_iminente(
        alertas_ativos: List[Alerta],
        parametros_criticos: Dict[str, bool]
    ) -> bool:
        """
        Detecta se há risco de descompensação baseado em múltiplos sinais.
        
        Descompensação suspeita se:
        - 2+ alertas CRÍTICOS em diferentes sistemas, OU
        - 1 alerta CRÍTICO + piora em múltiplos parâmetros
        
        Args:
            alertas_ativos: Lista de alertas CRITICOS|ALTOS
            parametros_criticos: {"PA sistolica": True, "HbA1c": True}
            
        Returns:
            True se descompensação iminente
        """
        
        alertas_criticos = [a for a in alertas_ativos if a.nivel == NivelAlerta.CRITICO.value]
        alertas_altos = [a for a in alertas_ativos if a.nivel == NivelAlerta.ALTO.value]
        
        criticos_count = len(alertas_criticos)
        parametros_criticos_count = sum(1 for v in parametros_criticos.values() if v)
        
        # 2+ críticos = Descompensação confirmada
        if criticos_count >= 2:
            return True
        
        # 1 crítico + 2+ parâmetros críticos = Descompensação provável
        if criticos_count >= 1 and parametros_criticos_count >= 2:
            return True
        
        # 3+ altos em tendência PIORA = Descompensação suspeita
        alertas_altos_piora = [a for a in alertas_altos if a.tendencia == "PIORA"]
        if len(alertas_altos_piora) >= 3:
            return True
        
        return False

    @staticmethod
    def calcular_score_controle(
        alertas_ativos: List[Alerta]
    ) -> int:
        """
        Calcula score de controle da condição (0-100).
        
        - 100: Sem alertas
        - 75-99: Alertas BAIXO apenas
        - 50-74: Alertas MÉDIO
        - 25-49: Alertas ALTO
        - 0-24: Alertas CRITICO
        
        Args:
            alertas_ativos: Alertas não resolvidos
            
        Returns:
            Score 0-100
        """
        
        if not alertas_ativos:
            return 100
        
        criticos = sum(1 for a in alertas_ativos if a.nivel == NivelAlerta.CRITICO.value)
        altos = sum(1 for a in alertas_ativos if a.nivel == NivelAlerta.ALTO.value)
        medios = sum(1 for a in alertas_ativos if a.nivel == NivelAlerta.MEDIO.value)
        baixos = sum(1 for a in alertas_ativos if a.nivel == NivelAlerta.BAIXO.value)
        
        if criticos > 0:
            score = max(0, 20 - criticos * 5)
        elif altos > 0:
            score = max(25, 50 - altos * 5)
        elif medios > 0:
            score = max(50, 75 - medios * 3)
        else:
            score = min(99, 75 + baixos)
        
        return score
