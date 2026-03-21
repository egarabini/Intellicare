---
tipo: especificacao-funcional
demanda: DEM-068
titulo: Staging Full Sync 2026-04-18
sprint: 2026-04-18
status: aguarda-prereqs
dev: DEV-3/4
criado: 2026-03-21
depende_de: [DEM-065, DEM-066, DEM-067]
habilita: []
tags: [staging, deploy, smoke, infra]
---

# DEM-068 — Staging Full Sync 2026-04-18

## Objetivo

Validar que as entregas do sprint 2026-04-18 (DEM-065, DEM-066, DEM-067) estão funcionando corretamente no ambiente de staging após deploy, sem regressões nos módulos anteriores. Registrar evidências e fechar o sprint.

---

## Pré-requisitos

- [ ] DEM-065 mergeada em `main`
- [ ] DEM-066 mergeada em `main`
- [ ] DEM-067 mergeada em `main`
- [ ] `git pull origin main` no VPS staging executado

---

## Critérios de aceite

1. **DEM-065** — Tenant `clinica-smoke` provisionado via API, schema criado no PostgreSQL, tenant suspenso retorna 403
2. **DEM-066** — VAPID key disponível, `sw.js` servido com Content-Type correto, subscription salva no banco
3. **DEM-067** — 4 flows novos visíveis no Kestra, trigger com `flow_id: jornada_com_fallback` retorna execution_id
4. **Regressão** — Evolution `state: open`, `GET /health/adapters` sem 500
5. Evidências registradas em `deploy/staging_sync_log.txt` e commitadas

---

## Fora de escopo

- Testes de push real no dispositivo (verificação apenas de endpoint e SW)
- Teste de flow de urgência com temporizadores reais (mock suficiente)
