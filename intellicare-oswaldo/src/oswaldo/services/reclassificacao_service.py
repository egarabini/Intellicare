"""
Serviço de Reclassificação - Orquestração de reestagiamento de condições crônicas.

Responsabilidades:
1. Buscar última classificação (histórico)
2. Comparar estágios (anterior vs novo)
3. Detectar piora progressiva
4. Determinar necessidade de alerta
"""

import logging
from typing import Optional, Dict, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc

from src.oswaldo.models.oswaldo_models import (
    CondicaoCronica, Estadiamento, Alerta
)

logger = logging.getLogger(__name__)


# Mapeamentos de gravidade por sistema de classificação
MAPEAMENTO_SEVERIDADE = {
    "HAS": {
        "NORMAL": 0,
        "ELEVADA": 1,
        "ESTAGIO_1": 2,
        "ESTAGIO_2": 3,
        "ESTAGIO_3": 4,
        "CRITICA": 5
    },
    "DRC": {
        "G1": 0,          # TFGE >= 90
        "G2": 1,          # TFGE 60-89
        "G3a": 2,         # TFGE 45-59
        "G3b": 2.5,       # TFGE 30-44
        "G4": 3,          # TFGE 15-29
        "G5": 4           # TFGE < 15
    },
    "DIABETES": {
        "CONTROLE": 0,    # HbA1c < 7%, glicemia < 180
        "LEVE": 1,        # HbA1c 7-8%, glicemia < 250
        "MODERADO": 2,    # HbA1c 8-9%, glicemia < 300
        "SEVERO": 3,      # HbA1c > 9%, glicemia > 300
        "CRITICA": 4      # Emergência: glicemia > 400 ou < 40
    },
    "INSUF_CARDIACA": {
        "ASSINTOMATICA": 0,
        "NYHA_I": 0.5,
        "NYHA_II": 1.5,
        "NYHA_III": 2.5,
        "NYHA_IV": 3.5
    }
}


