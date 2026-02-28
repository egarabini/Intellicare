"""
RabbitMQ Publisher para Oswaldo.

Publica eventos gerados por Oswaldo:
- Diagnóstico sugerido
- Alerta gerado
- Plano de cuidado criado
"""

import pika
import json
import logging
from typing import Dict, Any
from datetime import datetime

from src.oswaldo.integrations.metrics import track_event_publishing

logger = logging.getLogger(__name__)


class OswaldoRabbitMQPublisher:
    """
    Publisher RabbitMQ para publicar eventos gerados por Oswaldo.
    
    Usa exchange: oswaldo.events (topic exchange)
    Routing keys:
    - oswaldo.diagnostico (novo diagnóstico)
    - oswaldo.alerta (alerta clínico)
    - oswaldo.plano_cuidado (novo plano)
    """
    
    def __init__(self, host: str = "localhost", port: int = 5672,
                 vhost: str = "/", username: str = "guest", password: str = "guest"):
        """Inicializar publisher."""
        self.host = host
        self.port = port
        self.credentials = pika.PlainCredentials(username, password)
        self.connection = None
        self.channel = None
    
    def connect(self):
        """Conectar ao RabbitMQ."""
        try:
            params = pika.ConnectionParameters(
                host=self.host,
                port=self.port,
                virtual_host=self.vhost,
                credentials=self.credentials,
                connection_attempts=3,
                retry_delay=2
            )
            self.connection = pika.BlockingConnection(params)
            self.channel = self.connection.channel()
            
            # Declarar exchange
            self.channel.exchange_declare(
                exchange="oswaldo.events",
                exchange_type="topic",
                durable=True
            )
            
            logger.info(f"[Publisher] Conectado em {self.host}:{self.port}")
            
        except Exception as e:
            logger.error(f"[Publisher] Erro ao conectar: {e}")
            raise
    
    def publish_diagnostico(self, paciente_cpf_hash: str, cid10: str, 
                           score: float, medico_responsavel: str = None):
        """Publicar novo diagnóstico sugerido."""
        return self._publish_diagnostico_impl(paciente_cpf_hash, cid10, score, medico_responsavel)
    
    @track_event_publishing("diagnostico")
    def _publish_diagnostico_impl(self, paciente_cpf_hash: str, cid10: str, 
                                  score: float, medico_responsavel: str = None):
        """Implementação de publicação de diagnóstico (com metrics)."""
        
        event = {
            "event_type": "oswaldo_diagnostico",
            "paciente_cpf_hash": paciente_cpf_hash,
            "cid10": cid10,
            "score_confianca": score,
            "medico_responsavel": medico_responsavel,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self._publish(event, routing_key="oswaldo.diagnostico")
    
    def publish_alerta(self, paciente_cpf_hash: str, tipo_alerta: str,
                       severidade: str, descricao: str):
        """Publicar novo alerta clínico."""
        return self._publish_alerta_impl(paciente_cpf_hash, tipo_alerta, severidade, descricao)
    
    @track_event_publishing("alerta")
    def _publish_alerta_impl(self, paciente_cpf_hash: str, tipo_alerta: str,
                             severidade: str, descricao: str):
        """Implementação de publicação de alerta (com metrics)."""
        
        event = {
            "event_type": "oswaldo_alerta",
            "paciente_cpf_hash": paciente_cpf_hash,
            "tipo_alerta": tipo_alerta,
            "severidade": severidade,
            "descricao": descricao,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self._publish(event, routing_key="oswaldo.alerta")
    
    def publish_plano_cuidado(self, paciente_cpf_hash: str, condicao_cid10: str,
                              objetivos: list, intervencoes: list):
        """Publicar novo plano de cuidado criado."""
        return self._publish_plano_cuidado_impl(paciente_cpf_hash, condicao_cid10, objetivos, intervencoes)
    
    @track_event_publishing("plano_cuidado")
    def _publish_plano_cuidado_impl(self, paciente_cpf_hash: str, condicao_cid10: str,
                                    objetivos: list, intervencoes: list):
        """Implementação de publicação de plano (com metrics)."""
        
        event = {
            "event_type": "oswaldo_plano_cuidado",
            "paciente_cpf_hash": paciente_cpf_hash,
            "condicao_cid10": condicao_cid10,
            "objetivos": objetivos,
            "intervencoes": intervencoes,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self._publish(event, routing_key="oswaldo.plano_cuidado")
    
    def _publish(self, event: Dict[str, Any], routing_key: str):
        """Publicar evento genérico."""
        try:
            if not self.connection:
                self.connect()
            
            message = json.dumps(event, default=str)
            
            self.channel.basic_publish(
                exchange="oswaldo.events",
                routing_key=routing_key,
                body=message,
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Persistent
                    content_type="application/json"
                )
            )
            
            logger.info(f"[Publish] {routing_key}: {event.get('event_type')}")
            
        except Exception as e:
            logger.error(f"[Publish] Erro ao publicar: {e}", exc_info=True)
            raise
    
    def close(self):
        """Fechar conexão."""
        if self.connection:
            self.connection.close()
            logger.info("[Publisher] Desconectado")


# Publisher singleton para uso em toda aplicação
_publisher_instance = None


def get_publisher() -> OswaldoRabbitMQPublisher:
    """Obter instância do publisher (singleton)."""
    global _publisher_instance
    if _publisher_instance is None:
        _publisher_instance = OswaldoRabbitMQPublisher()
    return _publisher_instance
