# D7 - Dashboard e Monitoramento

## 📊 Visão Geral

Módulo de observabilidade completa para o sistema de comunicação IntelliCare, fornecendo métricas, dashboards, alertas e health checks.

---

## 🎯 Objetivos

- ✅ Coletar métricas de todas as operações de comunicação
- ✅ Visualizar dados em dashboards Grafana
- ✅ Alertar sobre problemas críticos e degradações
- ✅ Monitorar health de todos os componentes
- ✅ Fornecer dados analíticos via materialized views

---

## 📦 Componentes

### 1. Metrics Infrastructure (D7.1)

**Arquivos**:
- `comunicacao/monitoring/config.py` - Configuração de monitoramento
- `comunicacao/monitoring/metrics.py` - Definição de 15 métricas Prometheus
- `comunicacao/monitoring/middleware.py` - Middleware HTTP + collectors
- `comunicacao/monitoring/__init__.py` - Exports do módulo

**Métricas** (15 total):
- **7 Counters**: messages_total, channel_fallback_total, lgpd_blocked_total, lgpd_override_total, bot_commands_total, events_processed_total, teleconsult_created_total
- **3 Histograms**: message_latency_seconds, api_request_duration_seconds, event_processing_duration_seconds
- **5 Gauges**: db_connections_active, redis_connections_active, pending_intents, active_teleconsult_rooms, audit_chain_integrity, dispatcher_health, redis_consumer_lag

### 2. Health Checks (D7.2)

**Arquivos**:
- `comunicacao/monitoring/health.py` - HealthCheckService
- `comunicacao/api/health_routes.py` - 7 endpoints de health

**Endpoints**:
- `GET /api/v1/health` - Health geral
- `GET /api/v1/health/db` - PostgreSQL
- `GET /api/v1/health/redis` - Redis
- `GET /api/v1/health/channels` - Todos os canais
- `GET /api/v1/health/channels/{channel}` - Canal específico
- `GET /api/v1/health/liveness` - Kubernetes liveness probe
- `GET /api/v1/health/readiness` - Kubernetes readiness probe

### 3. Grafana Dashboards (D7.3)

**Arquivos** (8 dashboards):
1. `comunicacao/dashboards/comunicacao_overview.json` - Overview geral
2. `comunicacao/dashboards/comunicacao_channels.json` - Detalhamento por canal
3. `comunicacao/dashboards/comunicacao_teleconsulta.json` - Teleconsultas
4. `comunicacao/dashboards/comunicacao_lgpd.json` - LGPD Compliance
5. `comunicacao/dashboards/comunicacao_events.json` - Eventos Redis
6. `comunicacao/dashboards/comunicacao_sla.json` - SLA por equipe
7. `comunicacao/dashboards/comunicacao_bot.json` - Bot @intellicare
8. `comunicacao/dashboards/comunicacao_health.json` - Service Health

### 4. Prometheus Alerts (D7.4)

**Arquivo**:
- `prometheus/alerts/comunicacao.yml` - 14 regras de alerta

**Alertas Críticos**:
- ComunicacaoServiceDown
- ComunicacaoHighFailureRate
- HighCriticalOverrideRate
- AuditChainIntegrityBroken
- DatabaseConnectionPoolExhausted

**Alertas Warning**:
- HighChannelLatency
- LGPDBlockedSpike
- RedisConsumerLag
- DispatcherUnhealthy
- HighPendingIntents
- HighAPIErrorRate
- BotCommandFailureRate
- TeleconsultRoomCreationFailure

### 5. Materialized Views (D7.5)

**Arquivos**:
- `alembic/versions/007_create_materialized_views.py` - Migration
- `scripts/refresh_materialized_views.sh` - Script Bash de refresh
- `scripts/refresh_materialized_views.py` - Script Python de refresh

**Views**:
- `comunicacao_analitico.team_communication_sla` - Dados de SLA por equipe
- `comunicacao_analitico.lgpd_compliance_view` - Compliance LGPD

### 6. Documentation (D7.6)

**Arquivos**:
- `docs/07_dashboard_monitoramento/OPERACAO.md` - Guia operacional completo
- `docs/07_dashboard_monitoramento/README.md` - Este arquivo

---

## 🚀 Quick Start

### 1. Configurar Variáveis de Ambiente

```bash
export MONITORING_METRICS_ENABLED=true
export MONITORING_HEALTH_CHECK_INTERVAL_SECONDS=30
export MONITORING_DB_HEALTH_TIMEOUT_SECONDS=5
export MONITORING_REDIS_HEALTH_TIMEOUT_SECONDS=3
export MONITORING_CHANNEL_HEALTH_TIMEOUT_SECONDS=10
export MONITORING_CHANNEL_HEALTH_CACHE_TTL_SECONDS=60
```

### 2. Executar Migrations

```bash
alembic upgrade head
```

### 3. Configurar Prometheus

Adicionar ao `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'comunicacao'
    scrape_interval: 30s
    static_configs:
      - targets: ['localhost:8005']
    metrics_path: '/metrics'

rule_files:
  - 'alerts/comunicacao.yml'
```

### 4. Importar Dashboards no Grafana

```bash
# Via UI: Dashboards → Import → Upload JSON
# Ou via API:
for dashboard in comunicacao/dashboards/*.json; do
  curl -X POST http://grafana:3000/api/dashboards/db \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $GRAFANA_API_KEY" \
    -d @"$dashboard"
done
```

### 5. Configurar Refresh de Materialized Views

```bash
# Adicionar ao crontab
crontab -e

# Adicionar linha:
0 * * * * /path/to/scripts/refresh_materialized_views.sh >> /var/log/intellicare/comunicacao_mv_refresh.log 2>&1
```

---

## 📈 Estatísticas

| Métrica | Valor |
|---------|-------|
| **Arquivos Criados** | 20 |
| **Linhas de Código** | ~2,500 |
| **Métricas Prometheus** | 15 |
| **Dashboards Grafana** | 8 |
| **Alertas Configurados** | 14 |
| **Health Endpoints** | 7 |
| **Materialized Views** | 2 |

---

## 📚 Documentação Adicional

- [OPERACAO.md](./OPERACAO.md) - Guia operacional completo
- [Prometheus Metrics Reference](../../comunicacao/monitoring/metrics.py)
- [Health Check Service](../../comunicacao/monitoring/health.py)

---

**Status**: ✅ **COMPLETO - 100%**  
**Data de Conclusão**: 2026-02-17  
**Responsável**: Equipe IntelliCare

