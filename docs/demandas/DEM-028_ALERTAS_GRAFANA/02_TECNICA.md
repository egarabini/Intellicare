# DEM-028 — Alertas Grafana — Especificação Técnica

## 1. Arquitetura

```
Prometheus ──scrape──▶ métricas
                           │
                    avalia regras PromQL
                           │
                     Grafana Alerting ──▶ Contact Points
                                              ├── SMTP (e-mail)
                                              └── Slack (webhook)
```

O Grafana v10.4 (já instalado) inclui o motor de alertas unificado — **não é necessário Alertmanager separado**. As regras são definidas como `Grafana Managed Alerts` e armazenadas via provisioning em arquivos YAML.

---

## 2. Estrutura de arquivos novos

```
infra/grafana/
├── provisioning/
│   ├── alerting/
│   │   ├── contact-points.yaml    # canais de notificação (e-mail + Slack)
│   │   ├── notification-policies.yaml  # roteamento: crítico → todos, warning → e-mail
│   │   └── alert-rules.yaml       # 9 regras de alerta
│   └── datasources/
│       └── prometheus.yaml        # já existente
└── dashboards/
    └── ...                        # já existentes
```

---

## 3. `contact-points.yaml`

```yaml
apiVersion: 1

contactPoints:
  - orgId: 1
    name: email-ops
    receivers:
      - uid: email-ops-uid
        type: email
        settings:
          addresses: "${GRAFANA_ALERT_EMAIL}"
          subject: "[IntelliCare] {{ .CommonLabels.severity | toUpper }}: {{ .CommonLabels.alertname }}"

  - orgId: 1
    name: slack-ops
    receivers:
      - uid: slack-ops-uid
        type: slack
        settings:
          url: "${GRAFANA_SLACK_WEBHOOK_URL}"
          channel: "${GRAFANA_SLACK_CHANNEL:#intellicare-alertas}"
          title: "{{ if eq .CommonLabels.severity \"critical\" }}🔴 CRÍTICO{{ else }}⚠️ WARNING{{ end }}: {{ .CommonLabels.alertname }}"
          text: "Condição: {{ .CommonAnnotations.description }}\nValor: {{ .CommonAnnotations.value }}"
          mentionChannel: "{{ if eq .CommonLabels.severity \"critical\" }}here{{ end }}"
          color: "{{ if eq .CommonLabels.severity \"critical\" }}danger{{ else }}warning{{ end }}"
```

---

## 4. `notification-policies.yaml`

```yaml
apiVersion: 1

policies:
  - orgId: 1
    receiver: email-ops      # default: tudo vai por e-mail
    group_by: [alertname, severity]
    group_wait: 30s
    group_interval: 5m
    repeat_interval: 4h
    routes:
      - receiver: slack-ops  # críticos também vão para Slack
        matchers:
          - severity = critical
        continue: true       # continua para o receiver pai (email) também
```

---

## 5. `alert-rules.yaml` — 9 regras

