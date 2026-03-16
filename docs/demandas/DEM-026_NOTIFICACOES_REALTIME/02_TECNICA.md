---
tipo: especificacao-tecnica
demanda: DEM-026
titulo: Notificações em Tempo Real (WebSocket / SSE)
fase: 3
sprint: "3.2"
status: em-execucao
planejador: Claude
criado: 2026-03-16
---

# DEM-026 — Especificação Técnica

> Localização dos arquivos: `C:\Users\egara\INTELLICARE\`

## PRÉ-CONDIÇÕES

- Redis rodando (`docker compose up redis`)
- PostgreSQL com schemas de tenant criados
- Módulos admin e gestor funcionais (para dependências de auth)

## Arquitetura

```
Frontend (SSE/WS client)
       ↕
   /notifications/stream (SSE)    ← read-only push
   /notifications/ws (WebSocket)  ← bidirectional
       ↕
   NotificationService
       ↕
   Redis Pub/Sub ←→ channel: notif:{tenant}:{user_id}
       ↕
   PostgreSQL (tenant schema) → notifications table
```

## BLOCO 1 — Estrutura do Módulo

```
modules/notifications/
├── __init__.py
├── main.py           # Module(BaseModule)
├── schemas.py        # Pydantic models
├── service.py        # NotificationService (CRUD + pub/sub)
├── router.py         # REST + SSE + WebSocket
├── redis_pubsub.py   # Redis Pub/Sub connection manager
└── migrations.py     # SQL table definitions
```

## BLOCO 2 — Tabelas SQL (por tenant)

```sql
CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('appointment','clinical','system','message','alert')),
    priority TEXT NOT NULL DEFAULT 'normal'
        CHECK (priority IN ('low','normal','high','urgent')),
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    data JSONB DEFAULT '{}',
    read BOOLEAN NOT NULL DEFAULT FALSE,
    read_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_notifications_unread ON notifications(user_id) WHERE read = FALSE;

CREATE TABLE IF NOT EXISTS notification_preferences (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL UNIQUE,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    types_enabled TEXT[] DEFAULT ARRAY['appointment','clinical','system','message','alert'],
    priority_min TEXT NOT NULL DEFAULT 'low'
        CHECK (priority_min IN ('low','normal','high','urgent')),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

## BLOCO 3 — Endpoints REST

| Método | Rota | Auth | Descrição |
|--------|------|------|-----------|
| GET | /health | — | Health check |
| POST | /send | Authenticated | Criar e enviar notificação |
| GET | / | Authenticated | Listar notificações do usuário |
| GET | /unread-count | Authenticated | Contagem de não lidas |
| GET | /{id} | Authenticated | Detalhe de uma notificação |
| PATCH | /{id}/read | Authenticated | Marcar como lida |
| PATCH | /read-all | Authenticated | Marcar todas como lidas |
| DELETE | /{id} | Authenticated | Apagar notificação |
| GET | /preferences | Authenticated | Preferências do usuário |
| PUT | /preferences | Authenticated | Atualizar preferências |

## BLOCO 4 — SSE Endpoint

```
GET /notifications/stream
Authorization: Bearer {token}
Accept: text/event-stream
```

- Autenticação via header `Authorization`
- Canal Redis: `notif:{tenant_id}:{user_id}`
- Heartbeat a cada 30s (`:keepalive\n\n`)
- Formato: `data: {json}\n\n`

## BLOCO 5 — WebSocket Endpoint

```
WS /notifications/ws?token={jwt}
```

- Auth via query param (WebSocket não suporta custom headers)
- Mesmo canal Redis de pub/sub
- Mensagens JSON bidirecionais
- Ping/pong a cada 30s

## BLOCO 6 — Redis Pub/Sub

- Canal por usuário: `notif:{tenant_id}:{user_id}`
- Canal broadcast por tenant: `notif:{tenant_id}:*`
- Payload JSON serializado

## BLOCO 7 — Registro no ModuleLoader

Em `packages/intellicare-core/intellicare_core/module_loader/loader.py`:
```python
AVAILABLE_MODULES["notifications"] = "modules.notifications.main"
```

Em `packages/intellicare-core/intellicare_core/main.py`:
```python
loader.load("notifications")
```

## BLOCO 8 — Migração SQL

Arquivo: `db/tenant_migrations/007_notifications.sql`

## Commit Final

```bash
cd C:\Users\egara\INTELLICARE
git add .
git commit -m "feat(notifications): DEM-026 real-time notifications via SSE/WebSocket"
git push origin main
```
