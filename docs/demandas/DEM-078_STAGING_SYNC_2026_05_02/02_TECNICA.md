---
tipo: especificacao-tecnica
demanda: DEM-078
titulo: Staging Sync 2026-05-02
---

# DEM-078 — Especificação Técnica

## Checklist de aplicação

### 1. Pull e rebuild

```bash
cd /opt/intellicare
git pull origin main
# Confirmar 3 commits do sprint: DEM-075 (6ed6281) + DEM-076 (8e5fa8a) + DEM-077 (3105284)

docker compose build api clinicoui pacienteui
docker compose up -d
```

> ⚠️ O rebuild desta vez inclui os containers Marie (Dify). O `docker compose up -d` vai baixar as imagens `langgenius/dify-api:0.6.11` e `langgenius/dify-web:0.6.11` na primeira execução — pode demorar 5-10 minutos dependendo da conexão.

---

### 2. Aplicar migration 018 (interaction prompts)

> DEM-077 adicionou `db/platform_migrations/018_interaction_prompts.sql` com seed do slug `oswaldo_interaction_check`.

```bash
docker compose exec db psql -U postgres -d intellicare \
  -f /app/db/platform_migrations/018_interaction_prompts.sql

# Verificar seed inserido
docker compose exec db psql -U postgres -d intellicare -c \
  "SELECT slug, version, is_active FROM platform.prompt_templates WHERE slug = 'oswaldo_interaction_check';"
# Esperado: 1 row, is_active = t
```

---

### 3. Verificar containers Marie

```bash
docker compose ps | grep marie
# Esperado: marie-db, marie-redis, marie-api, marie-worker, marie-web — todos Up

# Verificar logs marie-api (primeira inicialização roda migrations Dify)
docker compose logs marie-api --tail=50
# Aguardar: "Application startup complete" sem erros
```

---

### 3. Configurar workflow Dify (primeira vez no staging)

```bash
# Acessar interface Marie
# http://staging-ip:porta/marie-web  (verificar porta no docker-compose.yml)

# 1. Criar conta admin Dify
# 2. Criar workspace "IntelliCare"
# 3. Criar Chatflow "cid10_rag" (ver 02_TECNICA.md DEM-075 §Workflow Dify)
# 4. Publicar workflow
# 5. Gerar API Key → copiar para .env.staging: MARIE_API_KEY=sk-...
# 6. Reiniciar container api para carregar nova API Key
docker compose restart api
```

---

### 4. Smoke — Interação Medicamentosa

```bash
TOKEN=$(curl -s -X POST http://staging:8000/auth/token \
  -d "username=dr.silva@test.com&password=test123" | jq -r '.access_token')

curl -s -X POST http://staging:8000/oswaldo/check-interactions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"medications": ["varfarina", "AAS", "atenolol"]}' | jq '{warnings_count: (.warnings | length), first_severity: .warnings[0].severity}'
# Esperado: {"warnings_count": 1, "first_severity": "GRAVE"}
```

---

### 5. Smoke — Portal Paciente Timeline

```bash
PAC_TOKEN=$(curl -s -X POST http://staging:8000/auth/token \
  -d "username=paciente@test.com&password=test123" | jq -r '.access_token')

curl -s -H "Authorization: Bearer $PAC_TOKEN" \
  "http://staging:8000/cuidado/paciente/me/timeline?limit=10" | jq '{total, no_soap_a: ([.events[] | select(.metadata.soap_a != null)] | length)}'
# Esperado: {total: N, no_soap_a: 0}  ← campo soap_a nunca deve aparecer
```

---

### 6. Smoke — Receituário do Paciente

```bash
# Obter ID de uma prescrição do paciente de teste
PRESC_ID=$(curl -s -H "Authorization: Bearer $PAC_TOKEN" \
  "http://staging:8000/cuidado/paciente/me/timeline" | jq -r '[.events[] | select(.type == "prescription")][0].id')

curl -s -o /tmp/receituario_paciente.pdf \
  -H "Authorization: Bearer $PAC_TOKEN" \
  "http://staging:8000/oswaldo/paciente/me/prescriptions/$PRESC_ID/receituario.pdf?type=simple"

file /tmp/receituario_paciente.pdf
# Esperado: PDF document
```

---

### 7. Suite de testes

```bash
docker compose exec api pytest \
  tests/test_marie_client.py \
  tests/test_portal_avancado.py \
  tests/test_oswaldo_interactions.py \
  -v
# Esperado: todos passando (mínimo 4 + 4 + 5 = 13 testes)
```

---

### 8. Smoke Manual — ClinicoUI banner de interação

Acesso manual: `http://staging-clinico`

- [ ] Oswaldo → abrir prescrição → adicionar "Varfarina" → adicionar "AAS" → banner vermelho aparece
- [ ] Clicar "Entendido — manter prescrição" → banner fecha
- [ ] Adicionar medicamentos sem interação conhecida → nenhum banner

---

## Variáveis de ambiente novas (adicionar ao `.env.staging`)

```env
MARIE_ENABLED=false
MARIE_API_URL=http://marie-api:5001
MARIE_API_KEY=        # preencher após setup Dify
MARIE_TIMEOUT_SECONDS=10
MARIE_DB_PASSWORD=marie-staging-db-pass
MARIE_REDIS_PASSWORD=marie-staging-redis-pass
MARIE_SECRET_KEY=marie-staging-secret
```
