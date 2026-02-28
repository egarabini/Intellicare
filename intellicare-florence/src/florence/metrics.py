"""
Florence Prometheus Metrics
===========================

Métricas para coleta de telemetria e monitoramento de Florence.
Integração com Prometheus para scraping a cada 15s.
"""

from prometheus_client import Counter, Histogram, Gauge
import time
from functools import wraps
from typing import Callable


# ============================================================================
# Contadores (Counter) - Sempre aumentam
# ============================================================================

validacoes_total = Counter(
    'florence_validacoes_total',
    'Total de validações executadas',
    ['tipo_exame', 'resultado']  # resultado: 'valido' | 'invalido'
)

validacoes_erros = Counter(
    'florence_validacoes_erros_total',
    'Total de erros nas validações',
    ['tipo_exame', 'tipo_erro']
)

eventos_publicados = Counter(
    'florence_eventos_publicados_total',
    'Total de eventos publicados em RabbitMQ',
    ['tipo_evento']  # exame_critico, exame_created, alerta_novo
)

pacientes_anonimizados = Counter(
    'florence_pacientes_anonimizados_total',
    'Total de pacientes anonimizados'
)

acessos_pii = Counter(
    'florence_acessos_pii_total',
    'Total de acessos a dados PII (com auditoria)',
    ['usuario_id', 'resultado']  # resultado: 'sucesso' | 'falha'
)


# ============================================================================
# Histogramas (Histogram) - Distribuição de latência
# ============================================================================

latencia_validacao = Histogram(
    'florence_validacao_latencia_segundos',
    'Latência de validação em segundos',
    ['tipo_exame'],
    buckets=(0.001, 0.005, 0.010, 0.025, 0.050, 0.100, 0.250, 0.500)
    # buckets: 1ms, 5ms, 10ms, 25ms, 50ms, 100ms, 250ms, 500ms
)

latencia_anonimizacao = Histogram(
    'florence_anonimizacao_latencia_segundos',
    'Latência de anonimização em segundos',
    ['operacao'],  # criar_paciente, recuperar_cpf, listar_acessos
    buckets=(0.001, 0.005, 0.010, 0.050, 0.100, 0.500, 1.0)
)

latencia_api = Histogram(
    'florence_api_latencia_segundos',
    'Latência de endpoints API',
    ['endpoint', 'metodo', 'status'],
    buckets=(0.001, 0.010, 0.050, 0.100, 0.250, 0.500, 1.0)
)

latencia_evento = Histogram(
    'florence_evento_publicacao_latencia_segundos',
    'Latência de publicação de eventos',
    ['tipo_evento'],
    buckets=(0.001, 0.010, 0.050, 0.100)
)


# ============================================================================
# Medidores (Gauge) - Valores instantâneos
# ============================================================================

validacoes_em_progresso = Gauge(
    'florence_validacoes_em_progresso',
    'Validações em progresso neste momento',
    ['tipo_exame']
)

pacientes_anonimizados_ativos = Gauge(
    'florence_pacientes_anonimizados_ativos',
    'Total de pacientes com anonimização ativa (não deletados)'
)

erros_rabbitmq = Gauge(
    'florence_erros_rabbitmq',
    'Contador de erros de conexão RabbitMQ (reset periodicamente)'
)

tamanho_fila_retentativa = Gauge(
    'florence_fila_retentativa_tamanho',
    'Tamanho da fila de retentativa para eventos failed'
)

eventos_fila = Gauge(
    'florence_eventos_em_fila',
    'Eventos aguardando publicação',
    ['tipo_evento']
)


# ============================================================================
# Decoradores para instrumentação automática
# ============================================================================

