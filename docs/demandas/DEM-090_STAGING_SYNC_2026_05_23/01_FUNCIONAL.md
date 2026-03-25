# DEM-090 — Staging Sync 2026-05-23

## Objetivo

Sincronizar o ambiente de staging com todas as entregas da sprint 2026-05-23, executar smoke tests para confirmar a integridade do sistema e fechar os dois deltas de infra que estavam pendentes desde a sprint 2026-05-16.

## Entregas validadas nesta DEM

| Sprint | DEM | O que valida |
|--------|-----|-------------|
| 2026-05-16 (pendente) | DEM-087 | JWT issuer fix + Traefik `/api/identity/*` |
| 2026-05-23 | DEM-088 | Professional identity: migration 024 aplicada |
| 2026-05-23 | DEM-089 | Reconciliation endpoint + AdminUI identity page |

## Critério de aceite

- Migration 024 aplicada sem erros no staging
- `POST https://intellicare.ia.br/api/identity/pessoas` → 200 ✅ (delta DEM-087 fechado)
- `GET http://localhost:9000/identity/pessoas` com token válido → 200 ✅ (delta JWT fechado)
- `POST /clinico/professionals` com CPF → `professionals.pessoa_id` preenchido ✅
- `POST /admin/identity/reconcile` → relatório de batch sem erros ✅
- `GET /admin-ui/identity` carrega sem erro 404 ✅
- Suite pytest completa passando (sem regressões)

## O que NÃO está em escopo

- Backfill de profissionais legados — fora de escopo (apenas pacientes via DEM-089)
- MinIO / DEM-070 — próxima sprint estratégica
