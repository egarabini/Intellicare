# Domínio 7 — Dashboard e Monitoramento
## Especificação Funcional Detalhada

**Identificadores**: EF-COM-060, EF-COM-061  
**Prioridade Global**: ALTA  
**Sprint**: S5–S6 (final, depende de todos os domínios)  
**Dependências**: D1 (métricas routing), D4 (métricas canal), D5 (consolidação analítica), D6 (métricas LGPD)  
**Dependentes**: Nenhum (topo da cadeia)

---

## 1. OBJETIVO

Implementar a camada de observabilidade completa do módulo de comunicação, incluindo:

1. **Dashboards Grafana** com 8+ painéis dedicados
2. **Métricas Prometheus** (counters, histograms, gauges)
3. **Alerting rules** para SLAs e anomalias
4. **Health checks** unificados
5. **API de métricas** para outros módulos consultarem
6. **Integração com infraestrutura** existente (Prometheus + Grafana do .)

**Contexto**: O IntelliCare já possui infraestrutura de monitoramento (ver `./prometheus.yml`, `grafana-dashboards.yml`, `grafana-datasources.yml`). Este domínio adiciona métricas específicas do módulo de comunicação a essa infraestrutura existente.

---

## 2. CONTEXTO ARQUITETURAL

```
┌────────────────────────────────────────────────────────────────────┐
│                    OBSERVABILITY STACK                              │
│                                                                    │
│  ┌─────────────┐    ┌──────────────┐    ┌───────────────────┐     │
│  │  Prometheus  │←───│  /metrics    │←───│ intellicare-      │     │
│  │  (scrape)    │    │  endpoint    │    │ comunicacao        │     │
│  └──────┬──────┘    └──────────────┘    │                    │     │
│         │                                │ MetricsCollector   │     │
│         v                                │ ├── routing_*      │     │
│  ┌─────────────┐                         │ ├── channel_*      │     │
│  │   Grafana    │                         │ ├── lgpd_*         │     │
│  │  8+ painéis  │                         │ └── event_*        │     │
│  └──────┬──────┘                         └───────────────────┘     │
│         │                                                          │
│         v                                                          │
│  ┌─────────────┐    ┌──────────────┐                              │
│  │  AlertManager│───→│  Webhook     │───→ Rocket.Chat #alertas    │
│  │  (rules)     │    │  Receiver    │                              │
│  └─────────────┘    └──────────────┘                              │
│                                                                    │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │              comunicacao_analitico (D5)                      │   │
│  │  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐   │   │
│  │  │comm_analytics│  │daily_metrics │  │team_comm_sla    │   │   │
│  │  └─────────────┘  └──────────────┘  └─────────────────┘   │   │
│  │              ↑ Grafana datasource (PostgreSQL)              │   │
│  └────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────┘
```

---

## 3. EF-COM-060 — Dashboards Grafana

### 3.1 Painel 1 — Overview de Comunicações

**Arquivo**: `dashboards/comunicacao_overview.json`

```json
{
  "dashboard": {
    "title": "IntelliCare Comunicação — Overview",
    "uid": "intellicare-comm-overview",
    "tags": ["intellicare", "comunicacao"],
    "timezone": "browser",
    "refresh": "30s"
  }
}
```

**Widgets**:

| # | Widget | Tipo | Fonte | Query |
|---|--------|------|-------|-------|
| 1 | Total comunicações (últimas 24h) | Stat | Prometheus | `sum(increase(comm_messages_total[24h]))` |
| 2 | Taxa de entrega (%) | Gauge | Prometheus | `sum(rate(comm_messages_total{status="delivered"}[1h])) / sum(rate(comm_messages_total[1h])) * 100` |
| 3 | Comunicações por canal | Pie Chart | Prometheus | `sum by(channel)(increase(comm_messages_total[24h]))` |
| 4 | Comunicações por severidade | Bar Chart | Prometheus | `sum by(severity)(increase(comm_messages_total[24h]))` |
| 5 | Latência de entrega (p50/p95/p99) | Time Series | Prometheus | `histogram_quantile(0.95, rate(comm_delivery_latency_seconds_bucket[5m]))` |
| 6 | Falhas recentes | Table | Prometheus | `topk(10, increase(comm_messages_total{status="failed"}[1h]))` |

### 3.2 Painel 2 — Canais de Comunicação

**Arquivo**: `dashboards/comunicacao_channels.json`

**Widgets**:

| # | Widget | Tipo | Fonte | Query |
|---|--------|------|-------|-------|
| 1 | WhatsApp — Mensagens/min | Time Series | Prometheus | `rate(comm_messages_total{channel="whatsapp"}[5m])` |
| 2 | WhatsApp — Taxa de leitura | Gauge | Prometheus | `rate(comm_messages_total{channel="whatsapp",status="read"}[1h]) / rate(comm_messages_total{channel="whatsapp"}[1h])` |
| 3 | SMS — Mensagens/min | Time Series | Prometheus | `rate(comm_messages_total{channel="sms"}[5m])` |
| 4 | Email — Mensagens/min | Time Series | Prometheus | `rate(comm_messages_total{channel="email"}[5m])` |
| 5 | Push — Entregues/Bounced | Stacked Bar | Prometheus | `sum by(status)(rate(comm_messages_total{channel="push"}[1h]))` |
| 6 | Rocket.Chat — Mensagens/min | Time Series | Prometheus | `rate(comm_messages_total{channel="rocketchat"}[5m])` |
| 7 | Cascading fallback rate | Gauge | Prometheus | `rate(comm_channel_fallback_total[1h])` |
| 8 | Custo estimado ($ por canal) | Stat | PostgreSQL | `SELECT channel, SUM(estimated_cost) FROM comm_analytics WHERE date >= NOW() - INTERVAL '30 days' GROUP BY channel` |

