# Checklist Homologacao E2E - Fase 4 (EF-W008/009/010)

## Objetivo
- Validar em ambiente real (Redis/PostgreSQL) os recursos de resiliencia, rastreabilidade e observabilidade da Wanda.

## Pre-requisitos
- Executar sempre via ambiente virtual:
- `.\.venv\Scripts\python.exe --version`
- Redis disponivel e acessivel.
- PostgreSQL disponivel (opcional para Fase 4, recomendado para cenário completo).
- Variaveis de ambiente habilitadas:
- `INTELLICARE_ENABLE_RESILIENCE=true`
- `INTELLICARE_ENABLE_DECISION_TRACING=true`
- `INTELLICARE_ENABLE_METRICS=true`
- `INTELLICARE_ENABLE_REDIS=true`
- `INTELLICARE_ENABLE_LANGGRAPH=true` (para validar metricas de workflow)
- `INTELLICARE_ENABLE_ALERT_HUB=true` (para validar metricas de alertas)

## 1. Smoke de inicializacao
1. Subir API Wanda.
2. Validar:
- `GET /api/v1/health` retorna `status=healthy`.
- `GET /api/v1/info` retorna versao e capabilities.

### Evidencia esperada
- Logs sem erro de inicializacao de `MetricsRegistry`, `DecisionTracer` e `CircuitBreakerManager`.

## 2. Resiliencia (EF-W008)
1. Executar chamadas que induzam falha de modulo (timeout/5xx).
2. Validar endpoints:
- `GET /api/v1/health/ecosystem`
- `GET /api/v1/health/agents/{agent}`
- `POST /api/v1/circuit/{agent}/reset`
3. Verificar fallback parcial no fluxo `/api/v1/chat`.

### Aceite
- Circuit breaker muda de estado e pode ser resetado.
- Chat retorna resposta parcial quando houver fallback.

## 3. Tracing e auditoria (EF-W009)
1. Executar pelo menos 5 chats com cenarios diferentes (sucesso e falha).
2. Validar:
- `GET /api/v1/traces`
- `GET /api/v1/traces/{trace_id}`
- `GET /api/v1/traces/patterns`
- `GET /api/v1/traces/anomalies`
- `GET /api/v1/traces/{trace_id}/fhir`

### Aceite
- Traces contem `routing_method`, chamadas de agente e latencia.
- Export FHIR retorna `resourceType=AuditEvent`.
- Endpoint de anomalias retorna itens quando houver degradacao induzida.

## 4. Metricas e SLO (EF-W010)
1. Gerar carga funcional:
- Chats com sucesso/falha.
- 1 execucao de workflow.
- 1 alerta recebido + ack.
- 1 consulta IPS com miss e hit.
2. Validar:
- `GET /metrics`
- `GET /api/v1/metrics/summary`
- `GET /api/v1/slos`
- `GET /api/v1/slos/history`

### Aceite
- `/metrics` expoe metricas de:
- orquestracao
- agentes
- routing
- IPS
- alertas
- workflows
- `summary` apresenta blocos `agents`, `ips_cache`, `routing`, `alerts`.
- `slos/history` cresce entre chamadas.

## 5. Persistencia Redis (circuit + SLO history)
1. Capturar estado atual:
- `GET /api/v1/slos/history`
2. Reiniciar processo Wanda.
3. Validar novamente:
- `GET /api/v1/slos/history`
- `GET /api/v1/health/ecosystem`

### Aceite
- Historico de SLO permanece apos restart.
- Estado de circuit breaker permanece quando aplicavel.

## 6. Fluxo de workflow (runtime metric)
1. Chamar `POST /api/v1/workflows/execute`.
2. Validar em `/metrics`:
- `wanda_workflow_executions_total`
- `wanda_workflow_duration_seconds`
- `wanda_workflow_iterations`

### Aceite
- Contadores/histogramas incrementam apos execucao.

## 7. Fluxo de alerta (runtime metric)
1. Chamar `POST /api/v1/alerts`.
2. Chamar `PUT /api/v1/alerts/{id}/acknowledge`.
3. Validar em `/metrics`:
- `wanda_alerts_received_total`
- `wanda_alert_acknowledgment_seconds`
- `wanda_alerts_pending`
- `wanda_alerts_escalated_total` (quando houver escalacao)

### Aceite
- Received incrementa no recebimento.
- Ack histogram recebe amostra no acknowledge.
- Pending reduz apos ack/resolve.

## 8. Fluxo IPS (runtime metric)
1. Chamar `GET /api/v1/ips/{patient_id}` duas vezes.
2. Validar em `/metrics`:
- `wanda_ips_cache_miss_total` (primeira)
- `wanda_ips_cache_hit_total` (segunda)
- `wanda_ips_load_duration_seconds`
- `wanda_ips_age_hours` (quando aplicavel)

### Aceite
- Miss + hit observados conforme sequencia.

## 9. Comando rapido de regressao local
- `.\.venv\Scripts\python.exe -m pytest --no-cov tests\test_metrics_registry.py tests\test_tracing.py tests\test_alert_hub.py tests\test_workflow_executor.py tests\test_ips_manager_metrics.py tests\test_phase4_routes.py tests\test_orchestrator_phase4.py -q`

### Aceite
- Suite passa sem regressao.

## Criterio final de aprovacao da Fase 4
- Todos os itens de aceite acima validados.
- Evidencias anexadas (saida de endpoints + logs + dump curto de `/metrics`).
- Atualizar:
- `desenvolvimento/FASE4_HARDENING_STATUS.md` para status `Concluida`.
- `desenvolvimento/VERSIONAMENTO.md` com marco da Fase 4.
