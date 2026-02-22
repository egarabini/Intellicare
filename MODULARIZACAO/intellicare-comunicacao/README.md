# intellicare-comunicacao

Modulo de comunicacao integrada do IntelliCare — sistema nervoso da plataforma.

> **Status:** Em desenvolvimento ativo — suíte estável: 133 passed, 1 skipped (2026-02-18)
> **Porta:** 8005
> **Stack:** Python 3.11 + FastAPI + Rocket.Chat API + Jitsi JWT + Redis Streams + PostgreSQL

---

## Plataformas Operacionais

| Plataforma | URL | Proposito |
|---|---|---|
| **Rocket.Chat** | `https://rocket.gsi.srv.br` | Mensagens da equipe, alertas clinicos, bot @intellicare |
| **Jitsi Meet** | `https://meet.gsi.srv.br` | Teleconsultas, salas de caso multidisciplinar |
| **Keycloak** | `https://keycloak.gsi.srv.br` | SSO/RBAC (realm: bemcuidar) |

> **Nota:** Matrix/Synapse foi descontinuado no roteamento ativo. O stack legado
> (`MatrixClientService` e endpoints Matrix) permanece opcional via
> `MATRIX_ENABLE_LEGACY_STACK`, fora do `DispatcherManager` ativo.

---

## Arquitetura (7 Dominios)

```
Modulos Clinicos (Oswaldo, Florence, Geralda, Donabedian)
                │
                │ Redis Streams / API REST
                ▼
┌──────────────────────────────────┐
│  D1 — Engine de Roteamento       │
│  RoutingEngine → DispatcherMgr   │
└────────────────┬─────────────────┘
                 │
    ┌────────────┼────────────┐
    ▼            ▼            ▼
┌────────┐  ┌────────┐  ┌──────────┐
│ D2 RC  │  │ D3     │  │ D4 Ext   │
│Rocket  │  │Jitsi/  │  │WhatsApp  │
│Chat    │  │Telecon │  │SMS/Email │
└────────┘  └────────┘  └──────────┘
    │
    ▼
D5 Eventos | D6 LGPD | D7 Dashboard
```

---

## Especificacoes Funcionais

| Dominio | EFs | Status | Arquivo |
|---|---|---|---|
| D1 — Engine Roteamento | EF-COM-001..003 | ✅ Implementado | [docs/01_engine_roteamento/](docs/01_engine_roteamento/) |
| D2 — Rocket.Chat | EF-COM-010..012 | ✅ Implementado (sem bot) | [docs/02_integracao_rocketchat/](docs/02_integracao_rocketchat/) |
| D3 — Teleconsulta/Jitsi | EF-COM-020 | 🔵 Em desenvolvimento | [docs/03_teleconsulta_video/](docs/03_teleconsulta_video/) |
| D3 — Sala de Caso Multi | EF-COM-021 | ✅ Implementado (7 endpoints) | [docs/03_teleconsulta_video/](docs/03_teleconsulta_video/) |
| D4 — Notificacoes Externas | EF-COM-030..033 | ✅ SMS + Email implementados | [docs/04_notificacoes_canais_externos/](docs/04_notificacoes_canais_externos/) |
| D5 — Eventos/Consolidacao | EF-COM-040..041 | 🔵 Parcial (consumer integrado) | [docs/05_eventos_consolidacao/](docs/05_eventos_consolidacao/) |
| D6 — LGPD/Auditoria | EF-COM-050..051 | ✅ Implementado | [docs/06_conformidade_lgpd_auditoria/](docs/06_conformidade_lgpd_auditoria/) |
| D7 — Dashboard | EF-COM-060..061 | ⏳ Pendente | [docs/07_dashboard_monitoramento/](docs/07_dashboard_monitoramento/) |

**Indice completo:** [docs/INDICE_ESPECIFICACOES_FUNCIONAIS.md](docs/INDICE_ESPECIFICACOES_FUNCIONAIS.md)

---

## Estrutura do Codigo

