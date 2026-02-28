"""
RabbitMQ Consumer para Oswaldo.

Recebe eventos do Florence para:
1. Novos exames → Reclassificar e gerar alertas
2. Dados do paciente → Atualizar contexto
3. Solicitação de consulta → Gerar agendamento
"""

import pika
import json
import logging
from typing import Callable, Dict, Any
from datetime import datetime
import threading

from src.oswaldo.integrations.event_models import (
    ExameResultadoEvent,
    PacienteDadosEvent,
    RequestConsultaEvent
)
from src.oswaldo.integrations.metrics import (
    set_connection_status,
    track_event_processing
)

logger = logging.getLogger(__name__)


class FlorenzeRabbitMQConsumer:
    """
    Consumer RabbitMQ para processar eventos do Florence.
    
    Connection: localhost:5672 (RabbitMQ server)
    Queue: oswaldo.events (durável, persistent)
    Prefetch: 1 (processa um evento por vez)
    """
    
    def __init__(self, host: str = "localhost", port: int = 5672, 
                 vhost: str = "/", username: str = "guest", password: str = "guest"):
        """Inicializar consumer."""
        self.host = host
        self.port = port
        self.vhost = vhost
        self.credentials = pika.PlainCredentials(username, password)
        self.connection = None
        self.channel = None
        self.running = False
        
        # Event handlers
        self.handlers: Dict[str, Callable] = {}
        
        # Métricas
        self.metrics = {
            "events_received": 0,
            "events_processed": 0,
            "events_failed": 0,
            "last_processed": None
        }
        
    def connect(self):
        """Conectar ao RabbitMQ."""
        try:
            params = pika.ConnectionParameters(
                host=self.host,
                port=self.port,
                virtual_host=self.vhost,
                credentials=self.credentials,
                connection_attempts=3,
                retry_delay=2,
                heartbeat=600,
                blocked_connection_timeout=300
            )
            self.connection = pika.BlockingConnection(params)
            self.channel = self.connection.channel()
            logger.info(f"[RabbitMQ] Conectado em {self.host}:{self.port}")
            
            # Atualizar status de conexão nas métricas
            set_connection_status(True)
            
            # Definir QoS: processar um evento por vez
            self.channel.basic_qos(prefetch_count=1)
            
        except Exception as e:
            logger.error(f"[RabbitMQ] Erro ao conectar: {e}")
            set_connection_status(False)
            raise
    
    def setup_exchanges_and_queues(self):
        """Declarar exchanges e queues."""
        try:
            # Exchange: florence.events (topic exchange)
            self.channel.exchange_declare(
                exchange="florence.events",
                exchange_type="topic",
                durable=True
            )
            
            # Queue: oswaldo.exame_resultado
            self.channel.queue_declare(
                queue="oswaldo.exame_resultado",
                durable=True
            )
            self.channel.queue_bind(
                exchange="florence.events",
                queue="oswaldo.exame_resultado",
                routing_key="florence.exame_resultado"
            )
            
            # Queue: oswaldo.paciente_dados
            self.channel.queue_declare(
                queue="oswaldo.paciente_dados",
                durable=True
            )
            self.channel.queue_bind(
                exchange="florence.events",
                queue="oswaldo.paciente_dados",
                routing_key="florence.paciente_dados"
            )
            
            # Queue: oswaldo.request_consulta
            self.channel.queue_declare(
                queue="oswaldo.request_consulta",
                durable=True
            )
            self.channel.queue_bind(
                exchange="florence.events",
                queue="oswaldo.request_consulta",
                routing_key="florence.request_consulta"
            )
            
            logger.info("[RabbitMQ] Exchanges e queues declarados")
            
        except Exception as e:
            logger.error(f"[RabbitMQ] Erro ao declarar queues: {e}")
            raise
    
    def register_handler(self, event_type: str, handler: Callable):
        """Registrar handler para um tipo de event."""
        self.handlers[event_type] = handler
        logger.info(f"[Handler] Registrado para {event_type}")
    
    def _process_message(self, ch, method, properties, body):
        """Processar mensagem recebida."""
        try:
            self.metrics["events_received"] += 1
            
            # Parsear JSON
            event_data = json.loads(body)
            logger.debug(f"[Event] Recebido: {event_data.get('event_type')}")
            
            # Determinar tipo de evento
            event_type = event_data.get("event_type")
            
            if event_type not in self.handlers:
                logger.warning(f"[Event] Nenhum handler para: {event_type}")
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return
            
            # Chamar handler
            handler = self.handlers[event_type]
            handler(event_data)
            
            # Marcar como processado
            ch.basic_ack(delivery_tag=method.delivery_tag)
            self.metrics["events_processed"] += 1
            self.metrics["last_processed"] = datetime.utcnow().isoformat()
            logger.info(f"[Event] Processado: {event_type}")
            
        except json.JSONDecodeError as e:
            logger.error(f"[Event] Erro ao parsear JSON: {e}")
            self.metrics["events_failed"] += 1
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            
        except Exception as e:
            logger.error(f"[Event] Erro ao processar: {e}", exc_info=True)
            self.metrics["events_failed"] += 1
            # Requeue se não for erro de parsing
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
    
    def start_consuming(self):
        """Iniciar consumo de eventos."""
        if not self.connection:
            self.connect()
        
        if not self.handlers:
            logger.warning("[Consumer] Nenhum handler registrado!")
            return
        
        self.running = True
        
        # Consumir de todas as 3 queues
        queues = [
            "oswaldo.exame_resultado",
            "oswaldo.paciente_dados",
            "oswaldo.request_consulta"
        ]
        
        for queue in queues:
            self.channel.basic_consume(
                queue=queue,
                on_message_callback=self._process_message
            )
        
        logger.info("[Consumer] Iniciando consumo de eventos...")
        
        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            self.stop_consuming()
    
    def stop_consuming(self):
        """Parar de consumir eventos."""
        if self.channel:
            self.channel.stop_consuming()
        if self.connection:
            self.connection.close()
        self.running = False
        logger.info("[Consumer] Parado")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Obter métricas de consumo."""
        return {
            **self.metrics,
            "status": "running" if self.running else "stopped",
            "connected": self.connection is not None
        }


def start_consumer_in_background(consumer: FlorenzeRabbitMQConsumer) -> threading.Thread:
    """
    Inicia o consumer em uma thread background.
    
    Retorna a thread para poder fazer join() mais tarde.
    """
    thread = threading.Thread(
        target=consumer.start_consuming,
        name="FlorenzeConsumer",
        daemon=True
    )
    thread.start()
    logger.info("[Thread] Consumer iniciado em background")
    return thread