### 3.3 Painel 3 — Teleconsulta

**Arquivo**: `dashboards/comunicacao_teleconsulta.json`

**Widgets**:

| # | Widget | Tipo | Fonte | Query |
|---|--------|------|-------|-------|
| 1 | Sessões ativas agora | Stat | Prometheus | `comm_teleconsult_active_sessions` |
| 2 | Sessões hoje | Stat | Prometheus | `increase(comm_teleconsult_total[24h])` |
| 3 | Taxa de no-show | Gauge | Prometheus | `rate(comm_teleconsult_total{status="no_show"}[7d]) / rate(comm_teleconsult_total[7d]) * 100` |
| 4 | Duração média | Stat | Prometheus | `histogram_quantile(0.5, rate(comm_teleconsult_duration_seconds_bucket[24h]))` |
| 5 | Sessões por status | Pie Chart | Prometheus | `sum by(status)(increase(comm_teleconsult_total[24h]))` |
| 6 | Case rooms ativas | Stat | Prometheus | `comm_case_rooms_active` |

### 3.4 Painel 4 — LGPD e Conformidade

**Arquivo**: `dashboards/comunicacao_lgpd.json`

**Widgets**:

| # | Widget | Tipo | Fonte | Query |
|---|--------|------|-------|-------|
| 1 | Cobertura de consentimento (%) | Gauge | PostgreSQL | `SELECT COUNT(CASE WHEN consent_given_at IS NOT NULL THEN 1 END)::float / COUNT(*)::float * 100 FROM communication_preferences` |
| 2 | Comunicações por base legal | Pie Chart | Prometheus | `sum by(legal_basis)(increase(comm_messages_total[24h]))` |
| 3 | CRITICAL overrides (24h) | Stat | Prometheus | `sum(increase(comm_lgpd_override_total{severity="CRITICAL"}[24h]))` |
| 4 | Bloqueados por LGPD | Stat | Prometheus | `sum(increase(comm_lgpd_blocked_total[24h]))` |
| 5 | Opt-out rate (30d) | Time Series | PostgreSQL | `SELECT date_trunc('day', status_changed_at) as day, COUNT(*) FROM channel_preferences WHERE status = 'revoked' GROUP BY day` |
| 6 | Chain integrity (último check) | Stat | Prometheus | `comm_audit_chain_integrity` |
| 7 | Solicitações Art. 18 (30d) | Stat | Prometheus | `increase(comm_lgpd_data_requests_total[30d])` |

### 3.5 Painel 5 — Eventos e Processamento

**Arquivo**: `dashboards/comunicacao_events.json`

**Widgets**:

| # | Widget | Tipo | Fonte | Query |
|---|--------|------|-------|-------|
| 1 | Eventos processados/min | Time Series | Prometheus | `rate(comm_events_processed_total[5m])` |
| 2 | Eventos por stream | Stacked Area | Prometheus | `sum by(stream)(rate(comm_events_processed_total[5m]))` |
| 3 | Pending entries (lag) | Time Series | Prometheus | `comm_events_pending_entries` |
| 4 | Duplicatas detectadas | Stat | Prometheus | `increase(comm_events_duplicates_total[1h])` |
| 5 | Consumer lag por grupo | Bar Chart | Prometheus | `comm_consumer_group_lag` |
| 6 | Tempo de processamento (p95) | Gauge | Prometheus | `histogram_quantile(0.95, rate(comm_event_processing_seconds_bucket[5m]))` |

### 3.6 Painel 6 — SLA por Equipe

**Arquivo**: `dashboards/comunicacao_sla.json`

**Widgets**:

| # | Widget | Tipo | Fonte | Query/SQL |
|---|--------|------|-------|-----------|
| 1 | SLA de resposta por equipe | Table | PostgreSQL | `SELECT team_name, avg_response_time_min, messages_within_sla_pct FROM team_communication_sla WHERE metric_date = CURRENT_DATE` |
| 2 | SLA trend (30d) | Time Series | PostgreSQL | `SELECT metric_date, messages_within_sla_pct FROM team_communication_sla WHERE team_name = '${team}' ORDER BY metric_date` |
| 3 | Canais mais usados por equipe | Heatmap | PostgreSQL | `SELECT team_name, channel, count FROM daily_metrics WHERE metric_date >= NOW() - INTERVAL '7 days'` |
| 4 | Alertas CRITICAL por equipe | Bar Chart | Prometheus | `sum by(team)(increase(comm_messages_total{severity="CRITICAL"}[24h]))` |

### 3.7 Painel 7 — Bot IntelliCare

**Arquivo**: `dashboards/comunicacao_bot.json`

**Widgets**:

