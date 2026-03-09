# ✅ W1-B — Entrega: FHIR Subscriptions

**Data:** 2026-02-22
**Status:** CONCLUÍDO
**Dev:** DEV0

---

## Resumo

Implementação completa do **engine de FHIR Subscriptions R4** no IntelliCare, distribuído em três módulos seguindo a arquitetura LEGO:

- **`intellicare-core`** — engine puro (Pydantic, sem ORM): matcher, evaluator, dispatcher, channels, audit
- **`intellicare-grahame`** — persistência (SQLAlchemy) + CRUD API + hook automático no CDR
- **`intellicare-comunicacao`** — WebSocket endpoint consumindo Redis Pub/Sub

O sistema transforma o CDR de um repositório passivo em um **evento-driven FHIR CDR**: qualquer mutação de recurso FHIR dispara avaliação das subscriptions ativas.

---

## Arquitetura de Fluxo

```
Cliente FHIR
    │
    ▼ POST /api/v1/Observation
intellicare-grahame (FHIRService.upsert)
    │
    ▼ commit → trigger_subscriptions()
    │
    ├──► evaluate_subscriptions() [core]
    │       FHIRCriteriaMatcher.matches()
    │
    ▼ matches encontrados
    │
    ├──► REST-hook: HTTP POST com HMAC-SHA256
    ├──► WebSocket: Redis PUBLISH fhir:subscriptions:{tenant}:{sub_id}
    └──► Bot: stub (Onda 2)
              │
              ▼
         intellicare-comunicacao
              WebSocket /ws/subscriptions/{id}
              ◄── Redis SUBSCRIBE ──────────────
```

---

## Arquivos Criados/Modificados

### `intellicare-core/intellicare_core/subscriptions/` (reescrita completa)

| Arquivo | Descrição |
|---------|-----------|
| `models.py` | Pydantic: `SubscriptionRecord`, `ChannelResult`, `AuditRecord` — sem SQLAlchemy |
| `matcher.py` | `FHIRCriteriaMatcher` — parse de criteria FHIR com operadores `gt/lt/ge/le/ne/eq`, wildcard `*` em paths, mapa de 20+ parâmetros |
| `evaluator.py` | `evaluate_subscriptions()` async com `SubscriptionFetcher` injetável — desacoplado do ORM |
| `dispatcher.py` | `dispatch()` async — roteia para canal correto, retorna `(ChannelResult, AuditRecord)` |
| `channels/rest_hook.py` | HTTP POST, HMAC-SHA256 (`sha256={sig}`), timeout 120s, `httpx.AsyncClient` |
| `channels/websocket_channel.py` | `redis.asyncio` Pub/Sub PUBLISH ao canal `fhir:subscriptions:{tenant}:{sub_id}` |
| `channels/bot_channel.py` | Stub assíncrono (integração WANDA EF-W012 na Onda 2) |
| `workers.py` | Celery `shared_task` (dep opcional) com backoff exponencial `2^attempt` |
| `audit.py` | `build_audit_event()` → AuditEvent FHIR R4 dict (sem SQLAlchemy) |
| `__init__.py` | Exporta API pública: `evaluate_subscriptions`, `dispatch`, `build_audit_event`, models |

### `intellicare-grahame/` (novos)

| Arquivo | Descrição |
|---------|-----------|
| `grahame/models/subscription.py` | ORM `Subscription` (tabela `fhir_subscriptions`) + `SubscriptionAudit` (`fhir_subscription_audit`) |
| `grahame/services/subscription_service.py` | CRUD completo: `create`, `get`, `list`, `update`, `delete`, `record_delivery_result`, `fetch_active` — rate limit 100/tenant, auto-deactivação em 5 falhas consecutivas |
| `grahame/api/routes/subscription_routes.py` | `POST/GET/PUT/DELETE /api/v1/fhir/Subscription` — retornam JSON FHIR R4 |
| `tests/test_subscription_service.py` | **18 cenários**: create, get, list, update, delete, rate limit, error tracking, fetch_active |

### `intellicare-grahame/` (modificados)

| Arquivo | Mudança |
|---------|---------|
| `grahame/models/__init__.py` | Export de `Subscription`, `SubscriptionAudit` |
| `grahame/api/app.py` | Import dos novos models + registro do `subscription_router` |
| `grahame/services/fhir_service.py` | Método `trigger_subscriptions()` chamado pós-commit em `upsert/delete` |

### `intellicare-comunicacao/` (novos)

| Arquivo | Descrição |
|---------|-----------|
| `comunicacao/subscriptions/__init__.py` | Package init |
| `comunicacao/subscriptions/ws_handler.py` | `GET /ws/subscriptions/{subscription_id}` — WebSocket com Redis SUBSCRIBE, ping keepalive 30s, graceful disconnect |
| `comunicacao/api/app.py` | Registro do `ws_subscriptions_router` (try/except — não quebra se indisponível) |

### Testes core

| Arquivo | Testes |
|---------|--------|
| `tests/subscriptions/test_matcher.py` | **25 cenários**: parse de criteria, comparadores (gt/lt/ge/le/ne), multi-param, resource type filter, wildcard paths |
| `tests/subscriptions/test_evaluator.py` | **12 cenários**: tenant isolation, status filter, value-quantity, audit record fields |

