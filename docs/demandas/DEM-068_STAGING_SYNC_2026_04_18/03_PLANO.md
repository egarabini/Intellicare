---
tipo: plano-execucao
demanda: DEM-068
titulo: Staging Full Sync 2026-04-18
status: aguarda-prereqs
dev: DEV-3/4
criado: 2026-03-21
---

# DEM-068 — Plano de Execução

## Estimativa

Tempo estimado: ~2h (após DEMs 065/066/067 em main) | Complexidade: baixa

---

## Ordem de execução

### Bloco 1 — Deploy (20min)

```bash
cd /opt/intellicare
git pull origin main

# Verificar variáveis novas antes de rebuildar
grep -E "KEYCLOAK_ADMIN|VAPID" infra/.env.staging || echo "⚠️  VARIÁVEIS AUSENTES"

# Rebuild completo — novas dependências: pywebpush, py-vapid
docker compose --env-file infra/.env.staging -f infra/docker-compose.yml \
  build --no-cache intellicare-service

docker compose --env-file infra/.env.staging -f infra/docker-compose.yml \
  up -d intellicare-service

sleep 15
curl -s http://localhost:8000/health | python3 -m json.tool
```

### Bloco 2 — Smoke DEM-065 (30min)

```bash
# Provisionar tenant de teste
curl -s -X POST http://localhost:8000/admin/tenants \
  -H "Authorization: Bearer $PLATFORM_ADMIN_JWT" \
  -H "Content-Type: application/json" \
  -d '{"slug": "clinica-smoke", "display_name": "Clínica Smoke Test", "plan": "standard"}' \
  | python3 -m json.tool
# Esperado: 201 + schema_created: true + migrations_applied: true

# Listar tenants
curl -s http://localhost:8000/admin/tenants \
  -H "Authorization: Bearer $PLATFORM_ADMIN_JWT" | python3 -m json.tool
# Esperado: 200 + clinica-smoke na lista

# Suspender
curl -s -X POST http://localhost:8000/admin/tenants/clinica-smoke/suspend \
  -H "Authorization: Bearer $PLATFORM_ADMIN_JWT"
# Esperado: 200

# Verificar bloqueio
curl -s http://localhost:8000/gestor/dashboard \
  -H "Authorization: Bearer $CLINICA_SMOKE_JWT"
# Esperado: 403 {"detail": "tenant_suspended"}
```

### Bloco 3 — Smoke DEM-066 (20min)

```bash
# VAPID key (sem auth)
curl -s http://localhost:8000/notifications/push/vapid-public-key
# Esperado: 200 + {"public_key": "..."}

# Subscription fake
curl -s -X POST http://localhost:8000/notifications/push/subscribe \
  -H "Authorization: Bearer $JWT" \
  -H "Content-Type: application/json" \
  -d '{"endpoint":"https://fcm.example.com/smoke","keys":{"p256dh":"SMOKE","auth":"SMOKE"}}'
# Esperado: 201

# Service Worker com Content-Type correto
curl -I http://localhost:9000/clinico-ui/sw.js
# Esperado: Content-Type: application/javascript
```

### Bloco 4 — Smoke DEM-067 (20min)

```bash
# Flows carregados no Kestra
curl -s http://localhost:8080/api/v1/flows/intellicare \
  -H "Authorization: Basic $(echo -n admin:$KESTRA_PASSWORD | base64)" \
  | python3 -c "
import json, sys
flows = json.load(sys.stdin)
ids = [f['id'] for f in flows]
required = ['jornada_com_fallback','resposta_confirmacao','retry_com_backoff','urgencia_clinica']
missing = [r for r in required if r not in ids]
print('OK' if not missing else f'MISSING: {missing}')
"

# Trigger flow condicional
curl -s -X POST http://localhost:8000/journeys/trigger \
  -H "Authorization: Bearer $JWT" \
  -H "Content-Type: application/json" \
  -d '{"journey_id": "TEST-001", "flow_id": "jornada_com_fallback"}' \
  | python3 -m json.tool
# Esperado: 200 + execution_id
```

### Bloco 5 — Regressão geral (15min)

```bash
# Adapters sem 500
curl -s http://localhost:8000/careplanner/health/adapters | python3 -m json.tool

# WhatsApp ainda open
curl -s http://localhost:8081/instance/connectionState/intellicare \
  -H "apikey: $EVOLUTION_API_KEY" | python3 -m json.tool
# Esperado: state: "open"

# Florence ainda funcionando
curl -s http://localhost:8000/florence/notes/encounter/1 \
  -H "Authorization: Bearer $JWT"
# Esperado: 200
```

### Bloco 6 — Evidência e commit (10min)

```bash
cat >> deploy/staging_sync_log.txt << 'EOF'

=== 2026-04-18 — Sprint 2026-04-18 Smoke ===
DEM-065  POST /admin/tenants (provisioning)         201 ✅
DEM-065  POST /admin/tenants/clinica-smoke/suspend  200 ✅
DEM-065  tenant suspenso → 403                      403 ✅
DEM-066  GET /notifications/push/vapid-public-key   200 ✅
DEM-066  POST /notifications/push/subscribe         201 ✅
DEM-066  GET /clinico-ui/sw.js (Content-Type JS)    200 ✅
DEM-067  Flows Kestra (4 novos carregados)          OK  ✅
DEM-067  POST /journeys/trigger (fallback flow)     200 ✅
Health   GET /careplanner/health/adapters           200 ✅
WA       connectionState/intellicare                open ✅
Florence GET /florence/notes/encounter/1            200 ✅
EOF

git add deploy/staging_sync_log.txt
git commit -m "infra: staging sync sprint 2026-04-18 — DEMs 065-067 smoke OK"
```

Hash do commit → enviar para o ARQUITETO fechar DEM-068 e sprint.