| # | Widget | Tipo | Fonte | Query |
|---|--------|------|-------|-------|
| 1 | Comandos/hora | Time Series | Prometheus | `rate(comm_bot_commands_total[1h])` |
| 2 | Comandos por tipo | Pie Chart | Prometheus | `sum by(command)(increase(comm_bot_commands_total[24h]))` |
| 3 | Tempo de resposta bot (p95) | Gauge | Prometheus | `histogram_quantile(0.95, rate(comm_bot_response_seconds_bucket[5m]))` |
| 4 | Erros do bot | Stat | Prometheus | `increase(comm_bot_errors_total[1h])` |
| 5 | DrNise queries | Stat | Prometheus | `increase(comm_bot_commands_total{command="drnise"}[24h])` |

### 3.8 Painel 8 — Status e Health

**Arquivo**: `dashboards/comunicacao_health.json`

**Widgets**:

| # | Widget | Tipo | Fonte | Query |
|---|--------|------|-------|-------|
| 1 | Serviço UP/DOWN | Stat | Prometheus | `up{job="intellicare-comunicacao"}` |
| 2 | CPU / Memory | Time Series | Prometheus | `process_cpu_seconds_total{job="intellicare-comunicacao"}` |
| 3 | Conexões DB ativas | Gauge | Prometheus | `comm_db_connections_active` |
| 4 | Redis connections | Gauge | Prometheus | `comm_redis_connections_active` |
| 5 | Error rate (5xx) | Time Series | Prometheus | `rate(comm_http_requests_total{status=~"5.."}[5m])` |
| 6 | Latência API (p50/p95/p99) | Time Series | Prometheus | `histogram_quantile(0.95, rate(comm_http_request_duration_seconds_bucket[5m]))` |

---

## 4. EF-COM-061 — Métricas Prometheus

### 4.1 MetricsCollector

```python
from prometheus_client import Counter, Histogram, Gauge, Info
from typing import Optional


class CommunicationMetrics:
    """
    Colletor central de métricas Prometheus para o módulo de comunicação.
    
    Todas as métricas seguem a convenção:
    - Prefixo: comm_
    - Labels: channel, severity, status, intent_type, legal_basis
    
    Integra com prometheus_client para exposição no endpoint /metrics.
    """
    
    # ── COUNTERS ──
    
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
    
    # Eventos processados
    events_processed_total = Counter(
        "comm_events_processed_total",
        "Total de eventos Redis Streams processados",
        labelnames=["stream", "handler"]
    )
    
    # Duplicatas detectadas
    events_duplicates_total = Counter(
        "comm_events_duplicates_total",
        "Total de eventos duplicados descartados",
        labelnames=["stream"]
    )
    
    # LGPD overrides
    lgpd_override_total = Counter(
        "comm_lgpd_override_total",
        "Total de comunicações enviadas com override LGPD (CRITICAL/HIGH)",
        labelnames=["severity", "legal_basis"]
    )
    
    # LGPD bloqueios
    lgpd_blocked_total = Counter(
        "comm_lgpd_blocked_total",
        "Total de comunicações bloqueadas por LGPD",
        labelnames=["reason"]
    )
    
    # Teleconsultas
    teleconsult_total = Counter(
        "comm_teleconsult_total",
        "Total de teleconsultas",
        labelnames=["status"]  # scheduled, started, completed, no_show, cancelled
    )
    
    # Bot commands
    bot_commands_total = Counter(
        "comm_bot_commands_total",
        "Total de comandos processados pelo bot",
        labelnames=["command"]
    )
    
    # Bot errors
    bot_errors_total = Counter(
        "comm_bot_errors_total",
        "Total de erros do bot",
        labelnames=["command", "error_type"]
    )
    
    # Solicitações LGPD (Art. 18)
    lgpd_data_requests_total = Counter(
        "comm_lgpd_data_requests_total",
        "Total de solicitações de direito do titular (Art. 18)",
        labelnames=["request_type"]  # data_export, anonymization, consent_history
    )
    
    # HTTP requests
    http_requests_total = Counter(
        "comm_http_requests_total",
        "Total de requisições HTTP à API de comunicação",
        labelnames=["method", "endpoint", "status"]
    )
    
    # ── HISTOGRAMS ──
    
    # Latência de entrega
    delivery_latency_seconds = Histogram(
        "comm_delivery_latency_seconds",
        "Latência de entrega de mensagens (segundos)",
        labelnames=["channel"],
        buckets=[0.1, 0.5, 1, 2, 5, 10, 30, 60, 120, 300]
    )
    
    # Duração de teleconsulta
    teleconsult_duration_seconds = Histogram(
        "comm_teleconsult_duration_seconds",
        "Duração de teleconsultas (segundos)",
        buckets=[60, 300, 600, 900, 1200, 1800, 2700, 3600]
    )
    
    # Tempo de processamento de evento
    event_processing_seconds = Histogram(
        "comm_event_processing_seconds",
        "Tempo de processamento de eventos (segundos)",
        labelnames=["stream", "handler"],
        buckets=[0.01, 0.05, 0.1, 0.5, 1, 5, 10]
    )
    
    # Tempo de resposta do bot
    bot_response_seconds = Histogram(
        "comm_bot_response_seconds",
        "Tempo de resposta do bot IntelliCare (segundos)",
        labelnames=["command"],
        buckets=[0.1, 0.5, 1, 2, 5, 10]
    )
    
    # Latência da API
    http_request_duration_seconds = Histogram(
        "comm_http_request_duration_seconds",
        "Latência das requisições HTTP (segundos)",
        labelnames=["method", "endpoint"],
        buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10]
    )
    
    # ── GAUGES ──
    
    # Teleconsultas ativas
    teleconsult_active_sessions = Gauge(
        "comm_teleconsult_active_sessions",
        "Número de teleconsultas ativas agora"
    )
    
    # Case rooms ativas
    case_rooms_active = Gauge(
        "comm_case_rooms_active",
        "Número de case rooms ativas"
    )
    
    # Pending entries (consumer lag)
    events_pending_entries = Gauge(
        "comm_events_pending_entries",
        "Número de eventos pendentes no consumer group",
        labelnames=["stream", "consumer_group"]
    )
    
    # Consumer group lag
    consumer_group_lag = Gauge(
        "comm_consumer_group_lag",
        "Lag do consumer group (diferença entre último evento e último processado)",
        labelnames=["stream", "consumer_group"]
    )
    
    # Conexões DB
    db_connections_active = Gauge(
        "comm_db_connections_active",
        "Conexões ativas ao PostgreSQL"
    )
    
    # Conexões Redis
    redis_connections_active = Gauge(
        "comm_redis_connections_active",
        "Conexões ativas ao Redis"
    )
    
    # Integridade da audit chain
    audit_chain_integrity = Gauge(
        "comm_audit_chain_integrity",
        "Integridade da hash chain de auditoria (1=ok, 0=broken)"
    )
    
    # ── INFO ──
    
    build_info = Info(
        "comm_build",
        "Informações do build do módulo de comunicação"
    )


class MetricsMiddleware:
    """
    Middleware FastAPI para coleta automática de métricas HTTP.
    
    Instrumenta automaticamente todas as requisições com:
    - Counter de requests
    - Histogram de latência
    - Labels: method, endpoint, status
    """
    
    def __init__(self, app, metrics: CommunicationMetrics):
        self._app = app
        self._metrics = metrics
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self._app(scope, receive, send)
        
        import time
        start = time.perf_counter()
        
        # Extract endpoint
        path = scope.get("path", "unknown")
        method = scope.get("method", "GET")
        
        # Process request
        status_code = 200
        
        async def send_wrapper(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)
        
        try:
            await self._app(scope, receive, send_wrapper)
        finally:
            duration = time.perf_counter() - start
            
            self._metrics.http_requests_total.labels(
                method=method,
                endpoint=self._normalize_path(path),
                status=str(status_code)
            ).inc()
            
            self._metrics.http_request_duration_seconds.labels(
                method=method,
                endpoint=self._normalize_path(path)
            ).observe(duration)
    
    def _normalize_path(self, path: str) -> str:
        """
        Normaliza path para evitar explosão de cardinalidade.
        Ex: /api/v1/messages/abc-123 → /api/v1/messages/{id}
        """
        import re
        # UUIDs
        path = re.sub(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', '{id}', path)
        # Numeric IDs
        path = re.sub(r'/\d+', '/{id}', path)
        return path
```