class ReclassificacaoService:
    """
    Serviço responsável por reclassificação dinâmica de condições crônicas.
    
    Fluxo:
    1. Receber novo evento (exame, consulta, etc)
    2. Obter última classificação
    3. Reclassificar com novo valor
    4. Comparar: detectar mudança de estágio
    5. Se piora: gerar alerta clínico
    """
    
    def __init__(self, db: Session):
        """
        Inicializa serviço com conexão ao banco.
        
        Args:
            db: Sessão SQLAlchemy
        """
        self.db = db
    
    # ================================================================
    # 4.1: QUERY PARA RECLASSIFICAÇÃO
    # ================================================================
    
    def obter_ultima_classificacao(self, condicao_id: int) -> Optional[Estadiamento]:
        """
        Busca o histórico mais recente de classificação para uma condição.
        
        Args:
            condicao_id: ID da condição crônica
        
        Returns:
            Estadiamento mais recente ou None se não houver histórico
        """
        try:
            ultima = self.db.query(Estadiamento)\
                .filter(Estadiamento.condicao_cronica_id == condicao_id)\
                .order_by(desc(Estadiamento.data_classificacao))\
                .first()
            
            if ultima:
                logger.info(f"[RECLASSIFICACAO] Última classificação encontrada: "
                           f"condicao_id={condicao_id}, estagio={ultima.estagio}, "
                           f"data={ultima.data_classificacao}")
            else:
                logger.warning(f"[RECLASSIFICACAO] Nenhuma classificação anterior para "
                              f"condicao_id={condicao_id}")
            
            return ultima
        
        except Exception as e:
            logger.error(f"[RECLASSIFICACAO] Erro ao buscar classificação: {str(e)}")
            raise
    
    def obter_condicao_cronica(self, condicao_id: int) -> Optional[CondicaoCronica]:
        """
        Busca metadados da condição crônica.
        
        Args:
            condicao_id: ID da condição
        
        Returns:
            CondicaoCronica ou None
        """
        try:
            condicao = self.db.query(CondicaoCronica)\
                .filter(CondicaoCronica.id == condicao_id)\
                .first()
            
            return condicao
        
        except Exception as e:
            logger.error(f"[RECLASSIFICACAO] Erro ao buscar condição: {str(e)}")
            raise
    
    # ================================================================
    # 4.2: COMPARAÇÃO DE ESTÁGIOS
    # ================================================================
    
    def comparar_estadios(self, estagio_anterior: str, estagio_novo: str, 
                         sistema: str = "HAS") -> Dict:
        """
        Compara dois estágios clínicos e detecta mudança.
        
        Args:
            estagio_anterior: Estágio anterior (ex: "ESTAGIO_1")
            estagio_novo: Novo estágio (ex: "ESTAGIO_2")
            sistema: Sistema de classificação (HAS, DRC, DIABETES, INSUF_CARDIACA)
        
        Returns:
            {
                'mudou': bool,
                'piora': bool,
                'melhora': bool,
                'severidade_anterior': float,
                'severidade_novo': float,
                'delta_severidade': float
            }
        """
        try:
            # Obter mapeamento de severidade
            mapa = MAPEAMENTO_SEVERIDADE.get(sistema, {})
            
            if not mapa:
                logger.warning(f"[RECLASSIFICACAO] Sistema {sistema} não encontrado")
                return {'mudou': False, 'piora': False, 'melhora': False}
            
            # Obter severidade de cada estágio
            sev_anterior = mapa.get(estagio_anterior, 0)
            sev_novo = mapa.get(estagio_novo, 0)
            
            # Calcular delta
            delta = sev_novo - sev_anterior
            mudou = delta != 0
            piora = delta > 0
            melhora = delta < 0
            
            resultado = {
                'mudou': mudou,
                'piora': piora,
                'melhora': melhora,
                'severidade_anterior': sev_anterior,
                'severidade_novo': sev_novo,
                'delta_severidade': delta,
                'sistema': sistema,
                'estagio_anterior': estagio_anterior,
                'estagio_novo': estagio_novo
            }
            
            logger.info(f"[RECLASSIFICACAO] Comparação: {estagio_anterior} → {estagio_novo} "
                       f"(delta={delta}, piora={piora})")
            
            return resultado
        
        except Exception as e:
            logger.error(f"[RECLASSIFICACAO] Erro na comparação: {str(e)}")
            raise
    
    # ================================================================
    # 4.3: DETECÇÃO DE PIORA PROGRESSIVA
    # ================================================================
    
    def detectar_piora_progressiva(self, ultima: Optional[Estadiamento], 
                                  novo_estagio: str, 
                                  sistema: str) -> Dict:
        """
        Detecta piora progressiva comparando última classificação com a nova.
        
        Critérios:
        - Mudança de estágio para pior
        - Queda >= 2 níveis de severidade
        
        Args:
            ultima: Última Estadiamento ou None (primeira vez)
            novo_estagio: Novo estágio clínico
            sistema: Sistema de classificação
        
        Returns:
            {
                'piora_detectada': bool,
                'motivo': str,
                'comparacao': dict (resultado de comparar_estadios)
            }
        """
        try:
            # Caso 1: Primeira classificação (não há precedente)
            if not ultima:
                logger.info(f"[RECLASSIFICACAO] Primeira classificação para "
                           f"sistema={sistema}, estagio={novo_estagio}")
                return {
                    'piora_detectada': False,
                    'motivo': 'Primeira classificação',
                    'comparacao': None
                }
            
            # Caso 2: Comparar com última
            comparacao = self.comparar_estadios(
                estagio_anterior=ultima.estagio,
                estagio_novo=novo_estagio,
                sistema=sistema
            )
            
            # Piora detectada se: delta > 0 OU delta >= 1 (mudança significativa)
            piora_detectada = comparacao['piora'] and comparacao['delta_severidade'] >= 1
            
            motivo = ""
            if piora_detectada:
                motivo = (f"Piora progressiva: {ultima.estagio} → {novo_estagio} "
                         f"(delta = {comparacao['delta_severidade']})")
            
            resultado = {
                'piora_detectada': piora_detectada,
                'motivo': motivo,
                'comparacao': comparacao
            }
            
            logger.info(f"[RECLASSIFICACAO] Piora detectada: {piora_detectada}, motivo={motivo}")
            
            return resultado
        
        except Exception as e:
            logger.error(f"[RECLASSIFICACAO] Erro ao detectar piora: {str(e)}")
            raise
    
    # ================================================================
    # 4.4: LÓGICA PARA ALERTA
    # ================================================================
    
    def necessita_novo_alerta(self, piora_detectada: bool, novo_estagio: str, 
                             sistema: str) -> Tuple[bool, str, str]:
        """
        Determina necessidade de gerar novo alerta baseado em piora + severidade.
        
        Regras:
        - Piora progressiva SEMPRE gera alerta
        - Crítico na primeira vez TAMBÉM gera alerta
        - Melhora nunca gera alerta
        
        Args:
            piora_detectada: Se houve piora progressiva
            novo_estagio: Novo estágio clínico
            sistema: Sistema de classificação
        
        Returns:
            (gera_alerta: bool, severidade: str, descricao: str)
        """
        try:
            severidade_map = MAPEAMENTO_SEVERIDADE.get(sistema, {})
            nova_severidade = severidade_map.get(novo_estagio, 0)
            
            # Lógica de alerta
            gera_alerta = False
            severidade_alerta = "BAIXA"
            descricao = ""
            
            # Condição 1: Piora detectada
            if piora_detectada:
                gera_alerta = True
                descricao = f"Piora progressiva em {sistema}: novo estagio {novo_estagio}"
                
                # Determinar severidade do alerta pela nova severidade
                if nova_severidade >= 4:
                    severidade_alerta = "CRITICA"
                elif nova_severidade >= 3:
                    severidade_alerta = "ALTA"
                elif nova_severidade >= 2:
                    severidade_alerta = "MEDIA"
                else:
                    severidade_alerta = "BAIXA"
            
            # Condição 2: Primeira vez e já crítico
            elif nova_severidade >= 4:
                gera_alerta = True
                severidade_alerta = "CRITICA"
                descricao = f"Classificação crítica inicial em {sistema}: {novo_estagio}"
            
            # Condição 3: Estágio crítico específicos
            elif "CRITICA" in novo_estagio.upper() or "CRITICO" in novo_estagio.upper():
                gera_alerta = True
                severidade_alerta = "CRITICA"
                descricao = f"Estágio crítico detectado em {sistema}: {novo_estagio}"
            
            logger.info(f"[RECLASSIFICACAO] Alerta necessário: {gera_alerta}, "
                       f"severidade={severidade_alerta}, descricao={descricao}")
            
            return (gera_alerta, severidade_alerta, descricao)
        
        except Exception as e:
            logger.error(f"[RECLASSIFICACAO] Erro ao verificar necessidade de alerta: {str(e)}")
            raise
    
    # ================================================================
    # 4.5: MÉTODOS AUXILIARES
    # ================================================================
    
    def obter_historico_classificacoes(self, condicao_id: int, limite: int = 10) -> list:
        """
        Busca histórico de classificações para uma condição.
        
        Args:
            condicao_id: ID da condição
            limite: Número máximo de registros (default=10)
        
        Returns:
            Lista de Estadiamento ordenada por data descrescente
        """
        try:
            historico = self.db.query(Estadiamento)\
                .filter(Estadiamento.condicao_cronica_id == condicao_id)\
                .order_by(desc(Estadiamento.data_classificacao))\
                .limit(limite)\
                .all()
            
            logger.info(f"[RECLASSIFICACAO] Histórico obtido: condicao_id={condicao_id}, "
                       f"registros={len(historico)}")
            
            return historico
        
        except Exception as e:
            logger.error(f"[RECLASSIFICACAO] Erro ao obter histórico: {str(e)}")
            raise
    
    def calcular_tendencia(self, condicao_id: int, sistema: str) -> str:
        """
        Calcula tendência da condição (piora progressiva, estável, melhora).
        
        Args:
            condicao_id: ID da condição
            sistema: Sistema de classificação
        
        Returns:
            "PIORA_PROGRESSIVA" | "ESTAVEL" | "MELHORA"
        """
        try:
            historico = self.obter_historico_classificacoes(condicao_id, limite=5)
            
            if len(historico) < 2:
                return "INSUFICIENTE_DADOS"
            
            # Comparar últimas 2 classificações (mais recente vs anterior)
            ultima = historico[0]
            anterior = historico[1] if len(historico) > 1 else None
            
            if not anterior:
                return "INSUFICIENTE_DADOS"
            
            comparacao = self.comparar_estadios(anterior.estagio, ultima.estagio, sistema)
            
            if comparacao['piora']:
                return "PIORA_PROGRESSIVA"
            elif comparacao['melhora']:
                return "MELHORA"
            else:
                return "ESTAVEL"
        
        except Exception as e:
            logger.error(f"[RECLASSIFICACAO] Erro ao calcular tendência: {str(e)}")
            return "ERRO"
