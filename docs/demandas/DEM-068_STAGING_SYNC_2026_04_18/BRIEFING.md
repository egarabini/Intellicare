# DEM-068 — Staging Full Sync 2026-04-18

**Sprint:** 2026-04-18
**Dev:** DEV-3/4
**Estimativa:** ~2h
**Prioridade:** Blocker de encerramento de sprint — executar após DEM-065, DEM-066 e DEM-067 mergeadas em `main`

---

## Objetivo

Validar no ambiente de staging que as três entregas do sprint 2026-04-18 (DEM-065, DEM-066, DEM-067) estão funcionando corretamente após deploy. Registrar evidências em `deploy/staging_sync_log.txt` e fechar o sprint.

---

## Pré-requisitos

- [ ] DEM-065 mergeada (`tenant_provisioner.py`, migration 015, TenantsManager)
- [ ] DEM-066 mergeada (`sw.js`, migration 016, push_sender, endpoints push)
- [ ] DEM-067 mergeada (flows condicionais, seed_flows atualizado)
- [ ] `git pull origin main` no VPS staging
- [ ] Rebuild do container `intellicare-service`

---

## Procedimento de deploy

```bash
# No VPS staging
cd /opt/intellicare
git pull origin main

# Rebuild completo (migrations novas + deps novas: pywebpush, py-vapid)
docker compose --env-file infra/.env.staging -f infra/docker-compose.yml \
  build --no-cache intellicare-service

docker compose --env-file infra/.env.staging -f infra/docker-compose.yml \
  up -d intellicare-service

# Aguardar health check
sleep 15
curl -s http://localhost:8000/health | python3 -m json.tool
```

---

## Smoke tests

### DEM-065 — Multi-tenant

```bash
# 1. Provisionar tenant de teste
curl -s -X POST http://localhost:8000/admin/tenants \
  -H "Authorization: Bearer $PLATFORM_ADMIN_JWT" \
  -H "Content-Type: application/json" \
  -d '{"slug": "clinica-smoke", "display_name": "Clínica Smoke Test", "plan": "standard"}' \
  | python3 -m json.tool
# Esperado: 201 + status de cada etapa de provisionamento

# 2. Listar tenants
curl -s http://localhost:8000/admin/tenants \
  -H "Authorization: Bearer $PLATFORM_ADMIN_JWT" | python3 -m json.tool
# Esperado: 200 + clinica-smoke na lista

# 3. Suspender tenant
curl -s -X POST http://localhost:8000/admin/tenants/clinica-smoke/suspend \
  -H "Authorization: Bearer $PLATFORM_ADMIN_JWT"
# Esperado: 200

# 4. Verificar bloqueio
curl -s http://localhost:8000/gestor/dashboard \
  -H "Authorization: Bearer $CLINICA_SMOKE_JWT"
# Esperado: 403 {"detail": "tenant_suspended"}
```

### DEM-066 — Push PWA

```bash
# 1. VAPID public key disponível sem auth
curl -s http://localhost:8000/notifications/push/vapid-public-key
# Esperado: 200 + {"public_key": "..."}

# 2. Registrar subscription fake
curl -s -X POST http://localhost:8000/notifications/push/subscribe \
  -H "Authorization: Bearer $JWT" \
  -H "Content-Type: application/json" \
  -d '{
    "endpoint": "https://fcm.googleapis.com/fcm/send/smoke-test-endpoint",
    "keys": {"p256dh": "SMOKE_KEY", "auth": "SMOKE_AUTH"}
  }'
# Esperado: 201

# 3. Service worker registrável (verificar header correto)
curl -I http://localhost:9000/clinico-ui/sw.js
# Esperado: 200 + Content-Type: application/javascript + Service-Worker-Allowed header
```

### DEM-067 — Kestra Flows

```bash
# 1. Verificar flows carregados no Kestra
curl -s http://localhost:8080/api/v1/flows/intellicare \
  -H "Authorization: Basic $(echo -n admin:$KESTRA_PASSWORD | base64)" \
  | python3 -c "import json,sys; flows=json.load(sys.stdin); print([f['id'] for f in flows])"
# Esperado: [..., 'jornada_com_fallback', 'resposta_confirmacao', 'retry_com_backoff', 'urgencia_clinica']

# 2. Trigger flow condicional
curl -s -X POST http://localhost:8000/journeys/trigger \
  -H "Authorization: Bearer $JWT" \
  -H "Content-Type: application/json" \
  -d '{"journey_id": "...", "flow_id": "jornada_com_fallback"}' \
  | python3 -m json.tool
# Esperado: 200 + execution_id
```

### Health geral

```bash
curl -s http://localhost:8000/health/adapters | python3 -m json.tool
# Esperado: 200 sem 500s

curl -s http://localhost:8081/instance/connectionState/intellicare \
  -H "apikey: $EVOLUTION_API_KEY" | python3 -m json.tool
# Esperado: state: "open"
```

---

## Variáveis de ambiente a verificar no `.env.staging`

```bash
# Novas — necessárias para DEM-065 e DEM-066
KEYCLOAK_ADMIN_URL=http://keycloak:8080
KEYCLOAK_ADMIN_USER=admin
KEYCLOAK_ADMIN_PASSWORD=<senha>
VAPID_PUBLIC_KEY=<chave>
VAPID_PRIVATE_KEY=<chave>
VAPID_SUBJECT=mailto:admin@intellicare.ia.br
```

Se alguma estiver ausente, adicionar ao `.env.staging` e fazer `up -d` novamente.

---

## Registro de evidência

```bash
cat >> deploy/staging_sync_log.txt << 'EOF'

=== 2026-04-18 — Sprint 2026-04-18 Smoke ===
DEM-065  POST /admin/tenants (provisioning)         201 ✅
DEM-065  POST /admin/tenants/clinica-smoke/suspend  200 ✅
DEM-065  GET /gestor/dashboard (tenant suspenso)    403 ✅
DEM-066  GET /notifications/push/vapid-public-key   200 ✅
DEM-066  POST /notifications/push/subscribe         201 ✅
DEM-066  GET /clinico-ui/sw.js                      200 ✅
DEM-067  Flows Kestra (4 novos carregados)          OK  ✅
DEM-067  POST /journeys/trigger (fallback flow)     200 ✅
Health   GET /health/adapters                       200 ✅
WA       connectionState/intellicare                open ✅
EOF

git add deploy/staging_sync_log.txt
git commit -m "infra: staging sync sprint 2026-04-18 — DEMs 065-067 smoke OK"
```

---

## Critério de aceite

1. Tenant `clinica-smoke` provisionado com schema criado no PostgreSQL
2. `state: open` no WhatsApp Evolution (sem regressão)
3. 4 flows condicionais visíveis no Kestra
4. VAPID key disponível e sw.js servido com Content-Type correto
5. Commit de evidência enviado — hash para fechar DEM-068 e sprint