### 4.2 Instrumentação nos Serviços

```python
# ── RoutingEngine (D1) — instrumentação ──

class RoutingEngine:
    def __init__(self, ..., metrics: CommunicationMetrics):
        self._metrics = metrics
    
    async def route(self, intent):
        # ... routing logic ...
        
        # Registrar métrica de mensagem
        self._metrics.messages_total.labels(
            channel=delivery.channel,
            severity=intent.severity,
            status=delivery.status,
            intent_type=intent.intent_type
        ).inc()
        
        # Registrar latência
        if delivery.delivered_at and delivery.sent_at:
            latency = (delivery.delivered_at - delivery.sent_at).total_seconds()
            self._metrics.delivery_latency_seconds.labels(
                channel=delivery.channel
            ).observe(latency)
        
        # Registrar fallback se cascading
        if delivery.fallback_from:
            self._metrics.channel_fallback_total.labels(
                from_channel=delivery.fallback_from,
                to_channel=delivery.channel,
                reason=delivery.fallback_reason
            ).inc()


# ── LGPDComplianceService (D6) — instrumentação ──

class LGPDComplianceService:
    async def can_send(self, ...):
        decision = await self._evaluate(...)
        
        if decision.override_applied:
            self._metrics.lgpd_override_total.labels(
                severity=severity,
                legal_basis=decision.legal_basis.value
            ).inc()
        
        if not decision.allowed:
            self._metrics.lgpd_blocked_total.labels(
                reason=decision.reason[:50]
            ).inc()
        
        return decision


# ── MultiEventConsumer (D5) — instrumentação ──

class MultiEventConsumer:
    async def process_event(self, stream, event):
        import time
        start = time.perf_counter()
        
        try:
            result = await self._handler.handle(event)
            
            self._metrics.events_processed_total.labels(
                stream=stream,
                handler=self._handler.__class__.__name__
            ).inc()
        finally:
            duration = time.perf_counter() - start
            self._metrics.event_processing_seconds.labels(
                stream=stream,
                handler=self._handler.__class__.__name__
            ).observe(duration)


# ── TeleconsultService (D3) — instrumentação ──

class TeleconsultService:
    async def register_join(self, session_id, participant_id):
        # ... logic ...
        self._metrics.teleconsult_active_sessions.inc()
    
    async def register_end(self, session_id):
        # ... logic ...
        self._metrics.teleconsult_active_sessions.dec()
        
        duration = (session.ended_at - session.started_at).total_seconds()
        self._metrics.teleconsult_duration_seconds.observe(duration)
        
        self._metrics.teleconsult_total.labels(
            status="completed"
        ).inc()
```

