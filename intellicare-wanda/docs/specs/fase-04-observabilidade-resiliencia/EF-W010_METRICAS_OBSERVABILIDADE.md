# EF-W010 — Metricas e Observabilidade

> Dashboard completo de metricas operacionais da Wanda com Prometheus e alertas de degradacao.

## 1. Objetivo

Instrumentar completamente a Wanda para observabilidade operacional:
- Metricas de latencia e throughput por agente
- Metricas de taxa de sucesso/falha
- Metricas de IPS cache e roteamento
- Alertas automaticos de degradacao (Prometheus Alertmanager)
- Dashboard Grafana para equipe tecnica
- SLA tracking

## 2. Justificativa

- **SLA**: Wanda deve responder em < 5s 95% das vezes
- **Degradacao precoce**: Detectar antes que usuarios percebam
- **Capacidade**: Saber quando escalar
- **Raiz de problemas**: Diagnosticar rapido qual agente esta causando lentidao
- **Historico**: Tendencias de longo prazo

## 3. Escopo

### 3.1 Catalogo Completo de Metricas

#### Metricas de Orquestracao
```python
# Requisicoes totais por tipo e resultado
orchestration_requests_total = Counter(
    "wanda_orchestration_requests_total",
    "Total de requisicoes de orquestracao",
    ["request_type", "routing_method", "status"]
)

# Latencia end-to-end
orchestration_duration = Histogram(
    "wanda_orchestration_duration_seconds",
    "Duracao total da orquestracao",
    ["request_type", "routing_method"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
)

# Consultas ativas
orchestration_in_flight = Gauge(
    "wanda_orchestration_in_flight",
    "Orquestracoes em andamento"
)
```

#### Metricas de Agentes
```python
# Chamadas por agente
agent_calls_total = Counter(
    "wanda_agent_calls_total",
    "Total de chamadas a agentes",
    ["agent", "capability", "status"]
)

# Latencia por agente (percentis via Histogram)
agent_response_duration = Histogram(
    "wanda_agent_response_duration_seconds",
    "Latencia de resposta dos agentes",
    ["agent", "capability"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 15.0, 30.0]
)

# Taxa de erro
agent_error_rate = Gauge(
    "wanda_agent_error_rate",
    "Taxa de erros por agente (ultimos 5min)",
    ["agent"]
)

# Circuit breaker
circuit_breaker_state = Gauge(
    "wanda_circuit_breaker_state",
    "Estado do circuit breaker (0=CLOSED, 1=OPEN, 2=HALF_OPEN)",
    ["agent"]
)

circuit_breaker_transitions_total = Counter(
    "wanda_circuit_breaker_transitions_total",
    "Transicoes do circuit breaker",
    ["agent", "from_state", "to_state"]
)
```

#### Metricas de IPS
```python
ips_cache_hit_total = Counter(
    "wanda_ips_cache_hit_total",
    "Cache hits do IPS",
    ["freshness"]  # fresh, stale
)

ips_cache_miss_total = Counter(
    "wanda_ips_cache_miss_total",
    "Cache misses do IPS",
    ["reason"]  # not_found, expired, error
)

ips_load_duration = Histogram(
    "wanda_ips_load_duration_seconds",
    "Tempo de carregamento do IPS"
)

ips_age_hours = Histogram(
    "wanda_ips_age_hours",
    "Idade do IPS usado em horas",
    buckets=[0.1, 0.5, 1.0, 4.0, 12.0, 24.0, 72.0]
)
```

#### Metricas de Roteamento
```python
routing_decisions_total = Counter(
    "wanda_routing_decisions_total",
    "Decisoes de roteamento",
    ["method", "agents_count", "success"]
)

routing_llm_confidence = Histogram(
    "wanda_routing_llm_confidence",
    "Confianca do LLM no roteamento",
    buckets=[0.1, 0.3, 0.5, 0.7, 0.8, 0.9, 0.95, 1.0]
)

routing_fallback_total = Counter(
    "wanda_routing_fallback_total",
    "Fallbacks de LLM para keyword",
    ["reason"]
)
```

#### Metricas de Alertas
```python
alerts_received_total = Counter(
    "wanda_alerts_received_total",
    "Total de alertas recebidos",
    ["source_agent", "severity"]
)

alerts_pending = Gauge(
    "wanda_alerts_pending",
    "Alertas pendentes",
    ["severity"]
)

alert_acknowledgment_time = Histogram(
    "wanda_alert_acknowledgment_seconds",
    "Tempo para profissional reconhecer alerta",
    ["severity"]
)

alerts_escalated_total = Counter(
    "wanda_alerts_escalated_total",
    "Alertas escalados por nao reconhecimento",
    ["severity"]
)
```

#### Metricas de Workflows
```python
workflow_executions_total = Counter(
    "wanda_workflow_executions_total",
    "Execucoes de workflows LangGraph",
    ["workflow_id", "status"]
)

workflow_duration = Histogram(
    "wanda_workflow_duration_seconds",
    "Duracao de workflows",
    ["workflow_id"]
)

workflow_iterations = Histogram(
    "wanda_workflow_iterations",
    "Iteracoes por workflow",
    ["workflow_id"],
    buckets=[1, 2, 3, 5, 10]
)
```

### 3.2 SLO (Service Level Objectives)

