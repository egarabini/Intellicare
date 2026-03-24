---
tipo: plano-execucao
demanda: DEM-086
titulo: Staging Sync 2026-05-16
status: planejada
dev: DEV-1
sprint: 2026-05-16
criado: 2026-03-23
---

# DEM-086 — Plano de Execução

## Estimativa

Tempo estimado: ~2h | Complexidade: média

Sync menos complexa que DEM-082 — sem Dify workflow manual, sem Keycloak novos usuários. O risco principal é a migration 022 em múltiplos schemas e o smoke de idempotência do identity service.

## Pré-condições

- [ ] DEM-083 em `origin/main` e push confirmado
- [ ] DEM-084 em `origin/main` e push confirmado
- [ ] DEM-085 em `origin/main` e push confirmado (inclui migration 023)

---

## Ordem de execução

### Bloco 1 — Pull, rebuild e migrations (45min)
1. `git pull origin main` — confirmar commits DEM-083, DEM-084, DEM-085 no topo
2. `docker compose build api && docker compose up -d --force-recreate`
3. Health check: `curl http://staging/api/health` → `{"status": "healthy"}`
4. Aplicar migration 021 (platform) — ver `02_TECNICA.md §2`
5. Aplicar migration 022 em todos os tenants ativos
6. Aplicar migration 023 em todos os tenants (fix clinical_notes)
7. Verificar colunas: `\d demo.paciente | grep pessoa_id` e `\d demo.clinical_notes | grep encounter_id`

### Bloco 2 — Smokes identity (30min)
8. Smoke CPF inexistente → 404
9. Smoke find-or-create → 201 com UUID
10. Smoke idempotência → mesmo UUID em duas chamadas com mesmo CPF
11. Smoke `POST /cuidado/patients` com CPF → `pessoa_id` não-null no retorno

### Bloco 3 — Smokes regressão e saneamento (30min)
12. Smoke paciente legado (sem CPF) → continua funcionando
13. Smoke timeline, Florence, prescrição — zero regressões
14. CarePlanner Redis: 60s de logs sem erros de auth

### Bloco 4 — Suite pytest e fechamento (15min)
15. `pytest -x -v` → zero falhas
16. Commit e push:
```
chore(staging): sync 2026-05-16 — identity foundation, patient pessoa_id, saneamento técnico
```

---

## Entrega

```
chore(staging): sync 2026-05-16 — platform.pessoa, patient pessoa_id, migrations 021/022/023
```
Hash → enviar ao ARQUITETO após `git push origin HEAD:main` confirmado.
