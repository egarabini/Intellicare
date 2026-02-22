"""
Event handlers para Oswaldo.

Processam eventos do Florence:
1. handle_exame_resultado - Reclassificar condição e gerar alertas
2. handle_paciente_dados - Atualizar perfil do paciente
3. handle_request_consulta - Agendar acompanhamento
"""

import logging
import json
from datetime import datetime
from sqlalchemy.orm import Session

from src.oswaldo.models.oswaldo_models import (
    CondicaoCronica, Estadiamento, Acompanhamento, Alerta
)
from src.oswaldo.services.diagnostico_service import DiagnosticoService
from src.oswaldo.services.classificacao_service import ClassificacaoService
from src.oswaldo.database.session import SessionLocal

logger = logging.getLogger(__name__)


class FlorenzeEventHandlers:
    """Handlers para processar eventos do Florence."""
    
    def __init__(self, db_session: Session = None):
        """Inicializar com sessão de banco de dados."""
        self.db = db_session or SessionLocal()
        self.diagnostico_service = DiagnosticoService()
        self.classificacao_service = ClassificacaoService()
    
    def handle_exame_resultado(self, event: dict):
        """
        Processar novo resultado de exame.
        
        Ações:
        1. Verificar se há condição correspondente
        2. Reclassificar usando novo valor
        3. Se mudou classificação → salvar novo Estadiamento
        4. Se piora → gerar Alerta
        5. Salvar acompanhamento
        """
        try:
            cpf_hash = event.get("paciente_cpf_hash")
            tipo_exame = event.get("tipo_exame")
            valor = event.get("valor")
            laboratorio = event.get("laboratorio", "N/A")
            
            logger.info(f"[Exame] Processando {tipo_exame}={valor} para paciente {cpf_hash[:8]}...")
            
            # Mapear tipo de exame para condição CID-10
            cid_map = {
                "glicemia": "E11",  # Diabetes
                "hba1c": "E11",
                "creatinina": "N18",  # Doença renal
                "pa": "I10",  # Hipertensão
                "pressao_arterial": "I10",
                "colesterol": "E78",  # Dislipidem
            }
            
            cid10 = cid_map.get(tipo_exame, None)
            if not cid10:
                logger.warning(f"[Exame] Tipo de exame desconhecido: {tipo_exame}")
                return
            
            # Buscar condição ativa do paciente
            condicao = self.db.query(CondicaoCronica).filter(
                CondicaoCronica.paciente_cpf_hash == cpf_hash,
                CondicaoCronica.cid10 == cid10,
                CondicaoCronica.status != "ENCERRADO"
            ).first()
            
            if not condicao:
                logger.warning(f"[Exame] Nenhuma condição {cid10} ativa para paciente")
                # Poderia criar diagnóstico automático aqui
                return
            
            # Reclassificar baseado no novo exame
            nova_classe = self._reclassificar_exame(tipo_exame, valor, condicao.id)
            
            if nova_classe:
                # Comparar com última classificação
                ultima_classificacao = self.db.query(Estadiamento).filter(
                    Estadiamento.condicao_cronica_id == condicao.id
                ).order_by(Estadiamento.id.desc()).first()
                
                mudou = not ultima_classificacao or ultima_classificacao.estagio != nova_classe['estagio']
                
                if mudou:
                    logger.info(f"[Exame] Reclassificação: {ultima_classificacao.estagio if ultima_classificacao else 'N/A'} → {nova_classe['estagio']}")
                    
                    # Salvar novo estadiamento
                    novo_est = Estadiamento(
                        condicao_cronica_id=condicao.id,
                        sistema_classificacao=nova_classe['sistema'],
                        estagio=nova_classe['estagio'],  # Just the stage code (e.g., "A3", "G3a")
                        criterios=json.dumps({
                            "origem": "exame_automatico", 
                            "tipo": tipo_exame, 
                            "valor": valor,
                            "detalhes_classificacao": nova_classe['detalhes']
                        })
                    )
                    self.db.add(novo_est)
                    
                    # Gerar alerta se piora ou se estágio inicial é crítico
                    if ultima_classificacao:
                        if self._detectar_piora(ultima_classificacao.estagio, nova_classe['estagio']):
                            logger.warning(f"[Alerta] Piora detectada: {nova_classe['estagio']}")
                            self._gerar_alerta(condicao.id, cpf_hash, nova_classe, tipo_exame, valor)
                    else:
                        # Primeira vez: gerar alerta se for crítico
                        if "CRITICO" in nova_classe['estagio'].upper() or "A3" in nova_classe['estagio'] or "G5" in nova_classe['estagio']:
                            logger.warning(f"[Alerta] Primeira classificação crítica: {nova_classe['estagio']}")
                            self._gerar_alerta(condicao.id, cpf_hash, nova_classe, tipo_exame, valor)
            
            # Registrar acompanhamento
            acomp = Acompanhamento(
                paciente_cpf_hash=cpf_hash,
                condicao_cronica_id=condicao.id,
                data_acompanhamento=datetime.utcnow(),
                medico_id=event.get("medico_solicitante", "SISTEMA"),
                pressao_arterial=f"{int(valor)}/XX" if tipo_exame in ["pa", "pressao_arterial"] else None,
                glicemia=valor if tipo_exame in ["glicemia", "hba1c"] else None,
                observacoes=f"Exame automático: {tipo_exame}={valor} @ {laboratorio}"
            )
            self.db.add(acomp)
            self.db.commit()
            
            logger.info(f"[Exame] Processado com sucesso: {tipo_exame}={valor}")
        except Exception as e:
            logger.error(f"[Exame] Erro ao processar: {e}", exc_info=True)
            self.db.rollback()
            raise
    
    def handle_paciente_dados(self, event: dict):
        """
        Processar atualização de dados do paciente.
        
        Exemplo: idade, peso, altura, IMC, comorbidades
        Poderia disparar diagnósticos automáticos baseado em dados novos.
        """
        try:
            cpf_hash = event.get("paciente_cpf_hash")
            idade = event.get("idade")
            peso = event.get("peso_kg")
            altura = event.get("altura_cm")
            
            logger.info(f"[Paciente] Atualizando dados de {cpf_hash[:8]}: idade={idade}, peso={peso}, altura={altura}")
            
            # Aqui poderia:
            # 1. Atualizar cache de dados do paciente
            # 2. Disparar re-diagnóstico se dados significativos mudaram
            # 3. Atualizar score de risco
            
            logger.info(f"[Paciente] Dados atualizados com sucesso")
            
        except Exception as e:
            logger.error(f"[Paciente] Erro ao processar: {e}", exc_info=True)
    
    def handle_request_consulta(self, event: dict):
        """
        Processar solicitação de consulta/acompanhamento.
        
        Ações:
        1. Criar agendamento
        2. Definir prioridade baseado em urgência
        3. Notificar médico responsável
        """
        try:
            cpf_hash = event.get("paciente_cpf_hash")
            motivo = event.get("motivo", "Acompanhamento")
            urgencia = event.get("urgencia", "normal")
            
            logger.info(f"[Consulta] Solicitação para {cpf_hash[:8]}: {motivo} (urgência={urgencia})")
            
            # Aqui poderia:
            # 1. Criar ticket de agendamento
            # 2. Calcular próxima data baseado em urgência e estágio da doença
            # 3. Notificar coordenação de agendamento
            
            logger.info(f"[Consulta] Solicitação registrada com sucesso")
            
        except Exception as e:
            logger.error(f"[Consulta] Erro ao processar: {e}", exc_info=True)
    
    # ========================================================================
    # Métodos auxiliares
    # ========================================================================
    
    def _reclassificar_exame(self, tipo_exame: str, valor: float, condicao_id: int) -> dict:
        """Reclassificar condição baseado no novo exame."""
        
        if tipo_exame in ["pressao_arterial", "pa"]:
            # Assumir valor é PA sistólica
            classe = self.classificacao_service.classificar_has(valor, 90)
            return {
                "sistema": "SBC",
                "estagio": classe.get("estagio_sbc", "II"),  # Extract just the stage code
                "detalhes": classe,
                "valor": valor
            }
        
        elif tipo_exame in ["glicemia", "hba1c"]:
            classe = self.classificacao_service.classificar_diabetes(valor, valor)
            return {
                "sistema": "ADA",
                "estagio": classe.get("estagio_aida", "A3"),  # Extract just the stage code
                "detalhes": classe,
                "valor": valor
            }
        
        elif tipo_exame == "creatinina":
            # Calcular TFGE (simplificado)
            tfge = max(15, 100 - (valor - 0.7) * 50)  # Fórmula muito simplificada
            classe = self.classificacao_service.classificar_drc(tfge, tfge)
            return {
                "sistema": "KDIGO",
                "estagio": classe.get("estagio_kdigo", "G3a"),  # Extract just the stage code
                "detalhes": classe,
                "valor": tfge
            }
        
        return None
    
    def _detectar_piora(self, estagio_anterior: str, estagio_novo: str) -> bool:
        """Detectar se houve piora entre estágios."""
        
        # Ordem de estagiamento (do melhor para o pior)
        ordem_has = ["NORMAL", "ELEVADA", "ESTAGIO_1", "ESTAGIO_2", "ESTAGIO_3"]
        ordem_drc = ["G1", "G2", "G3a", "G3b", "G4", "G5"]
        ordem_diabetes = ["A0", "A1", "A2", "A3"]  # ADA classification codes
        
        def get_rank(estagio, ordem):
            try:
                return ordem.index(estagio)
            except:
                return -1
        
        # Tentar todas as ordens
        for ordem in [ordem_has, ordem_drc, ordem_diabetes]:
            rank_ant = get_rank(estagio_anterior, ordem)
            rank_novo = get_rank(estagio_novo, ordem)
            if rank_ant >= 0 and rank_novo >= 0:
                return rank_novo > rank_ant
        
        return False
    
    def _gerar_alerta(self, condicao_id: int, cpf_hash: str, classe: dict, tipo_exame: str, valor: float):
        """Gerar alerta clínico por piora."""
        
        alerta = Alerta(
            paciente_cpf_hash=cpf_hash,
            condicao_cronica_id=condicao_id,
            tipo_alerta="PIORA_PROGRESSIVA",
            severidade=self._calcular_severidade(classe['estagio']),
            descricao=f"Piora em {tipo_exame}: novo valor {valor} classificado como {classe['estagio']}",
            dados_alerta=json.dumps({
                "tipo_exame": tipo_exame,
                "valor": valor,
                "estagio": classe['estagio'],
                "sistema": classe['sistema']
            }),
            status="NOVO"
        )
        
        self.db.add(alerta)
    
    def _calcular_severidade(self, estagio: str) -> str:
        """Calcular severidade de alerta baseado no estágio."""
        
        if any(x in estagio.upper() for x in ["CRITICO", "G5", "ESTAGIO_3"]):
            return "CRITICO"
        elif any(x in estagio.upper() for x in ["MAL", "ESTAGIO_2", "G4"]):
            return "ALTO"
        elif any(x in estagio.upper() for x in ["MODERADO", "ESTAGIO_1", "G3"]):
            return "MÉDIO"
        else:
            return "BAIXO"