```python
class SLOTracker:
    """
    Rastreia conformidade com SLOs definidos.
    """

    SLOS = {
        "p95_latency": SLO(
            metric="wanda_orchestration_duration_seconds",
            threshold=5.0,
            percentile=0.95,
            window="5m",
            description="95% das requisicoes em < 5s",
        ),
        "availability": SLO(
            metric="wanda_orchestration_requests_total{status='success'}",
            threshold=0.995,    # 99.5%
            window="1h",
            description="99.5% de disponibilidade por hora",
        ),
        "agent_availability": SLO(
            metric="wanda_agent_calls_total{status='success'}",
            threshold=0.98,     # 98% por agente
            window="5m",
            description="98% de sucesso nas chamadas a agentes",
        ),
        "critical_alerts_acknowledgment": SLO(
            metric="wanda_alert_acknowledgment_seconds{severity='critical'}",
            threshold=300,      # 5 minutos
            percentile=0.95,
            window="1d",
            description="95% dos alertas criticos reconhecidos em 5min",
        ),
    }

    async def check_all_slos(self) -> list[SLOStatus]:
        """Verifica conformidade com todos os SLOs."""
```

### 3.3 Alertas Prometheus

```yaml
# prometheus_rules/wanda_alerts.yml
groups:
  - name: wanda_critical
    rules:
      - alert: WandaAgentDown
        expr: wanda_circuit_breaker_state{} == 1
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Agente {{ $labels.agent }} circuit breaker OPEN"
          description: "{{ $labels.agent }} tem circuit breaker aberto ha 2 minutos"

      - alert: WandaHighLatency
        expr: histogram_quantile(0.95, wanda_orchestration_duration_seconds) > 5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Wanda latencia p95 acima de 5s"

      - alert: WandaCriticalAlertsPending
        expr: wanda_alerts_pending{severity="critical"} > 0
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Alertas criticos pendentes ha mais de 5 minutos"

      - alert: WandaIPSCacheHitLow
        expr: rate(wanda_ips_cache_hit_total[5m]) / rate(wanda_ips_cache_miss_total[5m]) < 2
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Taxa de cache hit do IPS baixa"
```

### 3.4 Endpoint de Metricas

```python
# Padrao Prometheus
# GET /metrics → metricas no formato Prometheus

# Endpoint customizado para equipe
# GET /api/v1/metrics/summary → resumo legivel

# Resposta de /api/v1/metrics/summary:
{
    "timestamp": "2026-02-16T10:00:00Z",
    "period": "last_5_minutes",

    "slos": {
        "p95_latency": {"value": 1.2, "threshold": 5.0, "ok": true},
        "availability": {"value": 0.999, "threshold": 0.995, "ok": true},
    },

    "agents": {
        "florence": {"status": "healthy", "p95_ms": 320, "error_rate": 0.001},
        "oswaldo":  {"status": "healthy", "p95_ms": 180, "error_rate": 0.000},
        "geralda":  {"status": "healthy", "p95_ms": 240, "error_rate": 0.002},
        "zilda":    {"status": "healthy", "p95_ms": 150, "error_rate": 0.000},
    },

    "ips_cache": {
        "hit_rate": 0.94,
        "avg_age_hours": 0.8,
    },

    "routing": {
        "llm_rate": 0.85,
        "keyword_rate": 0.15,
        "avg_confidence": 0.91,
    },

    "alerts": {
        "critical_pending": 0,
        "high_pending": 2,
        "avg_ack_time_minutes": 3.2,
    },
}
```

### 3.5 Configuracao

```env
# Prometheus
INTELLICARE_WANDA_METRICS_PORT=9090
INTELLICARE_WANDA_METRICS_PATH=/metrics
INTELLICARE_WANDA_SLO_CHECK_INTERVAL=60

# Alertmanager (opcional)
INTELLICARE_WANDA_ALERTMANAGER_URL=http://alertmanager:9093
```

### 3.6 Endpoints

| Metodo | Path | Descricao |
|--------|------|-----------|
| GET | `/metrics` | Metricas Prometheus |
| GET | `/api/v1/metrics/summary` | Resumo operacional |
| GET | `/api/v1/slos` | Status dos SLOs |
| GET | `/api/v1/slos/history` | Historico de SLO compliance |

## 4. Testes

- Metricas: incremento, labels corretos (8 testes)
- SLOTracker: cada SLO, breach detectado (5 testes)
- Endpoints: metricas, summary, slos (4 testes)
- Integracao: operacao completa gera metricas corretas (3 testes)
- **Total**: 20+ testes

## 5. Criterios de Aceitacao

- [ ] 25+ metricas Prometheus definidas e expostas em `/metrics`
- [ ] 4 SLOs definidos com tracking automatico
- [ ] Regras de alerta Prometheus para situacoes criticas
- [ ] Endpoint `/api/v1/metrics/summary` legivel
- [ ] Metricas de todas as 4 fases (orquestracao, agentes, IPS, routing)
- [ ] Circuit breaker state como metrica Gauge
- [ ] SLO breach detectado e reportado
- [ ] 20+ testes
- [ ] Cobertura >= 85%

## 6. Estimativa de Complexidade

- **Arquivos novos**: ~5
- **Arquivos modificados**: ~6 (orchestrator, agent_client, ips_manager, router, api, docker)
- **Linhas estimadas**: ~800
- **Testes novos**: ~20