```yaml
apiVersion: 1

groups:
  - orgId: 1
    name: infraestrutura
    folder: IntelliCare
    interval: 1m
    rules:

      - uid: alt-i01
        title: "Serviço API Down"
        condition: C
        data:
          - refId: A
            queryType: ''
            relativeTimeRange: {from: 300, to: 0}
            datasourceUid: prometheus
            model:
              expr: 'up{job="intellicare-api"}'
          - refId: C
            datasourceUid: __expr__
            model:
              type: threshold
              conditions: [{evaluator: {params: [1], type: lt}}]
        noDataState: Alerting
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "API do IntelliCare está fora do ar"
          description: "up{job=intellicare-api} = 0 por mais de 1 minuto"

      - uid: alt-i02
        title: "CPU Alta (> 85%)"
        condition: C
        data:
          - refId: A
            relativeTimeRange: {from: 300, to: 0}
            datasourceUid: prometheus
            model:
              expr: '100 - (avg by(instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)'
          - refId: C
            datasourceUid: __expr__
            model:
              type: threshold
              conditions: [{evaluator: {params: [85], type: gt}}]
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "CPU acima de 85%"
          description: "Uso de CPU = {{ $values.A }}% nos últimos 5 minutos"

      - uid: alt-i03
        title: "Memória Alta (> 90%)"
        condition: C
        data:
          - refId: A
            relativeTimeRange: {from: 300, to: 0}
            datasourceUid: prometheus
            model:
              expr: '(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100'
          - refId: C
            datasourceUid: __expr__
            model:
              type: threshold
              conditions: [{evaluator: {params: [90], type: gt}}]
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Memória acima de 90%"
          description: "Uso de memória = {{ $values.A }}%"

      - uid: alt-i04
        title: "Disco Crítico (< 10% livre)"
        condition: C
        data:
          - refId: A
            relativeTimeRange: {from: 300, to: 0}
            datasourceUid: prometheus
            model:
              expr: '(node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}) * 100'
          - refId: C
            datasourceUid: __expr__
            model:
              type: threshold
              conditions: [{evaluator: {params: [10], type: lt}}]
        for: 10m
        labels:
          severity: critical
        annotations:
          summary: "Espaço em disco crítico"
          description: "Espaço livre em / = {{ $values.A }}%"

      - uid: alt-i05
        title: "PostgreSQL Down"
        condition: C
        data:
          - refId: A
            relativeTimeRange: {from: 300, to: 0}
            datasourceUid: prometheus
            model:
              expr: 'pg_up'
          - refId: C
            datasourceUid: __expr__
            model:
              type: threshold
              conditions: [{evaluator: {params: [1], type: lt}}]
        noDataState: Alerting
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "PostgreSQL está inacessível"
          description: "pg_up = 0"

      - uid: alt-i06
        title: "Redis Down"
        condition: C
        data:
          - refId: A
            relativeTimeRange: {from: 300, to: 0}
            datasourceUid: prometheus
            model:
              expr: 'redis_up'
          - refId: C
            datasourceUid: __expr__
            model:
              type: threshold
              conditions: [{evaluator: {params: [1], type: lt}}]
        noDataState: Alerting
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Redis está inacessível"
          description: "redis_up = 0"

      - uid: alt-a01
        title: "Taxa de Erros HTTP Alta (> 5%)"
        condition: C
        data:
          - refId: A
            relativeTimeRange: {from: 300, to: 0}
            datasourceUid: prometheus
            model:
              expr: 'rate(http_requests_total{status=~"5.."}[2m]) / rate(http_requests_total[2m]) * 100'
          - refId: C
            datasourceUid: __expr__
            model:
              type: threshold
              conditions: [{evaluator: {params: [5], type: gt}}]
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "Muitos erros HTTP 5xx"
          description: "Taxa de erro 5xx = {{ $values.A }}% nos últimos 2 minutos"

      - uid: alt-a02
        title: "Latência API Alta (p95 > 2s)"
        condition: C
        data:
          - refId: A
            relativeTimeRange: {from: 300, to: 0}
            datasourceUid: prometheus
            model:
              expr: 'histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))'
          - refId: C
            datasourceUid: __expr__
            model:
              type: threshold
              conditions: [{evaluator: {params: [2], type: gt}}]
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Latência p95 acima de 2s"
          description: "p95 latência = {{ $values.A }}s"

      - uid: alt-a03
        title: "Keycloak Down"
        condition: C
        data:
          - refId: A
            relativeTimeRange: {from: 300, to: 0}
            datasourceUid: prometheus
            model:
              expr: 'up{job="keycloak"}'
          - refId: C
            datasourceUid: __expr__
            model:
              type: threshold
              conditions: [{evaluator: {params: [1], type: lt}}]
        noDataState: Alerting
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Keycloak está inacessível"
          description: "up{job=keycloak} = 0"
```

---

## 6. Variáveis de ambiente (`.env` / `.env.staging`)

```env
# DEM-028 — Alertas Grafana
GRAFANA_ALERT_EMAIL=egarabini@gmail.com
GRAFANA_SMTP_HOST=smtp.gmail.com:587
GRAFANA_SMTP_USER=alertas@intellicare.ia.br
GRAFANA_SMTP_PASSWORD=<app-password>
GRAFANA_SLACK_WEBHOOK_URL=https://hooks.slack.com/services/xxx/yyy/zzz
GRAFANA_SLACK_CHANNEL=#intellicare-alertas
```

---

## 7. Alteração no `docker-compose.yml` — Grafana

Adicionar configuração SMTP e provisioning ao serviço `grafana`:

```yaml
grafana:
  environment:
    GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_PASSWORD:-admin}
    GF_USERS_ALLOW_SIGN_UP: "false"
    GF_INSTALL_PLUGINS: grafana-piechart-panel
    # SMTP para alertas
    GF_SMTP_ENABLED: "true"
    GF_SMTP_HOST: ${GRAFANA_SMTP_HOST:-smtp.gmail.com:587}
    GF_SMTP_USER: ${GRAFANA_SMTP_USER:-}
    GF_SMTP_PASSWORD: ${GRAFANA_SMTP_PASSWORD:-}
    GF_SMTP_FROM_ADDRESS: ${GRAFANA_SMTP_USER:-alertas@intellicare.ia.br}
    GF_SMTP_FROM_NAME: "IntelliCare Alertas"
    GF_SMTP_STARTTLS_POLICY: "MandatoryStartTLS"
  volumes:
    - grafana_data:/var/lib/grafana
    - ./grafana/provisioning:/etc/grafana/provisioning:ro
    - ./grafana/dashboards:/var/lib/grafana/dashboards:ro
```

O Grafana carrega automaticamente os arquivos em `provisioning/alerting/` ao iniciar.

---

## 8. Checklist de entrega

- [ ] `infra/grafana/provisioning/alerting/contact-points.yaml` criado
- [ ] `infra/grafana/provisioning/alerting/notification-policies.yaml` criado
- [ ] `infra/grafana/provisioning/alerting/alert-rules.yaml` com 9 regras
- [ ] `infra/docker-compose.yml`: GF_SMTP_* adicionado ao serviço grafana
- [ ] `.env.example` atualizado com as variáveis DEM-028
- [ ] `docker compose up -d grafana` aplica as regras sem restart manual
- [ ] Grafana UI → Alerting → Alert rules mostra 9 regras no folder "IntelliCare"
- [ ] Teste manual: parar `intellicare-service`, aguardar 1 min → e-mail recebido
- [ ] Teste manual: restaurar serviço → e-mail de resolução recebido
- [ ] Slack webhook configurado e testado (opcional se não tiver workspace)