### 4.3 Endpoint /metrics

```python
from fastapi import FastAPI, Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

app = FastAPI()


@app.get("/metrics")
async def metrics():
    """
    Endpoint Prometheus.
    
    Scraped pelo Prometheus configurado em ./prometheus.yml
    """
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


@app.get("/health")
async def health():
    """
    Health check unificado.
    
    Verifica:
    - PostgreSQL connectivity
    - Redis connectivity
    - Rocket.Chat API reachability
    - Keycloak token endpoint
    """
    checks = {}
    
    # PostgreSQL
    try:
        await db.execute("SELECT 1")
        checks["postgresql"] = {"status": "healthy"}
    except Exception as e:
        checks["postgresql"] = {"status": "unhealthy", "error": str(e)}
    
    # Redis
    try:
        await redis.ping()
        checks["redis"] = {"status": "healthy"}
    except Exception as e:
        checks["redis"] = {"status": "unhealthy", "error": str(e)}
    
    # Rocket.Chat
    try:
        resp = await http.get(f"{RC_URL}/api/v1/info")
        checks["rocketchat"] = {"status": "healthy" if resp.status_code == 200 else "degraded"}
    except Exception as e:
        checks["rocketchat"] = {"status": "unhealthy", "error": str(e)}
    
    # Keycloak
    try:
        resp = await http.get(f"{KC_URL}/realms/bemcuidar/.well-known/openid-configuration")
        checks["keycloak"] = {"status": "healthy" if resp.status_code == 200 else "degraded"}
    except Exception as e:
        checks["keycloak"] = {"status": "unhealthy", "error": str(e)}
    
    overall = "healthy" if all(c["status"] == "healthy" for c in checks.values()) else "degraded"
    
    return {
        "status": overall,
        "version": "1.0.0",
        "checks": checks
    }


@app.get("/readiness")
async def readiness():
    """
    Readiness probe (Kubernetes/Docker).
    
    Retorna 200 se o serviço está pronto para receber tráfego.
    """
    try:
        await db.execute("SELECT 1")
        await redis.ping()
        return {"ready": True}
    except Exception:
        return Response(status_code=503, content='{"ready": false}')
```

---

## 5. ALERTING RULES

### 5.1 Prometheus Alerting Rules

