# IntelliCare V3 — Infraestrutura e Deploy

> Última atualização: 2026-03-21 | Sprint 2026-04-18

---

## Serviços Docker em produção/staging

```mermaid
graph TB
    subgraph INTERNET ["🌐 Internet"]
        BROWSER[Browser / App]
    end

    subgraph VPS ["🖥 VPS (Ubuntu 22.04)"]
        subgraph PROXY ["Reverse Proxy"]
            TRAEFIK[Traefik v2.11\nporta 80/443\nLet's Encrypt TLS]
        end

        subgraph APP ["Aplicação"]
            SVC[intellicare-service\nFastAPI + Statics\nporta 8000]
        end

        subgraph INFRA_SVC ["Infraestrutura"]
            PG[PostgreSQL 16\nporta 5432]
            REDIS[Redis 7\nporta 6379]
            KC[Keycloak 24\nporta 8080]
        end

        subgraph CANAIS ["Canais CarePlanner"]
            EVO[Evolution API v2.3.7\nporta 8081]
            LISTMONK[Listmonk\nporta 9000]
            JASMIN[Jasmin SMS\nporta 8000/SMPP]
            RC[RocketChat\nporta 3000]
        end

        subgraph WORKFLOW ["Workflows"]
            KESTRA[Kestra 0.20\nporta 8080]
        end

        subgraph OBS ["Observabilidade"]
            PROM[Prometheus\nporta 9090]
            GRAF[Grafana\nporta 3000]
        end
    end

    BROWSER -->|HTTPS 443| TRAEFIK
    TRAEFIK -->|/admin, /gestor, /cuidado\n/florence, /oswaldo\n/careplanner, /auth| SVC
    SVC --> PG
    SVC --> REDIS
    SVC --> KC
    SVC --> EVO
    SVC --> LISTMONK
    SVC --> JASMIN
    SVC --> RC
    SVC --> KESTRA
    PROM -->|scrape :8000/metrics| SVC
    PROM -->|scrape :9090| PROM
    GRAF --> PROM
```

---

## Pipeline CI/CD

```mermaid
flowchart LR
    subgraph DEV ["👨‍💻 Desenvolvimento"]
        CODE[Commit + Push\nmain branch]
    end

    subgraph CI ["⚙️ GitHub Actions"]
        direction TB
        TEST[pytest backend\n--cov intellicare_core]
        BUILD_C[Build ClinicoUI\nnpm ci + vite build]
        BUILD_G[Build GestorUI\nnpm ci + vite build]
        BUILD_A[Build AdminUI\nnpm ci + vite build]
    end

    subgraph STAGING ["🧪 Staging (VPS)"]
        PULL[git pull origin main]
        REBUILD[docker compose build\n--no-cache intellicare-service]
        SMOKE[Smoke tests\ncurl endpoints]
        LOG[staging_sync_log.txt\ncommit evidência]
    end

    CODE --> TEST & BUILD_C & BUILD_G & BUILD_A
    TEST -->|badge README| DONE_TEST[✅]
    BUILD_C & BUILD_G & BUILD_A -->|artefatos incluídos\nno container| DONE_BUILD[✅]
    DONE_TEST & DONE_BUILD --> PULL
    PULL --> REBUILD --> SMOKE --> LOG
```

---

## Estratégia de banco de dados — Schema-per-tenant

```mermaid
erDiagram
    PLATFORM_TENANT_CONFIG {
        uuid id PK
        varchar tenant_slug UK
        varchar display_name
        varchar plan
        int max_users
        text_array modules_enabled
        timestamptz created_at
        timestamptz suspended_at
    }

    TENANT_SCHEMA_alfa {
        uuid users
        uuid encounters
        uuid clinical_notes
        uuid prescriptions
        uuid journeys
        uuid notifications
        uuid push_subscriptions
    }

    TENANT_SCHEMA_beta {
        uuid users
        uuid encounters
        uuid clinical_notes
        uuid prescriptions
        uuid journeys
        uuid notifications
        uuid push_subscriptions
    }

    PLATFORM_TENANT_CONFIG ||--|| TENANT_SCHEMA_alfa : "slug = 'alfa'"
    PLATFORM_TENANT_CONFIG ||--|| TENANT_SCHEMA_beta : "slug = 'beta'"
```

**Convenção de acesso:**
```python
# ✅ Correto — V3
async with tenant_session(ctx) as db:
    # SET search_path TO clinica_alfa, public
    result = await db.execute(select(ClinicalNote))

# ❌ Errado — V2 legacy
db = ctx.db  # não seta search_path
```

---

## Migrations — histórico

| Migration | DEM | Conteúdo |
|-----------|-----|---------|
| 001–006 | DEMs iniciais | Estrutura base — users, tenants, módulos |
| 007 | DEM-026 | notifications, SSE |
| 008 | DEM-038 | careplanner — journeys, tasks, channels |
| 009 | DEM-029 | appointments |
| 010–011 | DEM-022 | portal paciente |
| 012 | DEM-054 | appointment_id em journeys |
| 013 | DEM-055 | clinical_notes (Florence) |
| 014 | DEM-058 | prescriptions (Oswaldo) |
| 015 | DEM-065 | platform.tenant_config (schema global) |
| 016 | DEM-066 | push_subscriptions (por tenant) |

---

## Gotchas de infraestrutura — histórico de incidentes

| Incidente | Causa raiz | Fix | Commit |
|-----------|-----------|-----|--------|
| Evolution API QR count:0 | Baileys v6 race condition em v2.2.x | Trocar para `evoapicloud/v2.3.7` | `06a0b1e` |
| Redis `ValueError: Port could not be cast` | `#` na senha truncava URL Redis | `REDIS_PASSWORD_URLENC` com senha URL-encoded | `c7fabecc` |
| ClinicoUI Docker build falha | Vite não pré-bundlava `@tanstack/react-query` em SSR/Docker | `optimizeDeps.include` no `vite.config.ts` | `055e883` |
| Traefik 404 em produção | v3.2 incompatível com Docker API 1.24 no VPS | Downgrade para v2.11.31 | `59fd4c1` |
| `TenantContext has no attribute db` | Padrão V2 `ctx.db` usado em módulo V3 | Usar `tenant_session(ctx)` — gotcha documentado | `19799a2` |
| VAPID keys rotacionadas | Subscriptions antigas invalidadas silenciosamente | **Nunca rotacionar** sem `TRUNCATE push_subscriptions` | — |
