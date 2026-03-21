---
tipo: especificacao-tecnica
demanda: DEM-068
titulo: Staging Full Sync 2026-04-18
---

# DEM-068 — Especificação Técnica

## Variáveis novas a adicionar ao `.env.staging`

| Variável | Origem | Observação |
|----------|--------|------------|
| `KEYCLOAK_ADMIN_URL` | DEM-065 | `http://keycloak:8080` |
| `KEYCLOAK_ADMIN_USER` | DEM-065 | `admin` |
| `KEYCLOAK_ADMIN_PASSWORD` | DEM-065 | senha do realm master |
| `VAPID_PUBLIC_KEY` | DEM-066 | gerada one-time com `py-vapid` |
| `VAPID_PRIVATE_KEY` | DEM-066 | gerada one-time — nunca rotacionar |
| `VAPID_SUBJECT` | DEM-066 | `mailto:admin@intellicare.ia.br` |

## Migrations a aplicar

| Migration | DEM | Schema |
|-----------|-----|--------|
| `015_tenant_config.sql` | DEM-065 | `platform` (novo schema compartilhado) |
| `016_push_subscriptions.sql` | DEM-066 | schema de cada tenant |

Migrations são aplicadas automaticamente no startup do container se `alembic upgrade head` estiver no entrypoint. Verificar que `015` cria o schema `platform` antes de inserir.

## Smoke scripts

Ver `03_PLANO.md` para os comandos curl completos de cada smoke test.