```yaml
# File: alerting/comunicacao_alerts.yml

groups:
  - name: intellicare-comunicacao
    rules:
      # ── Disponibilidade ──
      
      - alert: ComunicacaoServiceDown
        expr: up{job="intellicare-comunicacao"} == 0
        for: 1m
        labels:
          severity: critical
          module: comunicacao
        annotations:
          summary: "Serviço de comunicação indisponível"
          description: "O módulo de comunicação está DOWN há mais de 1 minuto"
      
      # ── Taxa de Falha ──
      
      - alert: ComunicacaoHighFailureRate
        expr: |
          sum(rate(comm_messages_total{status="failed"}[5m]))
          / sum(rate(comm_messages_total[5m])) > 0.1
        for: 5m
        labels:
          severity: warning
          module: comunicacao
        annotations:
          summary: "Taxa de falha de comunicação > 10%"
          description: "{{ $value | humanizePercentage }} das comunicações estão falhando nos últimos 5 minutos"
      
      - alert: ComunicacaoCriticalFailureRate
        expr: |
          sum(rate(comm_messages_total{status="failed"}[5m]))
          / sum(rate(comm_messages_total[5m])) > 0.3
        for: 2m
        labels:
          severity: critical
          module: comunicacao
        annotations:
          summary: "Taxa de falha de comunicação > 30%"
          description: "{{ $value | humanizePercentage }} das comunicações falhando — possível queda de canal"
      
      # ── Canal Específico ──
      
      - alert: WhatsAppChannelDown
        expr: |
          sum(rate(comm_messages_total{channel="whatsapp",status="failed"}[5m]))
          / sum(rate(comm_messages_total{channel="whatsapp"}[5m])) > 0.5
        for: 3m
        labels:
          severity: critical
          channel: whatsapp
          module: comunicacao
        annotations:
          summary: "Canal WhatsApp com > 50% de falha"
          description: "Possível problema na API do WhatsApp Business"
      
      - alert: SMSChannelDown
        expr: |
          sum(rate(comm_messages_total{channel="sms",status="failed"}[5m]))
          / sum(rate(comm_messages_total{channel="sms"}[5m])) > 0.5
        for: 3m
        labels:
          severity: critical
          channel: sms
          module: comunicacao
        annotations:
          summary: "Canal SMS com > 50% de falha"
          description: "Possível problema no provedor de SMS"
      
      # ── Latência ──
      
      - alert: ComunicacaoHighLatency
        expr: |
          histogram_quantile(0.95, rate(comm_delivery_latency_seconds_bucket[5m])) > 30
        for: 5m
        labels:
          severity: warning
          module: comunicacao
        annotations:
          summary: "Latência p95 de entrega > 30s"
          description: "P95 da latência de entrega está em {{ $value }}s"
      
      # ── Consumer Lag ──
      
      - alert: EventConsumerLagHigh
        expr: comm_consumer_group_lag > 1000
        for: 5m
        labels:
          severity: warning
          module: comunicacao
        annotations:
          summary: "Consumer lag > 1000 eventos"
          description: "Stream {{ $labels.stream }} com lag de {{ $value }} eventos"
      
      - alert: EventConsumerLagCritical
        expr: comm_consumer_group_lag > 5000
        for: 2m
        labels:
          severity: critical
          module: comunicacao
        annotations:
          summary: "Consumer lag > 5000 eventos"
          description: "CRÍTICO: Stream {{ $labels.stream }} com lag de {{ $value }} eventos — possível parada do consumer"
      
      # ── LGPD ──
      
      - alert: HighCriticalOverrideRate
        expr: |
          increase(comm_lgpd_override_total[1h]) > 50
        for: 0m
        labels:
          severity: warning
          module: comunicacao
        annotations:
          summary: "> 50 overrides CRITICAL LGPD em 1 hora"
          description: "Volume anormalmente alto de comunicações enviadas sem consentimento"
      
      - alert: AuditChainIntegrityBroken
        expr: comm_audit_chain_integrity == 0
        for: 0m
        labels:
          severity: critical
          module: comunicacao
        annotations:
          summary: "Integridade da hash chain de auditoria QUEBRADA"
          description: "A trilha de auditoria pode ter sido adulterada — investigar IMEDIATAMENTE"
      
      # ── Teleconsulta ──
      
      - alert: HighNoShowRate
        expr: |
          sum(rate(comm_teleconsult_total{status="no_show"}[24h]))
          / sum(rate(comm_teleconsult_total[24h])) > 0.3
        for: 0m
        labels:
          severity: warning
          module: comunicacao
        annotations:
          summary: "Taxa de no-show em teleconsulta > 30%"
          description: "{{ $value | humanizePercentage }} de no-shows nas últimas 24h"
      
      # ── Infraestrutura ──
      
      - alert: DatabaseConnectionPoolExhausted
        expr: comm_db_connections_active > 45
        for: 1m
        labels:
          severity: critical
          module: comunicacao
        annotations:
          summary: "Pool de conexões PostgreSQL quase esgotado"
          description: "{{ $value }} conexões ativas (máximo: 50)"
      
      - alert: RedisConnectionHigh
        expr: comm_redis_connections_active > 90
        for: 1m
        labels:
          severity: warning
          module: comunicacao
        annotations:
          summary: "Muitas conexões Redis ativas"
          description: "{{ $value }} conexões Redis ativas"
```

### 5.2 AlertManager Webhook → Rocket.Chat

```python
class AlertManagerWebhookHandler:
    """
    Recebe webhooks do AlertManager e posta no Rocket.Chat.
    
    Canal alvo: #alertas-infraestrutura
    """
    
    async def handle_webhook(self, payload: dict):
        """
        Formato AlertManager → Rocket.Chat message.
        """
        for alert in payload.get("alerts", []):
            severity = alert["labels"].get("severity", "unknown")
            summary = alert["annotations"].get("summary", "Alerta sem resumo")
            description = alert["annotations"].get("description", "")
            status = alert["status"]  # "firing" | "resolved"
            
            if status == "firing":
                emoji = "🔴" if severity == "critical" else "🟡"
                color = "#FF0000" if severity == "critical" else "#FFA500"
            else:
                emoji = "🟢"
                color = "#00FF00"
            
            message = {
                "channel": "#alertas-infraestrutura",
                "alias": "IntelliCare Monitor",
                "emoji": ":robot:",
                "attachments": [{
                    "color": color,
                    "title": f"{emoji} [{status.upper()}] {summary}",
                    "text": description,
                    "fields": [
                        {"short": True, "title": "Severidade", "value": severity},
                        {"short": True, "title": "Módulo", "value": alert["labels"].get("module", "unknown")},
                        {"short": True, "title": "Canal", "value": alert["labels"].get("channel", "all")},
                    ],
                    "ts": alert.get("startsAt", "")
                }]
            }
            
            await self._rc_client.send_message(message)
```

---

## 6. INTEGRAÇÃO COM INFRAESTRUTURA EXISTENTE

### 6.1 Prometheus Configuration

Adicionar ao `./prometheus.yml`:

```yaml
# Adicionar ao scrape_configs existente:
  - job_name: 'intellicare-comunicacao'
    scrape_interval: 15s
    metrics_path: /metrics
    static_configs:
      - targets: ['intellicare-comunicacao:8000']
        labels:
          module: comunicacao
          environment: production
```

### 6.2 Grafana Datasource

Adicionar ao `./grafana-datasources.yml`:

