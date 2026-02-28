# 📦 ONDA_6 — Relatório de Entrega

**Data:** 2026-02-22
**Status:** ✅ CONCLUÍDA — W6-A (WAHA Webhook Inbound) + W6-B (Deploy & Versioning)

---

## W6-A: WAHA Webhook Inbound — Canal WhatsApp Bidirecional

### Objetivo
Completar o ciclo bidirecional do canal WhatsApp no `intellicare-comunicacao`: o módulo já sabia *enviar* mensagens via WAHA; agora também *recebe* as respostas dos pacientes via webhook HTTP e publica um evento Redis Stream para que o agente GERALDA prossiga o fluxo de acompanhamento.

### Arquivos Criados/Modificados

| Arquivo | Tipo | Descrição |
|---------|------|-----------|
| `comunicacao/channels/whatsapp/waha_webhook_handler.py` | **NOVO** | `WAHAWebhookHandler` — processa eventos WAHA |
| `comunicacao/api/webhook_routes.py` | **MODIFICADO** | Adicionado `POST /api/v1/webhooks/waha` |
| `tests/test_waha/test_webhook_handler.py` | **NOVO** | 12 testes de unidade |

### WAHAWebhookHandler

**Localização:** `intellicare-comunicacao/comunicacao/channels/whatsapp/waha_webhook_handler.py`

**Responsabilidades:**

1. **Roteamento de eventos** — `handle_event()` despacha por tipo:
   - `message` → `_handle_incoming_message()`
   - `session.status` → log informativo
   - outros → silenciosamente ignorados

2. **Persistência LGPD-safe** — persiste no `ExternalMessageLog`:
   - `direction = INBOUND`
   - `channel = "whatsapp"`
   - `provider_status = "waha:{session}:{msg_type}"`
   - `message_summary = body[:120] + "…"` (texto truncado — sem conteúdo completo em auditoria)

3. **Publicação Redis Stream** — emite em `intellicare:whatsapp.message.received`:
   ```json
   {
     "source": "waha",
     "session": "default",
     "message_id": "...",
     "from_phone": "+5511999999999",
     "from_chat_id": "5511999999999@c.us",
     "body": "Tomei o remédio",
     "type": "chat",
     "received_at": "2026-02-22T..."
   }
   ```

4. **Proteções:**
   - Mensagens `fromMe=True` descartadas
   - `from` vazio → warning + skip
   - Redis opcional: se `INTELLICARE_REDIS_URL` não configurado, publica silenciosamente; se `redis` não instalado, loga aviso

**Endpoint registrado:**

```
POST /api/v1/webhooks/waha
```

Depende de `INTELLICARE_REDIS_URL` ou `REDIS_URL` (env) para publicação no Redis.

### Testes W6-A

| Arquivo | Testes |
|---------|--------|
| `tests/test_waha/test_webhook_handler.py` | 12 |
| **Total W6-A** | **12** |

**Cenários cobertos:**
- `_extract_phone`: conversão `5511999999999@c.us` → `+5511999999999`
- Roteamento correto de evento `message` vs `session.status` vs desconhecido
- Persistência: `db.add()` + `db.commit()` invocados; `direction=INBOUND`; `channel=whatsapp`; `provider_status` contém `"waha"`
- Filtragem: mensagens `fromMe=True` ignoradas; `from` vazio ignorado
- Redis: `xadd()` chamado com stream correto quando URL configurada; não chamado quando `redis_url=None`

Todos passando: `12 passed`.

---

## W6-B: Deploy & Versioning

### Objetivo
Preparar os artefatos de deploy para produção: versões alinhadas, compose atualizado, smoke tests completos.

### 1. Version Bump — pyproject.toml

Todos os 5 módulos impactados pelas ONDAs 1–6 bumpeados de `1.0.0` → `1.1.0`:

| Módulo | Motivo do bump |
|--------|----------------|
| `intellicare-core` | + `cds_hooks/`, `terminology/`, `fhir_storage/`, `fhir_search/`, `audit/`, `questionnaire/`, `ips/`, `policy/` |
| `intellicare-grahame` | + CDS Hooks 2.0 routes, Terminology Service routes, FHIR Storage/Search, SMART-on-FHIR 2.0, Audit Trail, Questionnaire Engine |
| `intellicare-auth` | + SMART-on-FHIR 2.0 (launch tokens, scope translator, JWKS, well-known config) |
| `intellicare-portal` | + SMART-on-FHIR React components (SmartLaunchButton, EHRLaunchHandler, SmartCallback) |
| `intellicare-comunicacao` | + WAHA webhook inbound, Redis event emission |

