"""Métricas Prometheus consolidadas para o módulo de comunicação."""

from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram


class CommunicationMetrics:
    """
    Coletor central de métricas Prometheus para o módulo de comunicação.
    
    Todas as métricas seguem a convenção:
    - Prefixo: comm_
    - Labels: channel, severity, status, intent_type, legal_basis
    
    Integra com prometheus_client para exposição no endpoint /metrics.
    """
    
    # ══════════════════════════════════════════════════════════════════════════
    # COUNTERS - Sempre aumentam
    # ══════════════════════════════════════════════════════════════════════════
    
    # Mensagens totais
    messages_total = Counter(
        "comm_messages_total",
        "Total de mensagens processadas pelo módulo de comunicação",
        labelnames=["channel", "severity", "status", "intent_type"]
    )
    
    # Fallbacks de canal (cascading)
    channel_fallback_total = Counter(
        "comm_channel_fallback_total",
        "Total de fallbacks entre canais (cascading)",
        labelnames=["from_channel", "to_channel", "reason"]
    )
    
    # LGPD - Bloqueios
    lgpd_blocked_total = Counter(
        "comm_lgpd_blocked_total",
        "Total de comunicações bloqueadas por LGPD",
        labelnames=["reason", "severity"]
    )
    
    # LGPD - Overrides (CRITICAL)
    lgpd_override_total = Counter(
        "comm_lgpd_override_total",
        "Total de overrides LGPD (vital interest)",
        labelnames=["severity", "legal_basis"]
    )
    
    # Bot - Comandos executados
    bot_commands_total = Counter(
        "comm_bot_commands_total",
        "Total de comandos do bot @intellicare executados",
        labelnames=["command", "status"]
    )
    
    # Eventos Redis processados
    events_processed_total = Counter(
        "comm_events_processed_total",
        "Total de eventos Redis processados",
        labelnames=["event_type", "status"]
    )
    
    # Teleconsultas criadas
    teleconsult_created_total = Counter(
        "comm_teleconsult_created_total",
        "Total de salas de teleconsulta criadas",
        labelnames=["provider"]  # jitsi, zoom, etc.
    )
    
    # ══════════════════════════════════════════════════════════════════════════
    # HISTOGRAMS - Distribuição de valores
    # ══════════════════════════════════════════════════════════════════════════
    
    # Latência de mensagem (end-to-end)
    message_latency_seconds = Histogram(
        "comm_message_latency_seconds",
        "Latência de envio de mensagem (segundos)",
        labelnames=["channel"],
        buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
    )
    
    # Latência de API
    api_request_duration_seconds = Histogram(
        "comm_api_request_duration_seconds",
        "Duração de requisições HTTP (segundos)",
        labelnames=["method", "endpoint", "status_code"],
        buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
    )
    
    # Latência de processamento de eventos
    event_processing_duration_seconds = Histogram(
        "comm_event_processing_duration_seconds",
        "Duração de processamento de eventos Redis (segundos)",
        labelnames=["event_type"],
        buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0]
    )
    
    # ══════════════════════════════════════════════════════════════════════════
    # GAUGES - Valores instantâneos
    # ══════════════════════════════════════════════════════════════════════════
    
    # Conexões DB ativas
    db_connections_active = Gauge(
        "comm_db_connections_active",
        "Conexões ativas ao PostgreSQL"
    )
    
    # Conexões Redis ativas
    redis_connections_active = Gauge(
        "comm_redis_connections_active",
        "Conexões ativas ao Redis"
    )
    
    # Intents pendentes
    pending_intents = Gauge(
        "comm_pending_intents",
        "Número de intents pendentes de processamento",
        labelnames=["status"]
    )
    
    # Salas de teleconsulta ativas
    active_teleconsult_rooms = Gauge(
        "comm_active_teleconsult_rooms",
        "Número de salas de teleconsulta ativas"
    )
    
    # Integridade da hash chain de auditoria
    audit_chain_integrity = Gauge(
        "comm_audit_chain_integrity",
        "Integridade da hash chain de auditoria (1=OK, 0=BROKEN)"
    )
    
    # Health status dos dispatchers
    dispatcher_health = Gauge(
        "comm_dispatcher_health",
        "Health status dos dispatchers (1=healthy, 0=unhealthy)",
        labelnames=["channel"]
    )
    
    # Redis consumer lag
    redis_consumer_lag = Gauge(
        "comm_redis_consumer_lag",
        "Lag do consumer Redis (mensagens pendentes)",
        labelnames=["stream"]
    )