```yaml
# Adicionar datasources:
  - name: IntelliCare-Comunicacao-PostgreSQL
    type: postgres
    access: proxy
    url: postgresql:5432
    database: intellicare_comunicacao
    user: grafana_reader
    secureJsonData:
      password: ${GRAFANA_PG_PASSWORD}
    jsonData:
      sslmode: disable
      maxOpenConns: 5
      maxIdleConns: 5
      connMaxLifetime: 14400
      postgresVersion: 1500
      timescaledb: false
```

### 6.3 Grafana Dashboard Provisioning

Adicionar ao `./grafana-dashboards.yml`:

```yaml
# Adicionar ao providers existente:
  - name: 'intellicare-comunicacao'
    orgId: 1
    folder: 'IntelliCare Comunicação'
    type: file
    disableDeletion: false
    editable: true
    options:
      path: /var/lib/grafana/dashboards/comunicacao
      foldersFromFilesStructure: false
```

---

## 7. API DE MÉTRICAS

```yaml
# ── Métricas via API (para outros módulos) ──

GET /api/v1/metrics/summary
  Description: Resumo de métricas para dashboard interno
  Auth: Keycloak (admin, monitor)
  Response 200:
    {
      "period": "last_24h",
      "total_messages": int,
      "delivery_rate": float,
      "by_channel": {
        "whatsapp": { "sent": int, "delivered": int, "failed": int },
        "sms": { "sent": int, "delivered": int, "failed": int },
        "email": { "sent": int, "delivered": int, "failed": int },
        "push": { "sent": int, "delivered": int, "failed": int },
        "rocketchat": { "sent": int, "delivered": int, "failed": int }
      },
      "by_severity": {
        "CRITICAL": int, "HIGH": int, "MEDIUM": int, "LOW": int
      },
      "teleconsults": {
        "scheduled": int, "completed": int, "no_show": int
      },
      "lgpd": {
        "consent_coverage": float,
        "overrides": int,
        "blocked": int
      }
    }

GET /api/v1/metrics/channel/{channel}
  Description: Métricas detalhadas de um canal
  Auth: Keycloak (admin, monitor)
  Query: period (1h|6h|24h|7d|30d)
  Response 200: { channel: str, metrics: ChannelMetrics }

GET /api/v1/metrics/team/{team_id}
  Description: Métricas de comunicação de uma equipe
  Auth: Keycloak (team_lead, admin)
  Query: period (24h|7d|30d)
  Response 200: { team_id: str, metrics: TeamMetrics }

GET /api/v1/metrics/sla
  Description: Relatório de SLA de comunicação
  Auth: Keycloak (admin, monitor, quality)
  Query: period, team_id (optional)
  Response 200: { sla_targets: Dict, actual: Dict, compliance: float }
```

---

## 8. SCHEMA SQL (Analítico — complemento D5)

```sql
-- Migration: 2026_02_25_0007_create_monitoring_views.py
-- Schema: comunicacao_analitico (complementa tabelas de D5)

-- View materializada para dashboard de SLA
CREATE MATERIALIZED VIEW comunicacao_analitico.sla_dashboard AS
SELECT
    tcs.team_name,
    tcs.metric_date,
    tcs.messages_sent,
    tcs.messages_within_sla_pct,
    tcs.avg_response_time_min,
    dm.delivered,
    dm.failed,
    CASE 
        WHEN dm.total > 0 THEN dm.delivered::float / dm.total * 100 
        ELSE 0 
    END AS delivery_rate_pct
FROM comunicacao_analitico.team_communication_sla tcs
LEFT JOIN (
    SELECT 
        metric_date,
        SUM(CASE WHEN status = 'delivered' THEN count ELSE 0 END) AS delivered,
        SUM(CASE WHEN status = 'failed' THEN count ELSE 0 END) AS failed,
        SUM(count) AS total
    FROM comunicacao_analitico.daily_metrics
    GROUP BY metric_date
) dm ON dm.metric_date = tcs.metric_date
WHERE tcs.metric_date >= CURRENT_DATE - INTERVAL '90 days'
WITH DATA;

-- Refresh a cada hora
-- Schedule via pg_cron ou cron externo:
-- REFRESH MATERIALIZED VIEW CONCURRENTLY comunicacao_analitico.sla_dashboard;

-- View para LGPD compliance dashboard
CREATE VIEW comunicacao_analitico.lgpd_compliance_view AS
SELECT
    date_trunc('day', at.created_at) AS day,
    at.legal_basis,
    at.lgpd_override,
    COUNT(*) AS total_communications,
    COUNT(CASE WHEN at.status = 'blocked_lgpd' THEN 1 END) AS blocked,
    COUNT(CASE WHEN at.lgpd_override THEN 1 END) AS overrides
FROM comunicacao_operacional.audit_trail at
WHERE at.created_at >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY 1, 2, 3;

-- View para consent coverage
CREATE VIEW comunicacao_analitico.consent_coverage_view AS
SELECT
    date_trunc('day', cp.created_at) AS day,
    COUNT(*) AS total_patients,
    COUNT(CASE WHEN cp.consent_given_at IS NOT NULL THEN 1 END) AS consented,
    COUNT(CASE WHEN cp.consent_given_at IS NOT NULL THEN 1 END)::float 
        / NULLIF(COUNT(*), 0) * 100 AS coverage_pct
FROM comunicacao_operacional.communication_preferences cp
GROUP BY 1;

-- Usuário read-only para Grafana
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'grafana_reader') THEN
        CREATE ROLE grafana_reader LOGIN PASSWORD '${GRAFANA_PG_PASSWORD}';
    END IF;
END $$;

GRANT USAGE ON SCHEMA comunicacao_analitico TO grafana_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA comunicacao_analitico TO grafana_reader;
GRANT USAGE ON SCHEMA comunicacao_operacional TO grafana_reader;
GRANT SELECT ON comunicacao_operacional.audit_trail TO grafana_reader;
GRANT SELECT ON comunicacao_operacional.communication_preferences TO grafana_reader;
ALTER DEFAULT PRIVILEGES IN SCHEMA comunicacao_analitico GRANT SELECT ON TABLES TO grafana_reader;
```

