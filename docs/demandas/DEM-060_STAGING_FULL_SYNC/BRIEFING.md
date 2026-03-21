# DEM-060 — Staging Full Sync (DEMs 054–059)

> **Dev:** DEV-3/4
> **Estimativa:** ~1.5h
> **Dependência:** DEMs 054, 055, 056, 057, 058, 059 commitadas em main

---

## Contexto

O staging foi atualizado pela última vez em `06a0b1e` (DEM-053). As DEMs 054–059
entram nesta sprint. Esta DEM sincroniza o VPS, aplica as migrations novas e valida
que os módulos Florence e Oswaldo sobem sem erro.

---

## STEP-001 — Pull e rebuild no VPS

```bash
cd /opt/intellicare

# Confirmar branch e pull
git status
git pull origin main
git log --oneline -8

# Rebuild do intellicare-service (migrations + static)
docker compose --env-file infra/.env.staging -f infra/docker-compose.yml \
  build --no-cache intellicare-service

docker compose --env-file infra/.env.staging -f infra/docker-compose.yml \
  up -d intellicare-service
```

## STEP-002 — Verificar migrations

```bash
# Confirmar que migrations 012, 013 e 014 foram aplicadas
docker compose --env-file infra/.env.staging -f infra/docker-compose.yml \
  exec postgres psql -U intellicare_staging -d intellicare_alfa \
  -c "\dt care_tasks, clinical_notes, prescriptions"
```

**Critério:** tabelas `clinical_notes` e `prescriptions` presentes. Coluna
`appointment_id` visível em `care_tasks`:

```bash
docker compose --env-file infra/.env.staging -f infra/docker-compose.yml \
  exec postgres psql -U intellicare_staging -d intellicare_alfa \
  -c "\d care_tasks" | grep appointment_id
```

## STEP-003 — Smoke endpoints novos

```bash
BASE="https://api.intellicare.ia.br/api"
TOKEN="<JWT_CLINICO>"   # obter via login no staging

# Florence
curl -s -H "Authorization: Bearer $TOKEN" \
  "$BASE/florence/notes/encounter/1" | python3 -m json.tool

# Oswaldo CID-10
curl -s -H "Authorization: Bearer $TOKEN" \
  "$BASE/oswaldo/cid10/search?q=rinofar" | python3 -m json.tool

# Portal jornadas (com token PACIENTE)
TOKEN_PAC="<JWT_PACIENTE>"
curl -s -H "Authorization: Bearer $TOKEN_PAC" \
  "$BASE/portal/me/journeys" | python3 -m json.tool
```

**Critério:** todos retornam 200 (lista vazia é aceito).

## STEP-004 — Verificar WhatsApp ainda conectado

```bash
curl -s http://localhost:8081/instance/connectionState/intellicare \
  -H "apikey: $(grep EVOLUTION_API_KEY /opt/intellicare/infra/.env.staging | cut -d= -f2)"
```

**Critério:** `{"state":"open"}`. Se `close`, recriar instância conforme DEM-053.

## STEP-005 — Healthcheck geral

```bash
curl -s https://api.intellicare.ia.br/api/health/adapters | python3 -m json.tool
curl -s https://api.intellicare.ia.br/api/health | python3 -m json.tool
```

## STEP-006 — Commit de evidência

```bash
# Registrar sync no histórico (arquivo de evidência mínimo)
echo "Staging sync 2026-04-04: DEMs 054-059 aplicadas. Migrations OK. Florence+Oswaldo UP." \
  >> /opt/intellicare/deploy/staging_sync_log.txt

git add deploy/staging_sync_log.txt
git commit -m "infra: staging sync DEMs 054-059 + Florence+Oswaldo UP"
git push origin main
```

---

## Critérios de Aceite

- [ ] `git log` mostra commits DEM-054 a DEM-059 aplicados no VPS
- [ ] Tabelas `clinical_notes` e `prescriptions` existem no banco do tenant
- [ ] Coluna `appointment_id` presente em `care_tasks`
- [ ] `GET /florence/notes/encounter/1` retorna 200
- [ ] `GET /oswaldo/cid10/search?q=rinofar` retorna 200
- [ ] `GET /portal/me/journeys` retorna 200
- [ ] `connectionState` Evolution ainda em `open`
- [ ] `GET /health/adapters` sem erro 500
