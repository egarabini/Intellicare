# DEM-025 — Observabilidade: Especificação Técnica

## Arquitetura

```
intellicare-service ──→ /metrics (prometheus_fastapi_instrumentator)
postgres            ──→ postgres-exporter ──→ Prometheus
redis               ──→ redis-exporter    ──→ Prometheus
host                ──→ node-exporter     ──→ Prometheus
                                                   ↓
                                             Grafana :3000
```

---

## 1. FastAPI — métricas da aplicação

### Dependência

```bash
pip install prometheus-fastapi-instrumentator==6.1.0
```

Adicionar ao `requirements.txt` ou `pyproject.toml`.

### Instrumentação em `main.py`

```python
# packages/intellicare-core/intellicare_core/main.py
from prometheus_fastapi_instrumentator import Instrumentator

# ... após criar o app FastAPI ...

Instrumentator(
    should_group_status_codes=False,
    should_ignore_untemplated=True,
    should_respect_env_var=True,
    should_instrument_requests_inprogress=True,
    excluded_handlers=["/health", "/metrics"],
    env_var_name="ENABLE_METRICS",
    inprogress_name="intellicare_requests_inprogress",
    inprogress_labels=True,
).instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)
```

Adicionar variável ao `.env`:
```
ENABLE_METRICS=true
```

O endpoint `/metrics` ficará disponível em `http://localhost:9000/metrics`.

---

## 2. docker-compose.yml — novos serviços

Adicionar ao `infra/docker-compose.yml` (dentro de `services:`):

```yaml
  prometheus:
    image: prom/prometheus:v2.51.0
    container_name: intellicare-prometheus
    restart: unless-stopped
    command:
      - "--config.file=/etc/prometheus/prometheus.yml"
      - "--storage.tsdb.path=/prometheus"
      - "--web.console.libraries=/etc/prometheus/console_libraries"
      - "--web.console.templates=/etc/prometheus/consoles"
      - "--storage.tsdb.retention.time=15d"
      - "--web.enable-lifecycle"
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus
    ports:
      - "${PROMETHEUS_PORT:-9090}:9090"
    networks:
      - intellicare-net
    depends_on:
      - intellicare-service
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://localhost:9090/-/healthy"]
      interval: 15s
      timeout: 5s
      retries: 3

  grafana:
    image: grafana/grafana:10.4.0
    container_name: intellicare-grafana
    restart: unless-stopped
    environment:
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_PASSWORD:-admin}
      GF_USERS_ALLOW_SIGN_UP: "false"
      GF_INSTALL_PLUGINS: grafana-piechart-panel
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning:ro
      - ./grafana/dashboards:/var/lib/grafana/dashboards:ro
    ports:
      - "${GRAFANA_PORT:-3000}:3000"
    networks:
      - intellicare-net
    depends_on:
      - prometheus
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://localhost:3000/api/health"]
      interval: 15s
      timeout: 5s
      retries: 3

  postgres-exporter:
    image: prometheuscommunity/postgres-exporter:v0.15.0
    container_name: intellicare-postgres-exporter
    restart: unless-stopped
    environment:
      DATA_SOURCE_NAME: "postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}?sslmode=disable"
    networks:
      - intellicare-net
    depends_on:
      postgres:
        condition: service_healthy

  redis-exporter:
    image: oliver006/redis_exporter:v1.59.0
    container_name: intellicare-redis-exporter
    restart: unless-stopped
    environment:
      REDIS_ADDR: "redis://redis:6379"
      REDIS_PASSWORD: ${REDIS_PASSWORD}
    networks:
      - intellicare-net
    depends_on:
      - redis

  node-exporter:
    image: prom/node-exporter:v1.7.0
    container_name: intellicare-node-exporter
    restart: unless-stopped
    command:
      - "--path.procfs=/host/proc"
      - "--path.rootfs=/rootfs"
      - "--path.sysfs=/host/sys"
      - "--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)"
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    networks:
      - intellicare-net
```

Adicionar ao bloco `volumes:`:
```yaml
  prometheus_data:
  grafana_data:
```

---

## 3. infra/prometheus/prometheus.yml