---

## 9. ESTRUTURA DE CÓDIGO

```
comunicacao/
├── monitoring/
│   ├── __init__.py
│   ├── metrics.py                      # CommunicationMetrics (todas as métricas)
│   ├── middleware.py                    # MetricsMiddleware (HTTP)
│   ├── health.py                       # Health check endpoints
│   └── config.py                       # MonitoringConfig
├── dashboards/
│   ├── comunicacao_overview.json        # Painel 1
│   ├── comunicacao_channels.json        # Painel 2
│   ├── comunicacao_teleconsulta.json    # Painel 3
│   ├── comunicacao_lgpd.json            # Painel 4
│   ├── comunicacao_events.json          # Painel 5
│   ├── comunicacao_sla.json             # Painel 6
│   ├── comunicacao_bot.json             # Painel 7
│   └── comunicacao_health.json          # Painel 8
├── alerting/
│   ├── comunicacao_alerts.yml           # Prometheus alerting rules
│   └── webhook_handler.py              # AlertManager → Rocket.Chat
├── api/
│   └── metrics_routes.py               # /metrics, /health, /api/v1/metrics/*
└── tests/
    └── test_monitoring/
        ├── test_metrics.py
        ├── test_middleware.py
        ├── test_health.py
        ├── test_alerting.py
        └── test_dashboards.py
```

---

## 10. TESTES ESPERADOS

```
test_monitoring/
├── test_metrics.py
│   ├── test_messages_counter_incremented
│   ├── test_messages_counter_labels_correct
│   ├── test_delivery_latency_histogram
│   ├── test_fallback_counter
│   ├── test_lgpd_override_counter
│   ├── test_lgpd_blocked_counter
│   ├── test_teleconsult_active_gauge
│   ├── test_events_processed_counter
│   ├── test_bot_commands_counter
│   └── test_build_info_set
├── test_middleware.py
│   ├── test_http_request_counted
│   ├── test_http_duration_observed
│   ├── test_path_normalization_uuid
│   ├── test_path_normalization_numeric
│   └── test_non_http_skipped
├── test_health.py
│   ├── test_health_all_healthy
│   ├── test_health_postgres_down
│   ├── test_health_redis_down
│   ├── test_health_rc_down
│   ├── test_readiness_ok
│   └── test_readiness_db_down
├── test_alerting.py
│   ├── test_webhook_firing_critical
│   ├── test_webhook_firing_warning
│   ├── test_webhook_resolved
│   ├── test_webhook_posts_to_rc
│   └── test_alert_rules_valid_promql
└── test_dashboards.py
    ├── test_overview_json_valid
    ├── test_channels_json_valid
    ├── test_teleconsulta_json_valid
    ├── test_lgpd_json_valid
    ├── test_events_json_valid
    ├── test_sla_json_valid
    ├── test_bot_json_valid
    └── test_health_json_valid
```

---

## 11. CONFIGURAÇÃO

```bash
# Prometheus
PROMETHEUS_ENABLED=true
METRICS_PORT=8000
METRICS_PATH=/metrics

# Grafana  
GRAFANA_PG_PASSWORD=<senha_grafana_reader>

# Health checks
HEALTH_CHECK_INTERVAL=30
HEALTH_CHECK_TIMEOUT=5

# AlertManager
ALERTMANAGER_WEBHOOK_URL=http://intellicare-comunicacao:8000/webhooks/alertmanager
ALERTMANAGER_RC_CHANNEL=#alertas-infraestrutura
```

---

## 12. ENTREGÁVEIS DO DEV

1. **Especificação Técnica**: Arquitetura de observabilidade detalhada
2. **Plano de Implementação**: Metrics → Middleware → Health → Dashboards → Alerting
3. **Código**: Todos os serviços + 8 dashboard JSONs
4. **Migrations**: Views materializadas + roles Grafana
5. **Alerting rules**: YAML validado com promtool
6. **Integração**: Configuração Prometheus + Grafana + AlertManager
7. **Documentação**: README com screenshots de cada painel

**Prazo estimado**: 2 sprints (S5 + S6)

**Requisitos de pacotes**:
```
prometheus-client>=0.20.0
```

**NOTA**: Os dashboard JSONs devem ser gerados/importados via Grafana API ou provisioning. O formato JSON segue o padrão Grafana export.