### 2. docker-compose.full.yml — Atualizado

**Arquivo:** `./docker-compose.full.yml`

Alterações:
- Header atualizado para `v1.1.0 (ONDA_6 / 2026-02-22)`
- Contador de módulos: 6 → 9 backend modules
- Adicionado serviço `pierre` (8009 — Scientific Search: PubMed + Tavily + BVS/BIREME)
- Variáveis WAHA adicionadas ao serviço `comunicacao`:
  ```yaml
  - WAHA_BASE_URL=${WAHA_BASE_URL:-http://localhost:3000}
  - WAHA_SESSION=${WAHA_SESSION:-default}
  - WAHA_API_KEY=${WAHA_API_KEY:-}
  - WAHA_TIMEOUT_SECONDS=${WAHA_TIMEOUT_SECONDS:-30}
  ```
- Tabela de acesso atualizada: pierre (8009) + grahame (8012) + nise (8013) documentados

**Serviços no compose:**

| Serviço | Porta | Tier |
|---------|-------|------|
| postgres | 5432 | infrastructure |
| redis | 6379 | infrastructure |
| prometheus | 9090 | infrastructure |
| grafana | 3000 | infrastructure |
| florence | 8001 | backend |
| oswaldo | 8002 | backend |
| donabedian | 8003 | backend |
| wanda | 8004 | backend |
| comunicacao | 8005 | backend |
| geralda | 8006 | backend |
| pierre | 8009 | backend |
| grahame | 8012 | backend |
| nise | 8013 | backend |
| portal | 3001 | frontend |

> **Nota:** `intellicare-auth` não tem Dockerfile ainda — é uma biblioteca Python embarcada nos módulos que a utilizam (grahame, portal). Será containerizado em versão futura.

### 3. Smoke Tests — Atualizados

**Arquivo:** `scripts/smoke_tests.py`

Alterações:
- Adicionados `grahame` (8012) e `nise` (8013) ao dicionário `BACKEND_SERVICES`
- Contador dinâmico de módulos: `f"Backend Services ({len(BACKEND_SERVICES)} módulos)"`
- Path de health check corrigido: `/health` → `/api/v1/health` (alinhado com contrato IntelliCare)
- URL do portal corrigida para `/` (serve Nginx static)

**Arquivo:** `scripts/smoke_test.sh` — já incluía grahame e nise (sem alterações necessárias)

---

## Resumo de Testes ONDA_6

| Workstream | Testes |
|------------|--------|
| W6-A — WAHA Webhook | 12 |
| W6-B — Deploy/Versioning | — |
| **Total ONDA_6** | **12** |

---

## Acúmulo MEDPLUS_ON

| ONDA | Workstreams | Testes adicionados |
|------|-------------|---------------------|
| ONDA_1 | W1-A (IPS Generator) + W1-B (Policy Engine) | 91 |
| ONDA_2 | W2-A (Audit Trail) + W2-B (Questionnaire Engine) | 105 |
| ONDA_3 | W3-A (FHIR-Native Storage) + W3-B (FHIR Search Engine) | 87 |
| ONDA_4 | W4-A (React Components) + W4-B (SMART-on-FHIR) | 73 |
| ONDA_5 | W5-A (CDS Hooks 2.0) + W5-C (Terminology Service) | 70 |
| ONDA_6 | W6-A (WAHA Webhook) + W6-B (Deploy) | 12 |
| **Total** | **11 workstreams** | **~438 testes** |

---

## Próxima ONDA

**ONDA_7** — candidatos:

- **W7-A**: FHIR Bulk Data `$export` NDJSON — exportação assíncrona para analytics (Kestra ETL) — *alta prioridade para pipeline de dados*
- **W7-B**: CDS Hooks Feedback Loop + Métricas (Prometheus/Grafana) — fechar o ciclo do W5-A
- **W7-C**: `intellicare-auth` Dockerfile + standalone service — containerizar o módulo SMART-on-FHIR
- **W7-D**: FHIR Subscriptions v2 (Backport R5) — WebSocket + Email channels