def medir_validacao(tipo_exame: str) -> Callable:
    """
    Decorator para medir latência de validação.
    
    Uso:
        @medir_validacao('hemograma')
        def validar_hemograma(dados):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            validacoes_em_progresso.labels(tipo_exame=tipo_exame).inc()
            
            try:
                start = time.time()
                resultado = func(*args, **kwargs)
                latencia = time.time() - start
                
                latencia_validacao.labels(tipo_exame=tipo_exame).observe(latencia)
                
                # Resultado: válido ou inválido
                result_label = 'valido' if resultado[0] else 'invalido'
                validacoes_total.labels(tipo_exame=tipo_exame, resultado=result_label).inc()
                
                return resultado
                
            except Exception as e:
                validacoes_erros.labels(
                    tipo_exame=tipo_exame,
                    tipo_erro=type(e).__name__
                ).inc()
                raise
            finally:
                validacoes_em_progresso.labels(tipo_exame=tipo_exame).dec()
        
        return wrapper
    return decorator


def medir_anonimizacao(operacao: str) -> Callable:
    """
    Decorator para medir latência de anonimização.
    
    Uso:
        @medir_anonimizacao('criar_paciente')
        def criar_paciente_anonimizado(...):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            try:
                resultado = func(*args, **kwargs)
                latencia = time.time() - start
                latencia_anonimizacao.labels(operacao=operacao).observe(latencia)
                return resultado
            except Exception as e:
                latencia = time.time() - start
                latencia_anonimizacao.labels(operacao=operacao).observe(latencia)
                raise
        
        return wrapper
    return decorator


def medir_api(endpoint: str, metodo: str) -> Callable:
    """
    Decorator para medir latência de endpoints API.
    
    Uso:
        @medir_api('/api/v1/validacao/validador-clinico', 'POST')
        def validador_clinico(request):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            try:
                resultado = func(*args, **kwargs)
                latencia = time.time() - start
                
                status = getattr(resultado, 'status_code', 200) if hasattr(resultado, 'status_code') else 200
                latencia_api.labels(endpoint=endpoint, metodo=metodo, status=status).observe(latencia)
                
                return resultado
            except Exception as e:
                latencia = time.time() - start
                latencia_api.labels(endpoint=endpoint, metodo=metodo, status=500).observe(latencia)
                raise
        
        return wrapper
    return decorator


def medir_evento(tipo_evento: str) -> Callable:
    """
    Decorator para medir latência de publicação de eventos.
    
    Uso:
        @medir_evento('exame_critico')
        def publicar_exame_critico(...):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            try:
                resultado = func(*args, **kwargs)
                latencia = time.time() - start
                latencia_evento.labels(tipo_evento=tipo_evento).observe(latencia)
                
                if resultado:
                    eventos_publicados.labels(tipo_evento=tipo_evento).inc()
                return resultado
            except Exception as e:
                latencia = time.time() - start
                latencia_evento.labels(tipo_evento=tipo_evento).observe(latencia)
                raise
        
        return wrapper
    return decorator


# ============================================================================
# Funções auxiliares
# ============================================================================

def registrar_anonimizacao():
    """Incrementa contador de pacientes anonimizados"""
    pacientes_anonimizados.inc()
    pacientes_anonimizados_ativos.inc()


def remover_anonimizacao():
    """Decrementa contador de pacientes ativos (soft-delete)"""
    pacientes_anonimizados_ativos.dec()


def registrar_acesso_pii(usuario_id: str, resultado: str):
    """
    Registra acesso a dados PII para auditoria.
    
    Args:
        usuario_id: ID do usuário que acessou
        resultado: 'sucesso' ou 'falha'
    """
    acessos_pii.labels(usuario_id=usuario_id, resultado=resultado).inc()


def atualizar_fila_eventos(tipo_evento: str, tamanho: int):
    """
    Atualiza tamanho da fila de eventos aguardando publicação.
    
    Args:
        tipo_evento: exame_critico, exame_created, alerta_novo
        tamanho: Novo tamanho da fila
    """
    eventos_fila.labels(tipo_evento=tipo_evento).set(tamanho)


# ============================================================================
# Teste/Demo
# ============================================================================

if __name__ == "__main__":
    # Simular algumas métricas
    
    # Validação bem-sucedida
    validacoes_total.labels(tipo_exame='hemograma', resultado='valido').inc()
    latencia_validacao.labels(tipo_exame='hemograma').observe(0.025)
    
    # Validação com falha
    validacoes_total.labels(tipo_exame='glicemia', resultado='invalido').inc()
    latencia_validacao.labels(tipo_exame='glicemia').observe(0.030)
    
    # Evento publicado
    eventos_publicados.labels(tipo_evento='exame_critico').inc()
    latencia_evento.labels(tipo_evento='exame_critico').observe(0.015)
    
    # Anonimização
    registrar_anonimizacao()
    pacientes_anonimizados.inc()
    
    print("✅ Métricas Prometheus registradas com sucesso")
    print("\nPara expor métricas em /metrics:")
    print("  from prometheus_client import start_http_server")
    print("  start_http_server(8000)  # Port 8000 para Prometheus scraping")
