---
tipo: especificacao-tecnica
demanda: DEM-074
titulo: Staging Sync 2026-04-25
---

# DEM-074 — Especificação Técnica

## Checklist de aplicação

### 1. Pull e rebuild

```bash
# No VPS staging
cd /opt/intellicare
git pull origin main

# Rebuild dos containers afetados
docker compose build api adminui clinicoui
docker compose up -d
```

Containers afetados pelo sprint 2026-04-25:
- `api` — migration 017, novos endpoints (timeline, receituário, admin/prompts)
- `adminui` — PromptsPage nova
- `clinicoui` — ClinicalTimeline + OswaldoPrescriptionEditor com botão receituário

---

### 2. Migration 017

> O repo **não usa Alembic**. A migration 017 entra via runner SQL em `tools/scripts/seed_demo.py`, executado **manualmente** — não roda automaticamente no startup do container.

```bash
docker compose exec db psql -U postgres -d intellicare \
  -f /app/db/platform_migrations/017_prompt_templates.sql
```

Verificar seeds após apply:
```bash
docker compose exec db psql -U postgres -d intellicare -c \
  "SELECT slug, version, is_active FROM platform.prompt_templates ORDER BY slug, version;"
```

Saída esperada:
```
       slug            | version | is_active
-----------------------+---------+-----------
 florence_free_text    |       1 | t
 florence_soap         |       1 | t
 oswaldo_cid10         |       1 | t
 oswaldo_prescription  |       1 | t
```

---

### 3. Smoke tests — Endpoints novos

#### 3a. Timeline

```bash
# Obter token
TOKEN=$(curl -s -X POST http://staging:8000/auth/token \
  -d "username=clinico@test.com&password=test123" | jq -r '.access_token')

# Smoke timeline (usar patient_id real do staging)
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://staging:8000/cuidado/patients/PATIENT_ID/timeline?days=90" | jq '{total, event_count: (.events | length)}'
```

Resposta esperada: `{"total": N, "event_count": N}` com N > 0.

#### 3b. Receituário PDF

```bash
# Smoke receituário (usar prescription_id real do staging)
curl -s -o /tmp/receituario_test.pdf \
  -H "Authorization: Bearer $TOKEN" \
  "http://staging:8000/oswaldo/prescriptions/PRESCRIPTION_ID/receituario.pdf?type=simple"

# Verificar que é um PDF válido
file /tmp/receituario_test.pdf
# Esperado: "PDF document, version 1.x"
```

#### 3c. Prompt Versioning API

```bash
# Listar prompts
curl -s -H "Authorization: Bearer $ADMIN_TOKEN" \
  "http://staging:8000/admin/prompts" | jq '[.[] | {slug, active_version}]'

# Salvar nova versão
curl -s -X POST -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content": "Teste de versão staging.", "description": "Smoke test DEM-074"}' \
  "http://staging:8000/admin/prompts/florence_soap/versions" | jq '{slug, version, is_active}'

# Ativar versão anterior (rollback)
curl -s -X POST -H "Authorization: Bearer $ADMIN_TOKEN" \
  "http://staging:8000/admin/prompts/florence_soap/versions/1/activate"
```

---

### 4. Smoke AdminUI

Acesso manual: `http://staging-adminui/prompts`

Verificar:
- [ ] Página carrega sem erro de console
- [ ] 4 slugs listados
- [ ] Clicar em `florence_soap` abre editor com conteúdo
- [ ] Salvar nova versão → histórico atualiza
- [ ] Ativar versão anterior → badge "ATIVO" move para versão selecionada

---

### 5. Smoke ClinicoUI

Acesso manual: `http://staging-clinico`

Verificar:
- [ ] PatientProfile → aba "Linha do Tempo" carrega eventos
- [ ] Filtro por tipo funciona (encounters, notes, etc.)
- [ ] OswaldoPrescriptionEditor → botão "Imprimir Receituário" abre PDF em nova aba
- [ ] PDF gerado tem cabeçalho com CRM, símbolo ℞, posologia formal

---

### 6. Rodar suite de testes no container

```bash
docker compose exec api pytest tests/test_timeline.py tests/test_receituario.py tests/test_prompt_versioning.py -v
```

Resultado esperado: todos passando (mínimo: 4 + 3 + 4 = 11 testes).

---

## Rollback de emergência

Se migration 017 falhar:

```bash
docker compose exec api alembic downgrade 016
```

Se API não subir após rebuild:

```bash
# Ver logs
docker compose logs api --tail=100

# Voltar para imagem anterior (se tagged)
docker compose down api
docker tag intellicare-api:previous intellicare-api:latest
docker compose up -d api
```

---

## Variáveis de ambiente — verificar antes do deploy

| Variável | Obrigatória em | Observação |
|----------|---------------|------------|
| `WEASYPRINT_FONTS_DIR` | api | Opcional — fontes DejaVu para símbolo ℞ |
| `PLATFORM_DATABASE_URL` | api | Tabela `prompt_templates` fica no schema `platform` |

> `PLATFORM_DATABASE_URL` é o mesmo `DATABASE_URL` se platform e tenant compartilham instância PostgreSQL. Confirmar antes do deploy.