Criar arquivo `infra/prometheus/prometheus.yml`:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    monitor: 'intellicare-monitor'

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'intellicare-api'
    static_configs:
      - targets: ['intellicare-service:8000']
    metrics_path: /metrics

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']

  - job_name: 'node'
    static_configs:
      - targets: ['node-exporter:9100']
```

---

## 4. infra/grafana/provisioning/

### datasources/prometheus.yml

```yaml
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    jsonData:
      timeInterval: "15s"
```

### dashboards/dashboards.yml

```yaml
apiVersion: 1
providers:
  - name: 'IntelliCare'
    orgId: 1
    folder: 'IntelliCare'
    type: file
    disableDeletion: false
    updateIntervalSeconds: 30
    options:
      path: /var/lib/grafana/dashboards
```

---

## 5. infra/grafana/dashboards/intellicare-overview.json

Criar dashboard JSON com os seguintes panels. Use o editor do Grafana para criar e depois exportar o JSON, ou use este template como base:

**Panels obrigatórios:**

| Panel | Tipo | Query PromQL |
|-------|------|--------------|
| API Requests/s | Stat | `rate(http_requests_total{job="intellicare-api"}[1m])` |
| API Error Rate % | Gauge | `rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) * 100` |
| Latência p95 (ms) | Stat | `histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) * 1000` |
| PostgreSQL Connections | Gauge | `pg_stat_activity_count` |
| Redis Memory Used | Stat | `redis_memory_used_bytes / 1024 / 1024` |
| CPU Host % | Time series | `100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[1m])) * 100)` |
| RAM Available | Stat | `node_memory_MemAvailable_bytes / 1024 / 1024 / 1024` |
| Requests por Endpoint | Table | `topk(10, sum by (handler) (rate(http_requests_total[5m])))` |

**Dica:** Importe o dashboard ID `1860` (Node Exporter Full) e `9628` (PostgreSQL Database) da galeria pública do Grafana para ter dashboards de infra completos sem criar do zero.

---

## 6. Variáveis de ambiente (.env)

Adicionar ao `infra/.env`:

```env
# Observabilidade
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
GRAFANA_PASSWORD=IntelliCare@Grafana2025
ENABLE_METRICS=true
```

---

## Estrutura de arquivos a criar

```
infra/
├── prometheus/
│   └── prometheus.yml
├── grafana/
│   ├── provisioning/
│   │   ├── datasources/
│   │   │   └── prometheus.yml
│   │   └── dashboards/
│   │       └── dashboards.yml
│   └── dashboards/
│       └── intellicare-overview.json
```

---

## Sequência de execução

```bash
# 1. Instalar dependência Python
pip install prometheus-fastapi-instrumentator==6.1.0

# 2. Aplicar instrumentação no main.py

# 3. Criar estrutura de arquivos Prometheus/Grafana

# 4. Rebuild do intellicare-service
docker compose --env-file infra/.env -f infra/docker-compose.yml build intellicare-service

# 5. Subir novos serviços
docker compose --env-file infra/.env -f infra/docker-compose.yml up -d

# 6. Verificar targets do Prometheus
# Abrir: http://localhost:9090/targets
# Todos devem aparecer como "UP"

# 7. Abrir Grafana
# http://localhost:3000 → admin / IntelliCare@Grafana2025
# Importar dashboard IDs: 1860, 9628
```

---

## Validação

```bash
# Verificar endpoint de métricas da API
curl http://localhost:9000/metrics | grep http_requests_total

# Verificar Prometheus scraping
curl "http://localhost:9090/api/v1/query?query=up" | python -m json.tool

# Verificar Grafana
curl http://localhost:3000/api/health
```

---

## Observações

- O `node-exporter` precisa de acesso a `/proc`, `/sys` e `/` do host — funciona no Linux/Mac. Em Windows com Docker Desktop, usar a imagem sem os volume mounts de host (métricas de container apenas).
- Para produção (DEM-023), adicionar as labels do Traefik ao Prometheus ou usar service discovery Docker.
- O Grafana persiste dashboards criados manualmente no volume `grafana_data` — fazer backup antes de destruir o volume.
