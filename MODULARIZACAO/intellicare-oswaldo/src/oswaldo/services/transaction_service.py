"""
Decorador @transactional e Context Manager para transações atômicas.

Garante ACID properties para operações críticas:
- Automaticamente faz commit em sucesso
- Automaticamente faz rollback em erro
- Gera alerta de erro de processamento
- Rastreia durability e timing
"""

import logging
import time
from functools import wraps
from typing import Callable, Any, Dict, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


class TransactionError(Exception):
    """Exceção customizada para erros de transação."""
    pass


class TransactionContext:
    """Context manager para transações atômicas."""
    
    def __init__(self, db: Session, operation_name: str = ""):
        """
        Args:
            db: Sessão SQLAlchemy
            operation_name: Nome da operação para logging
        """
        self.db = db
        self.operation_name = operation_name
        self.committed = False
        self.rolled_back = False
    
    def __enter__(self):
        """Inicia transação."""
        logger.info(f"[TX] Iniciando transação: {self.operation_name}")
        return self.db
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Finaliza transação com commit ou rollback."""
        
        if exc_type is not None:
            # Erro durante execução
            logger.error(f"[TX] Erro em transação: {self.operation_name}")
            logger.error(f"[TX] Tipo: {exc_type.__name__}, Valor: {exc_val}")
            
            self.db.rollback()
            self.rolled_back = True
            logger.warning(f"[TX] Rollback executado para: {self.operation_name}")
            
            # Re-raise a exception
            return False
        
        else:
            # Sucesso
            try:
                self.db.commit()
                self.committed = True
                logger.info(f"[TX] Commit executado: {self.operation_name}")
                return True
            
            except SQLAlchemyError as e:
                logger.error(f"[TX] Erro ao fazer commit: {str(e)}")
                self.db.rollback()
                self.rolled_back = True
                raise TransactionError(f"Falha ao fazer commit: {str(e)}")


def transactional(operation_name: str = "", generate_error_alert: bool = True):
    """
    Decorador para operações que requerem transações atômicas.
    
    Uso:
    ```python
    @transactional(operation_name="processar_exame")
    def processar_exame_novo(self, event: ExameResultadoEvent) -> Dict:
        # Operações aqui
        # Commit/Rollback automático
        return resultado
    ```
    
    Args:
        operation_name: Nome da operação para logging
        generate_error_alert: Se True, gera alerta em caso de erro
    
    Returns:
        Função decorada com transação automática
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, *args, **kwargs) -> Any:
            # Obter nome da operação
            op_name = operation_name or f"{self.__class__.__name__}.{func.__name__}"
            
            # Criar context manager
            with TransactionContext(self.db, op_name) as db:
                try:
                    logger.info(f"[TX] Executando: {op_name}")
                    result = func(self, *args, **kwargs)
                    logger.info(f"[TX] Sucesso: {op_name}")
                    return result
                
                except SQLAlchemyError as e:
                    logger.error(f"[TX] SQLAlchemy erro em {op_name}: {str(e)}")
                    
                    # Gerar alerta de erro se habilitado
                    if generate_error_alert and hasattr(self, '_gerar_alerta_erro'):
                        try:
                            self._gerar_alerta_erro(
                                operacao=op_name,
                                erro=str(e),
                                tipo_erro="DATABASE_ERROR"
                            )
                        except Exception as alert_error:
                            logger.error(f"[TX] Falha ao gerar alerta de erro: {alert_error}")
                    
                    raise TransactionError(f"Erro de banco em {op_name}: {str(e)}")
                
                except Exception as e:
                    logger.error(f"[TX] Erro geral em {op_name}: {str(e)}")
                    
                    # Gerar alerta de erro
                    if generate_error_alert and hasattr(self, '_gerar_alerta_erro'):
                        try:
                            self._gerar_alerta_erro(
                                operacao=op_name,
                                erro=str(e),
                                tipo_erro="PROCESSING_ERROR"
                            )
                        except Exception as alert_error:
                            logger.error(f"[TX] Falha ao gerar alerta de erro: {alert_error}")
                    
                    raise
        
        return wrapper
    return decorator


