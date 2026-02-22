"""
Prometheus metrics para RabbitMQ Consumer e Publisher.

Coleta:
- events_received: contador de eventos recebidos
- events_processed: contador de eventos processados com sucesso
- events_failed: contador de eventos com erro
- processing_latency_seconds: histograma de latência de processamento
- published_events: contador de eventos publicados
- publish_errors: contador de erros ao publicar
"""

from prometheus_client import Counter, Histogram, Gauge
import functools
import time
import logging

logger = logging.getLogger(__name__)


# ========================================
# CONSUMER METRICS
# ========================================

# Eventos recebidos do RabbitMQ
events_received = Counter(
    'oswaldo_events_received_total',
    'Total de eventos recebidos do RabbitMQ',
    ['event_type'],
    registry=None  # Use default registry
)

# Eventos processados com sucesso
events_processed = Counter(
    'oswaldo_events_processed_total',
    'Total de eventos processados com sucesso',
    ['event_type', 'handler'],
    registry=None
)

# Eventos com erro
events_failed = Counter(
    'oswaldo_events_failed_total',
    'Total de eventos com erro',
    ['event_type', 'error_type'],
    registry=None
)

# Latência de processamento (segundos)
processing_latency = Histogram(
    'oswaldo_event_processing_latency_seconds',
    'Latência de processamento de eventos (segundos)',
    ['event_type'],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0),
    registry=None
)

# Queue depth (eventos pendentes)
queue_depth = Gauge(
    'oswaldo_queue_depth',
    'Número de eventos na fila',
    ['queue_name'],
    registry=None
)

# Connection status
connection_status = Gauge(
    'oswaldo_consumer_connection_status',
    'Status da conexão ao RabbitMQ (1=conectado, 0=desconectado)',
    registry=None
)


# ========================================
# PUBLISHER METRICS
# ========================================

# Eventos publicados
events_published = Counter(
    'oswaldo_events_published_total',
    'Total de eventos publicados',
    ['event_type'],
    registry=None
)

# Erros ao publicar
publish_errors = Counter(
    'oswaldo_publish_errors_total',
    'Total de erros ao publicar eventos',
    ['event_type', 'error_type'],
    registry=None
)

# Latência de publicação
publish_latency = Histogram(
    'oswaldo_event_publish_latency_seconds',
    'Latência de publicação de eventos (segundos)',
    ['event_type'],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0),
    registry=None
)


# ========================================
# DECORATORS
# ========================================

def track_event_processing(event_type: str):
    """
    Decorator para rastrear processamento de eventos.
    
    Coleta:
    - events_received: +1
    - processing_latency: latência do handler
    - events_processed ou events_failed: +1
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Incrementar eventos recebidos
            events_received.labels(event_type=event_type).inc()
            
            # Medir latência
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                
                # Sucesso: registrar latência e incrementar contador
                latency = time.time() - start_time
                processing_latency.labels(event_type=event_type).observe(latency)
                events_processed.labels(
                    event_type=event_type,
                    handler=func.__name__
                ).inc()
                
                logger.debug(f"[Metrics] {event_type} processado em {latency:.3f}s")
                return result
                
            except Exception as e:
                # Erro: registrar latência e incrementar contador de falhas
                latency = time.time() - start_time
                processing_latency.labels(event_type=event_type).observe(latency)
                
                error_type = type(e).__name__
                events_failed.labels(
                    event_type=event_type,
                    error_type=error_type
                ).inc()
                
                logger.error(f"[Metrics] {event_type} falhou após {latency:.3f}s: {error_type}")
                raise
        
        return wrapper
    return decorator


def track_event_publishing(event_type: str):
    """
    Decorator para rastrear publicação de eventos.
    
    Coleta:
    - publish_latency: latência de publicação
    - events_published ou publish_errors: +1
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                
                # Sucesso: registrar latência e incrementar contador
                latency = time.time() - start_time
                publish_latency.labels(event_type=event_type).observe(latency)
                events_published.labels(event_type=event_type).inc()
                
                logger.debug(f"[Metrics] {event_type} publicado em {latency:.3f}s")
                return result
                
            except Exception as e:
                # Erro: registrar latência e incrementar contador de falhas
                latency = time.time() - start_time
                error_type = type(e).__name__
                publish_errors.labels(
                    event_type=event_type,
                    error_type=error_type
                ).inc()
                
                logger.error(f"[Metrics] {event_type} falhou ao publicar após {latency:.3f}s: {error_type}")
                raise
        
        return wrapper
    return decorator


# ========================================
# UTILITY FUNCTIONS
# ========================================

def set_connection_status(connected: bool):
    """Atualizar status de conexão ao RabbitMQ."""
    connection_status.set(1 if connected else 0)
    logger.info(f"[Metrics] Connection status: {'CONNECTED' if connected else 'DISCONNECTED'}")


def set_queue_depth(queue_name: str, depth: int):
    """Atualizar profundidade de fila."""
    queue_depth.labels(queue_name=queue_name).set(depth)
    logger.debug(f"[Metrics] {queue_name} queue_depth={depth}")


def get_metrics_summary():
    """
    Retornar resumo de métricas para logging/debug.
    
    Returns:
        dict com contadores principais
    """
    return {
        "events_received_total": sum(m.value for m in events_received.collect()[0].samples if m.name == 'oswaldo_events_received_total'),
        "events_processed_total": sum(m.value for m in events_processed.collect()[0].samples if m.name == 'oswaldo_events_processed_total'),
        "events_failed_total": sum(m.value for m in events_failed.collect()[0].samples if m.name == 'oswaldo_events_failed_total'),
        "events_published_total": sum(m.value for m in events_published.collect()[0].samples if m.name == 'oswaldo_events_published_total'),
        "publish_errors_total": sum(m.value for m in publish_errors.collect()[0].samples if m.name == 'oswaldo_publish_errors_total'),
    }
