# 📅 W1-B — Plano de Implementação: FHIR Subscriptions Engine

## Visão Geral
- **Duração estimada:** 10 dias úteis
- **Desenvolvedores:** 2 (Dev 3 + Dev 4)
- **Módulos:** `intellicare-core` (engine) + `intellicare-comunicacao` (WebSocket)

---

## Sprint 1 (Dias 1-5) — Core Engine + REST-Hook

### Dia 1-2: Fundação (Dev 3 + Dev 4 em pair)
- [ ] Criar package `intellicare_core/subscriptions/`
- [ ] Implementar `models.py` — SQLAlchemy models (fhir_subscriptions, fhir_subscription_audit)
- [ ] Criar migrations Alembic para as novas tabelas
- [ ] Implementar `matcher.py` — FHIR Criteria Matcher
  - [ ] Parser de critério ("Observation?code=glucose" → dict)
  - [ ] Avaliação de parâmetros simples (code, status, subject)
  - [ ] Avaliação de operadores (gt, lt, ge, le, eq, ne)
- [ ] Testes unitários do matcher (mínimo 15 cenários)

### Dia 3-4: REST-Hook Channel (Dev 3)
- [ ] Implementar `channels/rest_hook.py`
  - [ ] HTTP POST assíncrono via httpx
  - [ ] Headers padrão (Content-Type, X-IntelliCare-Subscription, X-IntelliCare-Interaction)
  - [ ] Custom headers do Subscription.channel.header
  - [ ] Assinatura HMAC-SHA256
  - [ ] Timeout de 120s
- [ ] Implementar `audit.py` — criação de AuditEvent FHIR
- [ ] Testes unitários com mock HTTP (sucesso, falha, timeout, HMAC)

### Dia 3-4: Evaluator + Dispatcher (Dev 4)
- [ ] Implementar `evaluator.py` — SubscriptionEvaluator
  - [ ] Busca de subscriptions ativas por tenant/resource_type
  - [ ] Loop de avaliação de critérios
  - [ ] Enfileiramento de jobs
  - [ ] Exclusão de AuditEvents
- [ ] Implementar `dispatcher.py` — despacho por canal
- [ ] Implementar `workers.py` — Celery task com retry
  - [ ] Backoff exponencial
  - [ ] Max attempts configurável
  - [ ] Desativação automática após N falhas
- [ ] Testes unitários

### Dia 5: Integração REST-Hook
- [ ] Integrar evaluator no hook do Grahame (create/update/delete)
- [ ] Teste end-to-end: criar recurso → subscription dispara → webhook recebe
- [ ] PR #1 — Core Engine + REST-Hook

---

## Sprint 2 (Dias 6-10) — WebSocket + Polish

### Dia 6-7: WebSocket Channel (Dev 3)
- [ ] Implementar `channels/websocket_channel.py` — publicação Redis Pub/Sub
- [ ] Implementar `comunicacao/subscriptions/ws_handler.py`
  - [ ] Endpoint WebSocket `/ws/subscriptions`
  - [ ] Autenticação via token JWT
  - [ ] Registro de subscription temporária no Redis
  - [ ] Escuta de Redis channel e filtro por subscription
  - [ ] Gerenciamento de conexão (reconexão, cleanup)
- [ ] Testes de WebSocket (conectar, receber, desconectar)

### Dia 6-7: Bot Channel stub + CRUD API (Dev 4)
- [ ] Implementar `channels/bot_channel.py` — stub que registra bot a executar
- [ ] API CRUD de Subscriptions em Grahame:
  - [ ] `POST /fhir/Subscription` — criar
  - [ ] `GET /fhir/Subscription/{id}` — ler
  - [ ] `PUT /fhir/Subscription/{id}` — atualizar
  - [ ] `DELETE /fhir/Subscription/{id}` — desativar
  - [ ] `GET /fhir/Subscription` — listar (com filtros FHIR)
- [ ] Validação de critério na criação
- [ ] Rate limit (max 100 ativas por tenant)

### Dia 8-9: Observabilidade (Dev 3 + Dev 4)
- [ ] Métricas Prometheus:
  - [ ] `subscription_jobs_total{tenant, channel, outcome}`
  - [ ] `subscription_queue_duration_seconds`
  - [ ] `subscription_execution_duration_seconds`
  - [ ] `subscription_rest_hook_duration_seconds`
- [ ] Logging estruturado (subscription_id, resource_type, tenant, outcome)
- [ ] Health check para Celery worker
- [ ] Alertas Prometheus para falhas excessivas

### Dia 10: Finalização
- [ ] Testes de integração completos
- [ ] Testes de multi-tenancy
- [ ] Documentação dos endpoints
- [ ] Documentação de configuração do Celery
- [ ] PR #2 — WebSocket + Bot stub + Observabilidade
- [ ] Merge final

---

## Critérios de Aceite

1. ✅ Subscription CRUD funcional via FHIR API
2. ✅ REST-hook dispara corretamente para Create, Update, Delete
3. ✅ HMAC-SHA256 assinatura verificável no receptor
4. ✅ Retry com backoff exponencial funcional
5. ✅ WebSocket recebe notificações em tempo real
6. ✅ Isolamento multi-tenant comprovado
7. ✅ AuditEvent gerado para cada execução
8. ✅ Métricas Prometheus expostas
9. ✅ Cobertura de testes ≥ 80%

---

## Pré-requisitos

- Celery configurado com Redis como broker (reusar o Redis existente)
- Redis Pub/Sub disponível para WebSocket
- Grahame com endpoints FHIR CRUD funcionais

## Riscos e Mitigações

| Risco | Impacto | Mitigação |
|---|---|---|
| Celery não configurado no Docker Compose | Alto | Adicionar worker Celery ao docker-compose.full.yml |
| Volume alto de subscriptions degradar performance | Médio | Index otimizado, cache de subscriptions no Redis |
| WebSocket instável em produção | Médio | Reconnect automático, health monitoring |
| Loops infinitos (subscription → cria recurso → subscription) | Crítico | Exclusão de AuditEvents + flag anti-loop |
