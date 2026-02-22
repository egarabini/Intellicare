"""
Integrações de Oswaldo com outros módulos (Florence, etc).

Inclui:
- RabbitMQ Consumer para eventos do Florence
- Event models para validação
- Publishers para publicar eventos de Oswaldo
"""

from src.oswaldo.integrations.rabbitmq_consumer import (
    FlorenzeRabbitMQConsumer,
    start_consumer_in_background
)
from src.oswaldo.integrations.event_models import (
    ExameResultadoEvent,
    PacienteDadosEvent,
    RequestConsultaEvent,
    FlorenzeEvent
)
from src.oswaldo.integrations.event_handlers import FlorenzeEventHandlers

__all__ = [
    "FlorenzeRabbitMQConsumer",
    "start_consumer_in_background",
    "ExameResultadoEvent",
    "PacienteDadosEvent",
    "RequestConsultaEvent",
    "FlorenzeEvent",
    "FlorenzeEventHandlers",
]
