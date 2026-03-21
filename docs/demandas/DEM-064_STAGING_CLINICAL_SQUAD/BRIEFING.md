# DEM-064 — Staging Clinical Squad Validation

> **Dev:** DEV-3/4
> **Estimativa:** ~1.5h
> **Pré-requisito:** DEM-060 concluída + DEMs 061–063 commitadas em main

---

## Contexto

Após DEM-060 sincronizar as DEMs 054–059, esta DEM sincroniza as DEMs 061–063
e valida o Clinical Squad completo em staging: Florence IA, Oswaldo IA, PDF clínico
e cobertura E2E.

---

## STEP-001 — Pull e rebuild

```bash
cd /opt/intellicare
git pull origin main
git log --oneline -6

docker compose --env-file infra/.env.staging -f infra/docker-compose.yml \
  build --no-cache intellicare-service
docker compose --env-file infra/.env.staging -f infra/docker-compose.yml \
  up -d intellicare-service

# Aguardar startup
sleep 20
docker compose --env-file infra/.env.staging -f infra/docker-compose.yml logs \
  intellicare-service --tail=30
```

## STEP-002 — Smoke Clinical Squad

```bash
TOKEN="<JWT_CLINICO>"
BASE="https://api.intellicare.ia.br/api"

# Florence suggest (rule-based sem LLM)
curl -s -X POST "$BASE/florence/notes/suggest" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"encounter_id":1,"patient_id":1,"chief_complaint":"Teste staging"}' \
  | python3 -m json.tool

# Oswaldo CID-10
curl -s "$BASE/oswaldo/cid10/search?q=rinofar" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

# Oswaldo suggest (rule-based)
curl -s -X POST "$BASE/oswaldo/suggest" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"encounter_id":1,"patient_id":1,"chief_complaint":"Dor de garganta"}' \
  | python3 -m json.tool

# PDF clínico
curl -s -o /tmp/test_report.pdf \
  "$BASE/encontros/1/report.pdf" \
  -H "Authorization: Bearer $TOKEN"
file /tmp/test_report.pdf   # Esperado: PDF document
```

## STEP-003 — Verificar WhatsApp ainda conectado

```bash
curl -s http://localhost:8081/instance/connectionState/intellicare \
  -H "apikey: $(grep EVOLUTION_API_KEY /opt/intellicare/infra/.env.staging | cut -d= -f2)"
# Esperado: {"state":"open"}
```

## STEP-004 — Healthcheck geral

```bash
curl -s https://api.intellicare.ia.br/api/health/adapters | python3 -m json.tool
```

## STEP-005 — Commit de evidência

```bash
echo "Staging sync 2026-04-11: DEMs 061-063 + Clinical Squad validado." \
  >> /opt/intellicare/deploy/staging_sync_log.txt
git add deploy/staging_sync_log.txt
git commit -m "infra: staging sync DEMs 061-063 + Clinical Squad smoke OK"
git push origin main
```

---

## Critérios de Aceite

- [ ] `git log` mostra DEMs 061–063 no VPS
- [ ] `POST /florence/notes/suggest` retorna `SOAPSuggestion` (rule-based)
- [ ] `GET /oswaldo/cid10/search` retorna lista
- [ ] `POST /oswaldo/suggest` retorna sugestão (rule-based)
- [ ] `GET /encontros/1/report.pdf` retorna arquivo PDF válido
- [ ] Evolution `connectionState` ainda em `open`
- [ ] `GET /health/adapters` sem erro 500