class TransactionalBatch:
    """Context manager para executar múltiplas operações em uma transação."""
    
    def __init__(self, db: Session, batch_name: str = ""):
        """
        Args:
            db: Sessão SQLAlchemy
            batch_name: Nome do lote para logging
        """
        self.db = db
        self.batch_name = batch_name
        self.result_count = 0
        self.error_count = 0
    
    def __enter__(self):
        """Inicia transação para lote."""
        logger.info(f"[TX-BATCH] Iniciando lote: {self.batch_name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Finaliza lote com commit ou rollback."""
        
        if exc_type is not None:
            logger.error(f"[TX-BATCH] Erro no lote: {self.batch_name}")
            self.db.rollback()
            logger.warning(f"[TX-BATCH] Rollback: {self.batch_name} "
                          f"({self.result_count} registros cancelados)")
            return False
        
        else:
            try:
                self.db.commit()
                logger.info(f"[TX-BATCH] Commit: {self.batch_name} "
                           f"({self.result_count} registros confirmados)")
                return True
            
            except SQLAlchemyError as e:
                logger.error(f"[TX-BATCH] Erro ao fazer commit: {str(e)}")
                self.db.rollback()
                raise TransactionError(f"Falha commit lote {self.batch_name}: {str(e)}")
    
    def add_result(self):
        """Incrementa contador de resultados bem-sucedidos."""
        self.result_count += 1
    
    def add_error(self):
        """Incrementa contador de erros."""
        self.error_count += 1
    
    def get_summary(self) -> Dict:
        """Retorna resumo do lote."""
        return {
            'batch_name': self.batch_name,
            'succeeded': self.result_count,
            'failed': self.error_count,
            'total': self.result_count + self.error_count,
            'success_rate': (self.result_count / (self.result_count + self.error_count) 
                            if (self.result_count + self.error_count) > 0 else 0)
        }


# Retry decorador para operações flaky
def retry_on_transient_error(max_retries: int = 3, delay_seconds: float = 0.5):
    """
    Decorador para retry em erros transitórios (deadlock, timeout, etc).
    
    Args:
        max_retries: Número máximo de tentativas
        delay_seconds: Delay entre retries em segundos
    
    Returns:
        Função decorada com retry automático
    """
    import time
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_error = None
            
            for attempt in range(1, max_retries + 1):
                try:
                    logger.info(f"[RETRY] Tentativa {attempt}/{max_retries} para {func.__name__}")
                    return func(*args, **kwargs)
                
                except SQLAlchemyError as e:
                    # Verificar se é erro transitório
                    error_str = str(e).lower()
                    is_transient = any(x in error_str for x in [
                        'deadlock',
                        'timeout',
                        'connection reset',
                        'too many connections',
                        'transient'
                    ])
                    
                    if not is_transient or attempt == max_retries:
                        logger.error(f"[RETRY] Erro permanent ou último retry: {error_str}")
                        raise
                    
                    last_error = e
                    logger.warning(f"[RETRY] Erro transiente, aguardando {delay_seconds}s...")
                    time.sleep(delay_seconds)
                
                except Exception as e:
                    logger.error(f"[RETRY] Erro não-transitório: {str(e)}")
                    raise
            
            # Fallback (não deve chegar aqui)


class TransactionWithAlertIntegration:
    """Integração de Transações com Sistema de Alertas."""
    
    def __init__(self, db: Session):
        """
        Args:
            db: Sessão SQLAlchemy
        """
        self.db = db
        self.alerts_table = None
        self._init_alerts_table()
    
    def _init_alerts_table(self):
        """Inicializa acesso à tabela de alertas."""
        try:
            from src.oswaldo.models.oswaldo_models import Alerta
            self.alerts_table = Alerta
        except ImportError:
            logger.warning("[TX-ALERTS] Tabela de Alertas não disponível")
    
    def gerar_alerta_erro_transacao(
        self,
        operacao: str,
        erro: str,
        tipo_erro: str = "TRANSACTION_ERROR",
        paciente_cpf_hash: Optional[str] = None,
        condicao_id: Optional[int] = None
    ) -> Optional[int]:
        """
        Gera alerta quando transação falha.
        
        Args:
            operacao: Nome da operação que falhou
            erro: Descrição do erro
            tipo_erro: Tipo de erro (DATABASE_ERROR, PROCESSING_ERROR, VALIDATION_ERROR)
            paciente_cpf_hash: CPF do paciente (opcional)
            condicao_id: ID da condição (opcional)
        
        Returns:
            ID do alerta gerado ou None se falhar
        """
        if not self.alerts_table:
            logger.error("[TX-ALERTS] Não é possível gerar alerta (tabela indisponível)")
            return None
        
        try:
            # Usar paciente_cpf_hash padrão se não fornecido
            cpf = paciente_cpf_hash or "SISTEMA"
            cond_id = condicao_id or 1  # ID padrão para alertas de sistema
            
            alerta = self.alerts_table(
                paciente_cpf_hash=cpf,
                condicao_cronica_id=cond_id,
                tipo_alerta="ERRO_PROCESSAMENTO",
                severidade="MEDIA" if "validation" in tipo_erro.lower() else "ALTA",
                descricao=f"Erro em {operacao}: {erro[:200]}",
                dados_alerta={
                    'operacao': operacao,
                    'tipo_erro': tipo_erro,
                    'erro_completo': erro,
                    'timestamp': datetime.now().isoformat()
                },
                status="NOVO"
            )
            
            self.db.add(alerta)
            self.db.commit()
            
            logger.info(f"[TX-ALERTS] Alerta de erro gerado: {alerta.id} para {operacao}")
            return alerta.id
        
        except Exception as e:
            logger.error(f"[TX-ALERTS] Falha ao gerar alerta: {str(e)}")
            return None
    
    def registrar_transacao(
        self,
        operacao: str,
        status: str,
        tempo_ms: float,
        mensagem: str = ""
    ) -> Dict:
        """
        Registra informações de durability de transação.
        
        Args:
            operacao: Nome da operação
            status: "COMMIT" ou "ROLLBACK"
            tempo_ms: Tempo da operação em milissegundos
            mensagem: Mensagem adicional
        
        Returns:
            Dicionário com informações da transação
        """
        registro = {
            'operacao': operacao,
            'status': status,
            'tempo_ms': tempo_ms,
            'timestamp': datetime.now().isoformat(),
            'mensagem': mensagem,
            'duravel': status == "COMMIT"
        }
        
        log_level = logging.INFO if status == "COMMIT" else logging.WARNING
        logger.log(
            log_level,
            f"[TX-DURABILITY] {operacao}: {status} em {tempo_ms:.2f}ms"
        )
        
        return registro


def transactional_with_alerts(
    operation_name: str = "", 
    generate_error_alert: bool = True,
    track_timing: bool = True
):
    """
    Decorador avançado para operações com transações atômicas e alertas de erro.
    
    Recursos adicionais:
    - Registra timing de transações
    - Gera alertas em caso de erro
    - Tracking de durability
    
    Args:
        operation_name: Nome da operação para logging
        generate_error_alert: Se True, gera alerta em caso de erro
        track_timing: Se True, registra timing e durability
    
    Returns:
        Função decorada
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, *args, **kwargs) -> Any:
            op_name = operation_name or f"{self.__class__.__name__}.{func.__name__}"
            start_time = time.time() if track_timing else None
            
            with TransactionContext(self.db, op_name) as db:
                try:
                    logger.info(f"[TX-ADVANCED] Executando: {op_name}")
                    result = func(self, *args, **kwargs)
                    
                    if track_timing and start_time:
                        elapsed_ms = (time.time() - start_time) * 1000
                        if hasattr(self, '_tx_alert_service'):
                            self._tx_alert_service.registrar_transacao(
                                op_name, "COMMIT", elapsed_ms
                            )
                        logger.info(f"[TX-ADVANCED] {op_name} completado em {elapsed_ms:.2f}ms")
                    
                    return result
                
                except Exception as e:
                    if track_timing and start_time:
                        elapsed_ms = (time.time() - start_time) * 1000
                    else:
                        elapsed_ms = 0
                    
                    logger.error(f"[TX-ADVANCED] Erro em {op_name}: {str(e)}")
                    
                    if generate_error_alert and hasattr(self, '_tx_alert_service'):
                        try:
                            self._tx_alert_service.gerar_alerta_erro_transacao(
                                operacao=op_name,
                                erro=str(e),
                                tipo_erro="DATABASE_ERROR" if isinstance(e, SQLAlchemyError) 
                                         else "PROCESSING_ERROR"
                            )
                        except Exception as alert_error:
                            logger.error(f"[TX-ADVANCED] Falha ao gerar alerta: {alert_error}")
                    
                    if track_timing:
                        if hasattr(self, '_tx_alert_service'):
                            self._tx_alert_service.registrar_transacao(
                                op_name, "ROLLBACK", elapsed_ms,
                                mensagem=str(e)[:100]
                            )
                    
                    raise
        
        return wrapper
    return decorator