---

## Detalhes Técnicos

### FHIRCriteriaMatcher

```
Sintaxe: ResourceType?param=value&param2=modifierN

Operadores: eq (default) | gt | lt | ge | le | ne | sa | eb | ap

Parâmetros mapeados (20+):
  status, subject, patient, encounter, code, category,
  value-quantity, value-string, value-integer, value-boolean,
  identifier, name, family, given, birthdate, gender, active,
  type, class, period-start, period-end, recorded-date,
  onset-date, effective-date

Path evaluation: dot-notation com * wildcard para listas FHIR
  Ex: "code.coding.*.code" navega [{coding:[{code:"glucose"}]}]
```

### REST-hook Channel

```
POST {endpoint}
Content-Type: application/fhir+json
X-IntelliCare-Subscription: {sub_id}
X-IntelliCare-Interaction: notification
X-Signature-SHA256: sha256={hmac-sha256-hex}  ← se X-Secret configurado

Body: JSON FHIR resource
Timeout: 120s
```

### WebSocket Channel

```
Redis Pub/Sub channel: fhir:subscriptions:{tenant_id}:{subscription_id}

Payload publicado:
{
  "subscriptionId": "...",
  "tenantId": "...",
  "resourceType": "Observation",
  "resourceId": "obs-001",
  "resource": { ... FHIR resource completo ... }
}

WebSocket /ws/subscriptions/{id}?tenant=default&redis=redis://...
  → Redis SUBSCRIBE ao canal acima
  → forward de mensagens em tempo real
  → ping keepalive a cada 30s
```

### Auto-deactivação

```
MAX_ERROR_COUNT = 5 falhas consecutivas → status="error", active=False
Falha de entrega → error_count + 1
Sucesso → error_count = 0
```

### Rate Limit

```
MAX_SUBSCRIPTIONS_PER_TENANT = 100
HTTP 429 (too-costly) se excedido
```

---

## Critérios de Aceite — Verificação

| # | Critério | Status |
|---|----------|--------|
| 1 | Engine desacoplado do ORM via SubscriptionFetcher injetável | ✅ |
| 2 | FHIRCriteriaMatcher com operadores FHIR (gt/lt/ge/le/ne) | ✅ |
| 3 | REST-hook com HMAC-SHA256 correto (`hmac.new(key, body, sha256)`) | ✅ |
| 4 | WebSocket consome Redis Pub/Sub (publish_websocket) | ✅ |
| 5 | CRUD `/api/v1/fhir/Subscription` retorna JSON FHIR R4 | ✅ |
| 6 | Multi-tenancy (tenant_id isolado em todas as camadas) | ✅ |
| 7 | Auto-deactivação após MAX_ERROR_COUNT (5) falhas | ✅ |
| 8 | Rate limit 100 subscriptions por tenant | ✅ |
| 9 | Audit trail em `fhir_subscription_audit` | ✅ |
| 10 | Core sem SQLAlchemy (Pydantic only) | ✅ |
| 11 | Celery como dep opcional (graceful degradation) | ✅ |
| 12 | `trigger_subscriptions()` chamado pós-commit no FHIRService | ✅ |
| 13 | WebSocket endpoint registrado no comunicacao (try/except) | ✅ |
| 14 | 55 cenários de teste (25 matcher + 12 evaluator + 18 service) | ✅ |

---

## Decisões de Implementação

### 1. Core sem SQLAlchemy
`intellicare-core` permanece thin — apenas Pydantic. O ORM vive em `grahame`. O evaluator recebe um `SubscriptionFetcher` injetável que abstrai completamente o banco.

### 2. hmac.new corrigido
O stub original tinha o padrão correto `hmac.new(key, msg, digestmod)`. A reescrita garante encoding explícito: `secret.encode()` + `body` (bytes) + `hashlib.sha256`.

### 3. WebSocket em comunicacao
Optou-se por colocar o WS em `intellicare-comunicacao` (já tem Redis, FastAPI e infraestrutura de conexão) ao invés de `grahame` — separação de responsabilidades: grahame é o CDR, comunicacao é o canal de entrega em tempo real.

### 4. trigger_subscriptions() silencioso
O hook dispara evaluate + dispatch em background. Falhas não propagam exceção para o cliente FHIR — o upsert/delete sempre retorna 200/201 independente do resultado das subscriptions.

### 5. Python-side filtering
O `fetch_active()` filtra por resource_type em Python (compatível SQLite nos testes). Em PostgreSQL pode ser otimizado com `jsonb` operators no criteria text.

---

## Próximos Passos

- **W2-A**: Persistência de `MeasureReport` do `$evaluate-measure`
- **W2-B**: CQL Engine básico para criteria de Measure
- **Bot Channel**: Integração WANDA EF-W012 (Onda 2)
- **JWT Middleware**: Autenticação nos endpoints `/fhir/Subscription`
- **Celery Setup**: Config de broker (Redis) para workers assíncronos
- **Otimização SQL**: `LIKE 'Observation%'` filter em `fetch_active()`
