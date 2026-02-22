# D7 - Dashboard e Monitoramento - Guia Operacional

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Configuração](#configuração)
3. [Dashboards Grafana](#dashboards-grafana)
4. [Métricas Prometheus](#métricas-prometheus)
5. [Alertas](#alertas)
6. [Health Checks](#health-checks)
7. [Troubleshooting](#troubleshooting)

---

## 1. Visão Geral

O módulo de Dashboard e Monitoramento (D7) fornece observabilidade completa para o sistema de comunicação IntelliCare.

### Componentes

- **Prometheus**: Coleta de métricas
- **Grafana**: Visualização de dashboards
- **AlertManager**: Gerenciamento de alertas
- **Health Checks**: Endpoints de saúde do serviço
- **Materialized Views**: Views otimizadas para queries analíticas

---

## 2. Configuração

### 2.1. Variáveis de Ambiente

```bash
# Monitoring
MONITORING_METRICS_ENABLED=true
MONITORING_HEALTH_CHECK_INTERVAL_SECONDS=30
MONITORING_DB_HEALTH_TIMEOUT_SECONDS=5
MONITORING_REDIS_HEALTH_TIMEOUT_SECONDS=3
MONITORING_CHANNEL_HEALTH_TIMEOUT_SECONDS=10
MONITORING_CHANNEL_HEALTH_CACHE_TTL_SECONDS=60
MONITORING_STRUCTURED_LOGGING=true
```

### 2.2. Prometheus Configuration

Adicionar job no `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'comunicacao'
    scrape_interval: 30s
    static_configs:
      - targets: ['localhost:8005']
    metrics_path: '/metrics'
```

### 2.3. AlertManager Configuration

Carregar alertas do arquivo `prometheus/alerts/comunicacao.yml`:

```yaml
rule_files:
  - 'alerts/comunicacao.yml'
```

---

## 3. Dashboards Grafana

### 3.1. Importar Dashboards

Os dashboards estão em `comunicacao/dashboards/*.json`:

1. **comunicacao_overview.json** - Overview geral de comunicações
2. **comunicacao_channels.json** - Detalhamento por canal
3. **comunicacao_teleconsulta.json** - Métricas de teleconsultas
4. **comunicacao_lgpd.json** - Compliance LGPD
5. **comunicacao_events.json** - Eventos Redis
6. **comunicacao_sla.json** - SLA por equipe
7. **comunicacao_bot.json** - Bot @intellicare
8. **comunicacao_health.json** - Health & Performance

**Importar via UI**:
1. Grafana → Dashboards → Import
2. Upload JSON file
3. Selecionar datasource Prometheus
4. Salvar

**Importar via API**:
```bash
curl -X POST http://grafana:3000/api/dashboards/db \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $GRAFANA_API_KEY" \
  -d @comunicacao/dashboards/comunicacao_overview.json
```

### 3.2. Datasources Necessários

- **Prometheus**: Métricas em tempo real
- **PostgreSQL**: Queries analíticas (SLA, LGPD compliance)

---

## 4. Métricas Prometheus

### 4.1. Counters

| Métrica | Descrição | Labels |
|---------|-----------|--------|
| `comm_messages_total` | Total de mensagens processadas | channel, severity, status, intent_type |
| `comm_channel_fallback_total` | Total de fallbacks entre canais | from_channel, to_channel, reason |
| `comm_lgpd_blocked_total` | Total bloqueados por LGPD | reason, severity |
| `comm_lgpd_override_total` | Total de overrides LGPD | legal_basis, severity |
| `comm_bot_commands_total` | Total de comandos do bot | command, status |
| `comm_events_processed_total` | Total de eventos Redis | event_type, status |
| `comm_teleconsult_created_total` | Total de teleconsultas criadas | room_type, provider, status |

### 4.2. Histograms

| Métrica | Descrição | Labels | Buckets |
|---------|-----------|--------|---------|
| `comm_message_latency_seconds` | Latência de envio de mensagem | channel | 0.1, 0.5, 1, 2, 5, 10, 30, 60 |
| `comm_api_request_duration_seconds` | Duração de requisições HTTP | method, endpoint, status_code | 0.01, 0.05, 0.1, 0.5, 1, 2, 5 |
| `comm_event_processing_duration_seconds` | Duração de processamento de eventos | event_type | 0.1, 0.5, 1, 2, 5, 10 |

### 4.3. Gauges

| Métrica | Descrição | Labels |
|---------|-----------|--------|
| `comm_db_connections_active` | Conexões ativas ao PostgreSQL | - |
| `comm_redis_connections_active` | Conexões ativas ao Redis | - |
| `comm_pending_intents` | Intents pendentes de processamento | - |
| `comm_active_teleconsult_rooms` | Salas de teleconsulta ativas | - |
| `comm_audit_chain_integrity` | Integridade da hash chain (1=OK, 0=BROKEN) | - |
| `comm_dispatcher_health` | Health dos dispatchers (1=healthy, 0=unhealthy) | channel |
| `comm_redis_consumer_lag` | Lag do consumer Redis | - |

### 4.4. Queries Úteis

**Taxa de sucesso de mensagens (24h)**:
```promql
sum(increase(comm_messages_total{status="delivered"}[24h])) / sum(increase(comm_messages_total[24h])) * 100
```

**Latência p95 por canal**:
```promql
histogram_quantile(0.95, sum by(channel, le)(rate(comm_message_latency_seconds_bucket[5m])))
```

**Throughput de mensagens (msg/s)**:
```promql
sum(rate(comm_messages_total[5m]))
```

---

## 5. Alertas

### 5.1. Alertas Críticos

| Alerta | Condição | Ação |
|--------|----------|------|
| `ComunicacaoServiceDown` | Serviço DOWN por 1min | Verificar logs, reiniciar serviço |
| `ComunicacaoHighFailureRate` | >10% falhas por 5min | Verificar dispatchers, logs de erro |
| `HighCriticalOverrideRate` | >5 overrides CRITICAL/s | Investigar uso inadequado de overrides |
| `AuditChainIntegrityBroken` | Hash chain quebrada | Investigação urgente, possível violação |
| `DatabaseConnectionPoolExhausted` | >90 conexões ativas | Escalar pool, investigar vazamento |

### 5.2. Alertas de Warning

| Alerta | Condição | Ação |
|--------|----------|------|
| `HighChannelLatency` | p95 >30s por 10min | Verificar health do canal |
| `LGPDBlockedSpike` | >10 bloqueios/s | Verificar configurações de consentimento |
| `RedisConsumerLag` | Lag >1000 msgs | Escalar consumer, verificar Redis |
| `DispatcherUnhealthy` | Dispatcher unhealthy por 3min | Verificar health check do dispatcher |
| `HighPendingIntents` | >500 intents pendentes | Verificar workers, escalar processamento |

---

## 6. Health Checks

### 6.1. Endpoints

| Endpoint | Descrição | Uso |
|----------|-----------|-----|
| `GET /api/v1/health` | Health geral do serviço | Monitoramento geral |
| `GET /api/v1/health/db` | Health do PostgreSQL | Verificar banco |
| `GET /api/v1/health/redis` | Health do Redis | Verificar cache |
| `GET /api/v1/health/channels` | Health de todos os canais | Verificar dispatchers |
| `GET /api/v1/health/channels/{channel}` | Health de um canal específico | Debug de canal |
| `GET /api/v1/health/liveness` | Liveness probe (K8s) | Kubernetes liveness |
| `GET /api/v1/health/readiness` | Readiness probe (K8s) | Kubernetes readiness |

### 6.2. Kubernetes Probes

```yaml
livenessProbe:
  httpGet:
    path: /api/v1/health/liveness
    port: 8005
  initialDelaySeconds: 30
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3

readinessProbe:
  httpGet:
    path: /api/v1/health/readiness
    port: 8005
  initialDelaySeconds: 10
  periodSeconds: 5
  timeoutSeconds: 3
  failureThreshold: 2
```

---

## 7. Troubleshooting

### 7.1. Métricas Não Aparecem no Prometheus

**Sintomas**: Endpoint `/metrics` retorna vazio ou métricas não aparecem no Prometheus

**Soluções**:
1. Verificar se `MONITORING_METRICS_ENABLED=true`
2. Verificar se middleware está registrado no app
3. Verificar scrape config do Prometheus
4. Verificar logs do Prometheus: `docker logs prometheus`

### 7.2. Dashboards Não Carregam Dados

**Sintomas**: Painéis vazios ou "No data"

**Soluções**:
1. Verificar datasource Prometheus configurado corretamente
2. Verificar queries PromQL no painel
3. Verificar range de tempo selecionado
4. Verificar se métricas existem: `curl http://localhost:8005/metrics | grep comm_`

### 7.3. Materialized Views Desatualizadas

**Sintomas**: Dados antigos nos dashboards de SLA/LGPD

**Soluções**:
1. Executar refresh manual:
   ```sql
   SELECT comunicacao_analitico.refresh_materialized_views();
   ```
2. Verificar cron job:
   ```bash
   crontab -l | grep refresh_materialized_views
   ```
3. Verificar logs do script:
   ```bash
   tail -f /var/log/intellicare/comunicacao_mv_refresh.log
   ```

### 7.4. Alertas Não Disparam

**Sintomas**: Condições de alerta atingidas mas notificações não chegam

**Soluções**:
1. Verificar se AlertManager está rodando
2. Verificar configuração de notificações no AlertManager
3. Verificar regras carregadas: `http://prometheus:9090/rules`
4. Verificar alertas ativos: `http://prometheus:9090/alerts`

### 7.5. High Memory Usage

**Sintomas**: Uso de memória crescente, OOM kills

**Soluções**:
1. Verificar métricas de memória:
   ```promql
   process_resident_memory_bytes{job="comunicacao"} / 1024 / 1024
   ```
2. Verificar pool de conexões DB/Redis
3. Verificar cache de health checks (TTL configurado?)
4. Reiniciar serviço se necessário

### 7.6. Dispatcher Health Sempre Unhealthy

**Sintomas**: `comm_dispatcher_health{channel="X"} == 0` persistente

**Soluções**:
1. Verificar configuração do dispatcher
2. Testar health check manualmente:
   ```bash
   curl http://localhost:8005/api/v1/health/channels/rocketchat
   ```
3. Verificar logs do dispatcher
4. Verificar conectividade com serviço externo (Rocket.Chat, SMTP, etc.)

---

## 8. Manutenção

### 8.1. Refresh de Materialized Views

**Manual**:
```bash
# Via script Python
python scripts/refresh_materialized_views.py

# Via script Bash
./scripts/refresh_materialized_views.sh

# Via SQL direto
psql -d intellicare -c "SELECT comunicacao_analitico.refresh_materialized_views();"
```

**Automático (Cron)**:
```bash
# Adicionar ao crontab (refresh a cada hora)
0 * * * * /path/to/scripts/refresh_materialized_views.sh >> /var/log/intellicare/comunicacao_mv_refresh.log 2>&1
```

### 8.2. Limpeza de Métricas Antigas

Prometheus retém métricas por período configurado (padrão: 15 dias).

Para ajustar retenção:
```yaml
# prometheus.yml
storage:
  tsdb:
    retention.time: 30d
    retention.size: 50GB
```

### 8.3. Backup de Dashboards

```bash
# Exportar todos os dashboards
for dashboard in comunicacao/dashboards/*.json; do
  cp "$dashboard" "/backup/grafana/$(date +%Y%m%d)/"
done
```

---

## 9. Referências

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [PromQL Cheat Sheet](https://promlabs.com/promql-cheat-sheet/)
- [PostgreSQL Materialized Views](https://www.postgresql.org/docs/current/rules-materializedviews.html)

---

**Última Atualização**: 2026-02-17
**Responsável**: Equipe IntelliCare

