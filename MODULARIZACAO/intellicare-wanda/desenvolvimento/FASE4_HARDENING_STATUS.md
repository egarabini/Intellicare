# Fase 4 - Hardening (EF-W008/009/010)

## Data
- 2026-02-17

## Status Geral
- Em progresso acelerado
- Blocos implementados nesta rodada: resiliencia no registry, rastreabilidade expandida, observabilidade/SLO endpoints

## Concluido
- Instrumentacao runtime dos produtores reais:
- `IPSManager` agora registra:
- `record_ips_cache_hit(...)`
- `record_ips_cache_miss(...)`
- `record_ips_load(...)`
- `AlertHub` agora registra:
- `record_alert_received(...)`
- `record_alert_ack(...)` (tempo de ack estimado por recepcao/ack no hub)
- `record_alert_escalated(...)`
- `set_alerts_pending(...)` por severidade (refresh automatico)
- `WorkflowExecutor` agora registra:
- `record_workflow_execution(...)` para sucesso/falha
- Wiring no orchestrator:
- quando metricas estao ativas, injeta registry em `IPSManager`, `AlertHub` e `WorkflowExecutor`
- `app.state.metrics_registry` exposto no startup
- Historico de SLO com persistencia:
- `InMemorySLOHistoryStore` e `RedisSLOHistoryStore` em `wanda/observability/slo_store.py`
- `MetricsRegistry` agora aceita `history_store` + `history_limit`
- `slos_snapshot()` persiste no store
- `slos_history()` consulta store persistente
- `WandaOrchestrator` conectado para usar `RedisSLOHistoryStore` quando `enable_redis=true`
- Novas configs:
- `metrics_history_key`
- `metrics_history_max_items`
- Anomalias EF-W009 fortalecidas:
- Filtro por janela real (`period_days`)
- Detecao de `latency_regression` (p95 recente vs baseline)
- Detecao de `agent_error_spike` por agente
- Limiar de `high_failure_rate` revisado para 40%
- Catalogo de metricas EF-W010 praticamente completo no `MetricsRegistry`:
- Agentes: `agent_response_duration`, `agent_error_rate`
- Circuit breaker: `circuit_breaker_transitions_total`
- IPS: `ips_load_duration_seconds`, `ips_age_hours`
- Alertas: `alert_acknowledgment_seconds`, `alerts_escalated_total`
- Workflows: `workflow_executions_total`, `workflow_duration_seconds`, `workflow_iterations`
- Metodos de registro adicionados para todas as categorias acima
- `summary()` ampliado com blocos `ips_cache`, `routing` e `alerts`
- SLO de ACK critico implementado com valor p95 em runtime (`critical_alert_ack_seconds`)
- Metricas EF-W010 ampliadas:
- Novas metricas Prometheus de routing, IPS e alertas no `MetricsRegistry`
- API de registro operacional:
- `record_orchestration(...)`
- `record_agent_call(...)`
- `record_routing_decision(...)`
- SLO com calculo real em runtime:
- `p95_latency_seconds` calculado por janela de latencias
- `availability_ratio` e `agent_availability_ratio` calculados por contadores reais
- `summary()` com panorama de agentes (success rate e latencia media)
- Orchestrator integrado com os novos registros de metrica/SLO
- Persistencia opcional de estado do circuit breaker:
- `CircuitBreaker` com load/save de estado (OPEN/CLOSED/HALF_OPEN, contadores, timestamp)
- `CircuitBreakerManager` com `state_store` injetavel
- `RedisCircuitStateStore` (quando Redis disponivel) e `InMemoryCircuitStateStore`
- `WandaOrchestrator` conectado para usar store Redis quando `enable_redis=true`
- Novas configuracoes:
- `cb_state_ttl_seconds`
- `cb_state_key_prefix`
- Resiliencia integrada no `ModuleRegistry`:
- `configure_resilience(...)` e `has_resilience`
- `call_module(...)` com circuit breaker, retry, timeout e fallback
- Orchestrator adaptado para evitar dupla aplicacao de resiliencia quando registry ja esta configurado
- Tracing (EF-W009) expandido:
- `TraceQueryService` com `analyze_routing_patterns(...)` e `find_anomalies(...)`
- `FHIRAuditExporter` com exportacao de `DecisionTrace` em `AuditEvent`
- Novos endpoints:
- `GET /api/v1/traces/patterns`
- `GET /api/v1/traces/anomalies`
- `GET /api/v1/traces/{trace_id}/fhir`
- Metrics/SLO (EF-W010) expandido:
- `MetricsRegistry.slos()`
- `MetricsRegistry.slos_snapshot()`
- `MetricsRegistry.slos_history(...)`
- Novos endpoints:
- `GET /api/v1/slos`
- `GET /api/v1/slos/history`

## Testes Executados na .venv
- Comando:
- `.\.venv\Scripts\python.exe -m pytest --no-cov tests\test_tracing.py tests\test_metrics_registry.py tests\test_phase4_routes.py tests\test_registry_resilience.py tests\test_orchestrator_phase4.py -q`
- Resultado: `10 passed`
- Comando:
- `.\.venv\Scripts\python.exe -m pytest --no-cov tests\test_circuit_breaker.py tests\test_registry_resilience.py tests\test_orchestrator_phase4.py tests\test_phase4_routes.py -q`
- Resultado: `10 passed`
- Comando:
- `.\.venv\Scripts\python.exe -m pytest --no-cov tests\test_metrics_registry.py tests\test_phase4_routes.py tests\test_orchestrator_phase4.py -q`
- Resultado: `5 passed`
- Comando:
- `.\.venv\Scripts\python.exe -m pytest --no-cov tests\test_metrics_registry.py tests\test_phase4_routes.py tests\test_orchestrator_phase4.py -q`
- Resultado: `5 passed` (apos completar metricas de workflow/alerts/ips)
- Comando:
- `.\.venv\Scripts\python.exe -m pytest --no-cov tests\test_metrics_registry.py tests\test_tracing.py tests\test_phase4_routes.py tests\test_orchestrator_phase4.py -q`
- Resultado: `10 passed` (com persistencia de SLO + anomalias robustas)
- Comando:
- `.\.venv\Scripts\python.exe -m pytest --no-cov tests\test_metrics_registry.py tests\test_tracing.py tests\test_alert_hub.py tests\test_workflow_executor.py tests\test_ips_manager_metrics.py tests\test_phase4_routes.py tests\test_orchestrator_phase4.py -q`
- Resultado: `35 passed` (com instrumentacao runtime de workflow/alert/IPS)

## Pendencias para Fechamento Completo da Fase 4
- Rodar validacao E2E com Redis/PostgreSQL reais em ambiente de integracao (funcionalidade implementada e coberta por testes unitarios)