```
comunicacao/
├── routing/           # D1 — RoutingEngine, FallbackMonitor, rules, store ✅
│   ├── engine.py      # Motor de roteamento principal
│   ├── fallback_monitor.py
│   ├── models.py, rules.py, store.py, lgpd.py, recipient_resolver.py
├── rocketchat/        # D2 — Client, ChannelService, Models, Config ✅
│   ├── client.py      # HTTP client Rocket.Chat
│   ├── channel_service.py, config.py, models.py
├── case_room/         # D3 — Sala de Caso Multidisciplinar (EF-COM-021) ✅
│   ├── service.py, store.py, models.py
├── jitsi/             # D3 — Teleconsultas (EF-COM-020, em desenvolvimento)
│   ├── client.py, room_service.py, dispatcher.py, config.py, models.py
├── lgpd/              # D6 — ComplianceService, PreferencesService ✅
│   ├── compliance_service.py, preferences_service.py, models.py, config.py
├── audit/             # D6 — AuditService, HashChain ✅
│   ├── audit_service.py, hash_chain.py, models.py
├── templates/         # Templates de mensagens ✅
│   ├── renderer.py, store.py, models.py
├── dispatchers/       # D1 — Dispatchers ativos (RC/email/sms/whatsapp/push/jitsi) ✅
│   └── base.py
├── sync/              # Modelos de sincronizacao ✅
├── monitoring/        # Metricas Prometheus ✅
├── storage/           # Storage base ✅
├── bot/               # Estrutura bot RC (base) ✅
├── api/               # FastAPI routes ✅
│   ├── app.py
│   ├── case_room_routes.py, channel_routes.py, routing_routes.py
│   ├── lgpd_routes.py, template_routes.py, health_routes.py
│   └── jitsi_routes.py (EF-COM-020)
├── config.py
└── metrics.py
```

---


## Endpoints Principais (V5)

```
GET  /api/v1/health                       # Health check (aberto)
POST /api/v1/send                         # Envio omnicanal (protegido IAM)
GET  /api/v1/status/{message_id}          # Status de entrega (protegido IAM)
GET  /api/v1/intents                      # Listar intents (admin)
```

### Exemplo de proteção IAM/Keycloak

```python
from intellicare_auth.fastapi import get_current_user, require_role
from fastapi import Depends

@router.post("/api/v1/send", dependencies=[Depends(get_current_user)])
async def send_message(...):
    ...

@router.get("/api/v1/intents", dependencies=[Depends(require_role("admin"))])
async def list_intents():
    ...
```

Todos os endpoints sensíveis devem exigir autenticação IAM. Endpoints administrativos exigem role específica.

---

## Execucao Local (Baseline)

```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
source .venv/bin/activate # Linux/Mac
pip install -r requirements.txt
uvicorn comunicacao.api.app:create_app --factory --port 8005
```

Health check:
```bash
curl http://localhost:8005/api/v1/health
```

---

## Variaveis de Ambiente (Novo — V5)

```bash
# Rocket.Chat
ROCKETCHAT_URL=https://rocket.gsi.srv.br
ROCKETCHAT_BOT_USERNAME=intellicare-bot
ROCKETCHAT_BOT_PASSWORD=<secret>
ROCKETCHAT_ADMIN_USER_ID=<user_id>
ROCKETCHAT_ADMIN_AUTH_TOKEN=<token>
ROCKETCHAT_WEBHOOK_TOKEN=<token>

# Jitsi
JITSI_DOMAIN=meet.gsi.srv.br
JITSI_BASE_URL=https://meet.gsi.srv.br
JITSI_APP_ID=intellicare
JITSI_APP_SECRET=<JWT_APP_SECRET>

# Keycloak
KEYCLOAK_ADMIN_URL=https://keycloak.gsi.srv.br
KEYCLOAK_TARGET_REALM=bemcuidar

# DB + Redis
INTELLICARE_DATABASE_URL=postgresql+asyncpg://...
INTELLICARE_DATABASE_SCHEMA=comunicacao_operacional
REDIS_URL=redis://localhost:6379
```

---

## Estado dos Testes (2026-02-18)

```
Suíte estável: 133 passed, 1 skipped
```

| Modulo | Cobertura | Observacao |
|--------|-----------|------------|
| `case_room/` | 100% | EF-COM-021 completo |
| `routing/engine.py` | 91% | |
| `routing/fallback_monitor.py` | 97% | |
| `lgpd/compliance_service.py` | 84% | |
| `api/case_room_routes.py` | 98% | |

## Proximos Passos

1. ✅ D1 — RoutingEngine, FallbackMonitor (implementado)
2. ✅ D2 — RocketChat Client, ChannelService (implementado)
3. 🔵 D3 — EF-COM-020 Teleconsultas Jitsi (em desenvolvimento)
4. ✅ D4 — SMS (Twilio/Zenvia/SNS) + Email SMTP (implementado)
5. 🔵 D5 — Redis Consumer → RoutingEngine (integração base concluída, consolidação pendente)
6. ✅ D6 — LGPD + Auditoria (implementado)
7. ⏳ D7 — Dashboard Prometheus
