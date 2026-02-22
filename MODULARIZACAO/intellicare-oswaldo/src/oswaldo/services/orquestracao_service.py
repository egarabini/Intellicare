"""
Serviço de Orquestração - Automatização de reclassificação completa.

Fluxo E2E:
1. Receber exame novo (ExameResultadoEvent)
2. Validar dados
3. Obter condição ativa
4. Reclassificar exame com novo valor
5. Salvar Estadiamento (transaction)
6. Detectar piora progressiva
7. Gerar Alerta se necessário
8. Atualizar Plano de Cuidado
9. Log de evento no timeline
"""

import logging
from typing import Dict, Tuple, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from src.oswaldo.models.oswaldo_models import (
    CondicaoCronica, Estadiamento, Alerta, Acompanhamento
)
from src.oswaldo.integrations.event_models import ExameResultadoEvent, TipoExame
from src.oswaldo.services.reclassificacao_service import ReclassificacaoService
from src.oswaldo.services.classificacao_service import ClassificacaoService
from src.oswaldo.services.transaction_service import transactional

logger = logging.getLogger(__name__)


class OrquestradorService:
    """
    Orquestra o fluxo completo de processamento de novo exame clínico.
    
    Coordena:
    1. ReclassificacaoService - Comparação de estágios
    2. ClassificacaoService - Classificação de novo valor
    3. AlertService (via Alerta model) - Geração de alertas
    4. PlanoCuidadoService (futura) - Atualização de plano
    """
    
    def __init__(self, db: Session):
        """
        Inicializa orquestrador com dependências.
        
        Args:
            db: Sessão SQLAlchemy
        """
        self.db = db
        self.reclassificacao_svc = ReclassificacaoService(db)
        self.classificacao_svc = ClassificacaoService()
    
    # ================================================================
    # 4.2: PROCESSAMENTO DE NOVO EXAME
    # ================================================================
    
    @transactional(operation_name="processar_exame_novo", generate_error_alert=True)
    def processar_exame_novo(self, event: ExameResultadoEvent) -> Dict:
        """
        Processa novo exame e executa orquestração completa.
        
        Fluxo:
        1. Validar evento
        2. Obter condição ativa
        3. Reclassificar com novo exame
        4. Salvar Estadiamento (tx)
        5. Detectar piora
        6. Gerar Alerta se piora
        7. Atualizar Plano
        8. Log timeline
        
        Args:
            event: ExameResultadoEvent com valor novo
        
        Returns:
            {
                'sucesso': bool,
                'condicao_id': int,
                'estadiamento_criado': bool,
                'alerta_gerado': bool,
                'alerta_id': Optional[int],
                'mensagem': str,
                'detalhes': dict
            }
        """
        resultado = {
            'sucesso': False,
            'condicao_id': None,
            'estadiamento_criado': False,
            'alerta_gerado': False,
            'alerta_id': None,
            'mensagem': '',
            'detalhes': {}
        }
        
        try:
            # STEP 1: Validar evento
            validacao = self._validar_evento(event)
            if not validacao['valido']:
                resultado['mensagem'] = f"Evento inválido: {validacao['motivo']}"
                logger.warning(f"[ORQU] {resultado['mensagem']}")
                return resultado
            
            logger.info(f"[ORQU] Processando exame: paciente={event.paciente_cpf_hash}, "
                       f"tipo={event.tipo_exame.value}, valor={event.valor}")
            
            # STEP 2: Obter condição ativa
            condicao = self._obter_condicao_ativa_para_exame(event.paciente_cpf_hash, event.tipo_exame)
            if not condicao:
                resultado['mensagem'] = f"Nenhuma condição ativa para este exame"
                logger.warning(f"[ORQU] {resultado['mensagem']}")
                return resultado
            
            resultado['condicao_id'] = condicao.id
            logger.info(f"[ORQU] Condição obtida: id={condicao.id}, cid10={condicao.cid10}")
            
            # STEP 3: Reclassificar com novo exame
            reclassificacao = self._reclassificar_com_novo_exame(
                condicao=condicao,
                event=event
            )
            resultado['detalhes']['reclassificacao'] = reclassificacao
            
            novo_estagio = reclassificacao['novo_estagio']
            sistema_classificacao = reclassificacao['sistema']
            logger.info(f"[ORQU] Reclassificação: {reclassificacao.get('estagio_anterior', 'PRIMEIRA')} "
                       f"→ {novo_estagio}")
            
            # STEP 4: Salvar Estadiamento (transação)
            estadiamento = self._salvar_estadiamento_transacao(
                condicao_id=condicao.id,
                sistema=sistema_classificacao,
                novo_estagio=novo_estagio,
                criterios=reclassificacao.get('criterios', {}),
                exames_suporte=[{
                    'tipo': event.tipo_exame.value,
                    'valor': event.valor,
                    'unidade': event.unidade,
                    'data': event.data_coleta.isoformat()
                }]
            )
            
            if not estadiamento:
                resultado['mensagem'] = "Falha ao salvar Estadiamento"
                logger.error(f"[ORQU] {resultado['mensagem']}")
                return resultado
            
            resultado['estadiamento_criado'] = True
            logger.info(f"[ORQU] Estadiamento criado: id={estadiamento.id}")
            
            # STEP 5: Detectar piora
            ultima = self.reclassificacao_svc.obter_ultima_classificacao(condicao.id)
            piora_info = self.reclassificacao_svc.detectar_piora_progressiva(
                ultima=ultima if ultima and ultima.id != estadiamento.id else None,
                novo_estagio=novo_estagio,
                sistema=sistema_classificacao
            )
            
            resultado['detalhes']['piora'] = piora_info
            logger.info(f"[ORQU] Detecção de piora: {piora_info['piora_detectada']}")
            
            # STEP 6: Gerar Alerta se necessário
            gera_alerta, severidade, descricao = self.reclassificacao_svc.necessita_novo_alerta(
                piora_detectada=piora_info['piora_detectada'],
                novo_estagio=novo_estagio,
                sistema=sistema_classificacao
            )
            
            if gera_alerta:
                alerta = self._gerar_alerta(
                    condicao=condicao,
                    tipo_alerta="PIORA_PROGRESSIVA" if piora_info['piora_detectada'] else "DESCONTROLE",
                    severidade=severidade,
                    descricao=descricao,
                    dados_suporte={
                        'exame_tipo': event.tipo_exame.value,
                        'exame_valor': event.valor,
                        'estagio_anterior': piora_info['comparacao'].get('estagio_anterior') if piora_info['comparacao'] else 'PRIMEIRA',
                        'estagio_novo': novo_estagio
                    }
                )
                
                if alerta:
                    resultado['alerta_gerado'] = True
                    resultado['alerta_id'] = alerta.id
                    logger.info(f"[ORQU] Alerta criado: id={alerta.id}, severidade={severidade}")
            
            # STEP 7: Atualizar Plano de Cuidado (futura integração)
            # TODO: Integrar com PlanoCuidadoService quando implementado
            logger.info(f"[ORQU] Plano de Cuidado: atualização deferred (TBD)")
            
            # STEP 8: Log de evento no timeline (via Acompanhamento)
            self._registrar_acompanhamento_evento(
                condicao=condicao,
                evento_tipo='EXAME_RECLASSIFICACAO',
                evento_dados={
                    'exame_tipo': event.tipo_exame.value,
                    'valor': event.valor,
                    'estagio_novo': novo_estagio,
                    'alerta_gerado': gera_alerta
                }
            )
            
            # RESULTADO FINAL
            resultado['sucesso'] = True
            resultado['mensagem'] = f"Exame processado com sucesso: {novo_estagio}"
            logger.info(f"[ORQU] ✅ Processamento completo bem-sucedido")
            
            return resultado
        
        except SQLAlchemyError as e:
            resultado['mensagem'] = f"Erro de banco de dados: {str(e)}"
            logger.error(f"[ORQU] {resultado['mensagem']}")
            self.db.rollback()
            return resultado
        
        except Exception as e:
            resultado['mensagem'] = f"Erro inesperado: {str(e)}"
            logger.error(f"[ORQU] {resultado['mensagem']}")
            self.db.rollback()
            return resultado
    
    # ================================================================
    # 4.2.1: VALIDAÇÃO DE EVENTO
    # ================================================================
    
    def _validar_evento(self, event: ExameResultadoEvent) -> Dict:
        """
        Valida evento de exame antes de processar.
        
        Regras:
        - paciente_id não nulo
        - tipo_exame válido
        - valor dentro de faixa esperada
        - unidade compatível
        
        Args:
            event: ExameResultadoEvent
        
        Returns:
            {'valido': bool, 'motivo': str}
        """
        if not event.paciente_cpf_hash:
            return {'valido': False, 'motivo': 'paciente_cpf_hash nulo'}
        
        if not event.tipo_exame:
            return {'valido': False, 'motivo': 'tipo_exame nulo'}
        
        if event.valor is None or event.valor < 0:
            return {'valido': False, 'motivo': f'valor inválido: {event.valor}'}
        
        # Validação de faixa por tipo de exame
        faixas_esperadas = {
            TipoExame.GLICEMIA: (0, 1000),
            TipoExame.HBA1C: (0, 20),
            TipoExame.PA: (0, 300),  # sistólica
            TipoExame.CREATININA: (0, 10),
            TipoExame.COLESTEROL: (0, 500),
            TipoExame.OUTROS: (0, 10000)
        }
        
        faixa = faixas_esperadas.get(event.tipo_exame, (0, 10000))
        if event.valor > faixa[1]:
            logger.warning(f"[ORQU] Valor {event.valor} excede faixa esperada {faixa}")
            # Não falha, apenas avisa (pode ser crítico)
        
        return {'valido': True, 'motivo': ''}
    
    # ================================================================
    # 4.2.2: OBTER CONDIÇÃO ATIVA
    # ================================================================
    
    def _obter_condicao_ativa_para_exame(self, paciente_id: str, 
                                        tipo_exame: TipoExame) -> Optional[CondicaoCronica]:
        """
        Obtém condição crônica ativa para tipo de exame fornecido.
        
        Mapeamento:
        - GLICEMIA → E11 (Diabetes)
        - PA → I10 (HAS)
        - CREATININA → N18 (DRC)
        - HBA1C → E11 (Diabetes)
        - COLESTEROL → E78 (Dislipidemia)
        
        Args:
            paciente_id: CPF hash do paciente
            tipo_exame: Tipo de exame
        
        Returns:
            CondicaoCronica ativa ou None
        """
        mapeamento_cid = {
            TipoExame.GLICEMIA: "E11",
            TipoExame.HBA1C: "E11",
            TipoExame.PA: "I10",
            TipoExame.CREATININA: "N18",
            TipoExame.COLESTEROL: "E78",
            TipoExame.OUTROS: None
        }
        
        cid10_esperado = mapeamento_cid.get(tipo_exame)
        if not cid10_esperado:
            logger.warning(f"[ORQU] Tipo exame {tipo_exame.value} não mapeado")
            return None
        
        try:
            condicao = self.db.query(CondicaoCronica)\
                .filter(
                    CondicaoCronica.paciente_cpf_hash == paciente_id,
                    CondicaoCronica.cid10 == cid10_esperado,
                    CondicaoCronica.status == "CONFIRMADO"
                ).first()
            
            return condicao
        
        except Exception as e:
            logger.error(f"[ORQU] Erro ao buscar condição: {str(e)}")
            return None
    
    # ================================================================
    # 4.2.3: RECLASSIFICAR COM NOVO EXAME
    # ================================================================
    
    def _reclassificar_com_novo_exame(self, condicao: CondicaoCronica, 
                                     event: ExameResultadoEvent) -> Dict:
        """
        Reclassifica condição com novo valor de exame.
        
        Utiliza ClassificacaoService para gerar novo estágio baseado no valor.
        
        Args:
            condicao: CondicaoCronica
            event: ExameResultadoEvent com novo valor
        
        Returns:
            {
                'novo_estagio': str,
                'sistema': str,
                'criterios': dict,
                'estagio_anterior': Optional[str]
            }
        """
        try:
            # Obter última classificação
            ultima = self.reclassificacao_svc.obter_ultima_classificacao(condicao.id)
            
            estagio_anterior = ultima.estagio if ultima else "PRIMEIRA"
            
            # Usar ClassificacaoService para novo estágio
            novo_estagio, criterios = self._classificar_novo_valor(
                condicao_cid10=condicao.cid10,
                tipo_exame=event.tipo_exame,
                valor=event.valor
            )
            
            resultado = {
                'novo_estagio': novo_estagio,
                'sistema': self._obter_sistema_classificacao(condicao.cid10),
                'criterios': criterios,
                'estagio_anterior': estagio_anterior if ultima else None
            }
            
            return resultado
        
        except Exception as e:
            logger.error(f"[ORQU] Erro em reclassificação: {str(e)}")
            raise
    
    # ================================================================
    # 4.2.4: SALVAR ESTADIAMENTO (TRANSAÇÃO)
    # ================================================================
    
    def _salvar_estadiamento_transacao(self, condicao_id: int, sistema: str,
                                      novo_estagio: str, criterios: dict,
                                      exames_suporte: list) -> Optional[Estadiamento]:
        """
        Salva novo Estadiamento em transação atômica.
        
        Args:
            condicao_id: ID da condição
            sistema: Sistema de classificação
            novo_estagio: Novo estágio
            criterios: Critérios de classificação
            exames_suporte: Exames que suportam a classificação
        
        Returns:
            Estadiamento criado ou None em caso de erro
        """
        try:
            estadiamento = Estadiamento(
                condicao_cronica_id=condicao_id,
                sistema_classificacao=sistema,
                estagio=novo_estagio,
                data_classificacao=datetime.now(),
                criterios=criterios,
                exames_suporte=exames_suporte
            )
            
            self.db.add(estadiamento)
            self.db.commit()
            self.db.refresh(estadiamento)
            
            logger.info(f"[ORQU] Estadiamento salvo: {estadiamento.id}")
            return estadiamento
        
        except SQLAlchemyError as e:
            logger.error(f"[ORQU] Erro ao salvar Estadiamento: {str(e)}")
            self.db.rollback()
            return None
    
    # ================================================================
    # 4.2.5: GERAR ALERTA
    # ================================================================
    
    def _gerar_alerta(self, condicao: CondicaoCronica, tipo_alerta: str,
                     severidade: str, descricao: str, 
                     dados_suporte: dict) -> Optional[Alerta]:
        """
        Gera novo alerta baseado em detecção de piora.
        
        Args:
            condicao: CondicaoCronica
            tipo_alerta: DESCONTROLE | PIORA_PROGRESSIVA
            severidade: BAIXA | MEDIA | ALTA | CRITICA
            descricao: Descrição textual
            dados_suporte: Dados contextuais do alerta
        
        Returns:
            Alerta criado ou None
        """
        try:
            alerta = Alerta(
                paciente_cpf_hash=condicao.paciente_cpf_hash,
                condicao_cronica_id=condicao.id,
                tipo_alerta=tipo_alerta,
                severidade=severidade,
                descricao=descricao,
                dados_alerta=dados_suporte,
                status="NOVO",
                data_criacao=datetime.now()
            )
            
            self.db.add(alerta)
            self.db.commit()
            self.db.refresh(alerta)
            
            logger.info(f"[ORQU] Alerta criado: id={alerta.id}, severidade={severidade}")
            return alerta
        
        except SQLAlchemyError as e:
            logger.error(f"[ORQU] Erro ao criar alerta: {str(e)}")
            self.db.rollback()
            return None
    
    # ================================================================
    # 4.2.6: REGISTRAR NO TIMELINE
    # ================================================================
    
    def _registrar_acompanhamento_evento(self, condicao: CondicaoCronica,
                                        evento_tipo: str, 
                                        evento_dados: dict) -> Optional[Acompanhamento]:
        """
        Registra evento no timeline de acompanhamento.
        
        Args:
            condicao: CondicaoCronica
            evento_tipo: Tipo de evento (EXAME_RECLASSIFICACAO, etc)
            evento_dados: Dados do evento
        
        Returns:
            Acompanhamento criado ou None
        """
        try:
            acompanhamento = Acompanhamento(
                paciente_cpf_hash=condicao.paciente_cpf_hash,
                condicao_cronica_id=condicao.id,
                data_acompanhamento=datetime.now(),
                medico_id="SISTEMA_AUTOMATIZADO",
                observacoes=f"{evento_tipo}: {evento_dados}",
                criado_em=datetime.now()
            )
            
            self.db.add(acompanhamento)
            self.db.commit()
            
            logger.info(f"[ORQU] Acompanhamento registrado: {evento_tipo}")
            return acompanhamento
        
        except SQLAlchemyError as e:
            logger.error(f"[ORQU] Erro ao registrar acompanhamento: {str(e)}")
            self.db.rollback()
            return None
    
    # ================================================================
    # HELPERS PRIVADOS
    # ================================================================
    
    def _classificar_novo_valor(self, condicao_cid10: str, 
                               tipo_exame: TipoExame, 
                               valor: float) -> Tuple[str, dict]:
        """
        Usa ClassificacaoService para classificar novo valor.
        
        Returns:
            (novo_estagio, criterios_dict)
        """
        # Mapear tipo de exame para chamada de classificador
        if tipo_exame == TipoExame.GLICEMIA and condicao_cid10 == "E11":
            # Usar classificador de diabetes
            resultado = self.classificacao_svc.classificar_diabetes(glicemia_acaso=valor)
            estagio = resultado.get('controle_glicemico', 'DESCONHECIDO')
            return (estagio, resultado)
        
        elif tipo_exame == TipoExame.PA and condicao_cid10 == "I10":
            # Usar classificador de HAS
            sys_ha = valor
            dias_ha = None
            resultado = self.classificacao_svc.classificar_has(sys_ha, dias_ha)
            estagio = resultado.get('classificacao', 'DESCONHECIDO')
            return (estagio, resultado)
        
        elif tipo_exame == TipoExame.CREATININA and condicao_cid10 == "N18":
            # Usar classificador de DRC
            resultado = self.classificacao_svc.classificar_drc(None, valor)
            estagio = resultado.get('estagio_kdigo', 'DESCONHECIDO')
            return (estagio, resultado)
        
        else:
            logger.warning(f"[ORQU] Classificação não implementada para {tipo_exame}/{condicao_cid10}")
            return ("DESCONHECIDO", {})
    
    def _obter_sistema_classificacao(self, cid10: str) -> str:
        """Mapeia CID-10 para sistema de classificação."""
        mapeamento = {
            "I10": "HAS",
            "E11": "DIABETES",
            "N18": "DRC",
            "E78": "DISLIPIDEMIA"
        }
        return mapeamento.get(cid10, "OUTRO")
    
    def _gerar_alerta_erro(self, operacao: str, erro: str, tipo_erro: str = "PROCESSING_ERROR"):
        """
        Gera alerta automático em caso de erro em operação crítica.
        
        Args:
            operacao: Nome da operação que falhou
            erro: Descrição do erro
            tipo_erro: Tipo de erro (DATABASE_ERROR, PROCESSING_ERROR, VALIDATION_ERROR)
        """
        try:
            logger.warning(f"[ORQU-ALERTA-ERRO] Gerando alerta para operação: {operacao}")
            
            alerta = Alerta(
                paciente_cpf_hash=None,  # Erro sistêmico, sem paciente específico
                condicao_cronica_id=None,
                tipo_alerta="ERRO_SISTEMA",
                severidade="CRITICA",
                titulo=f"Erro em {operacao}",
                descricao=f"Erro {tipo_erro}: {erro[:200]}",  # Truncar erro muito longo
                data_criacao=datetime.now(),
                data_validade=None,  # Sem validade automática
                requer_intervencao_medica=True,
                status_alerta="ABERTO"
            )
            
            self.db.add(alerta)
            self.db.flush()  # Flush para confirmar inserção sem commit
            
            logger.info(f"[ORQU-ALERTA-ERRO] Alerta de erro criado: id={alerta.id}")
            
        except Exception as alert_error:
            logger.error(f"[ORQU-ALERTA-ERRO] Falha ao gerar alerta de erro: {str(alert_error)}")
            # Não re-raise; o erro original é mais importante

