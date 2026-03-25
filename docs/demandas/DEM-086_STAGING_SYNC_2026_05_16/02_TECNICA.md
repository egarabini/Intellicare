---
tipo: tecnica
demanda: DEM-086
titulo: Staging Sync 2026-05-16
status: planejada
dev: DEV-1
sprint: 2026-05-16
criado: 2026-03-23
---

# DEM-086 — Técnica: Staging Sync 2026-05-16

## 1. Pull e rebuild

```bash
git pull origin main
# Confirmar 3+ commits no topo: DEM-083, DEM-084, DEM-085

docker compose build api clinicoui gestorui pacienteui
docker compose up -d --force-recreate
docker compose ps  # todos healthy
```

---

## 2. Migrations

### Platform — migration 021

```bash
psql -U postgres -d intellicare \
  -f db/platform_migrations/021_pessoa_identity.sql

# Verificar tabelas criadas
psql -U postgres -d intellicare -c \
  "SELECT table_name FROM information_schema.tables WHERE table_schema = 'platform' ORDER BY table_name;"
# Esperado: pessoa, pessoa_contato, pessoa_estabelecimento, pessoa_fisica, pessoa_juridica, prompt_templates (pré-existente)
```

### Tenant — migration 022 (todos os schemas ativos)

```bash
for schema in demo tenant_clinica_alfa tenant_consultorio_gamma tenant_hospital_beta; do
  echo "Applying 022 to $schema..."
  sed "s/{schema}/$schema/g" db/tenant_migrations/022_paciente_pessoa_id.sql | \
    docker compose exec -T db psql -U postgres -d intellicare
done

# Verificar coluna
docker compose exec db psql -U postgres -d intellicare \
  -c "\d demo.paciente" | grep pessoa_id
# Esperado: pessoa_id | uuid | nullable
```

### Tenant — migration 023 (fix clinical_notes, se aplicável)

```bash
for schema in demo tenant_clinica_alfa tenant_consultorio_gamma tenant_hospital_beta; do
  sed "s/{schema}/$schema/g" db/tenant_migrations/023_fix_clinical_notes_encounter_id.sql | \
    docker compose exec -T db psql -U postgres -d intellicare
done
```

---

## 3. Smokes

### Identity service

```bash
TOKEN=$(curl -s -X POST http://staging/api/auth/token \
  -d "username=dr.silva&password=Demo@1234&client_id=clinico-ui" | jq -r '.access_token')

# CPF inexistente → 404
curl -s -H "Authorization: Bearer $TOKEN" \
  http://staging/api/identity/pessoas/cpf/00000000000 | jq '.detail'
# Esperado: "Pessoa não encontrada"

# Criar pessoa
curl -s -X POST http://staging/api/identity/pessoas \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"nome_completo": "DR TESTE SILVA", "cpf": "12345678901"}' | jq '{id, nome_completo, cpf}'
# Esperado: {id: "uuid...", nome_completo: "DR TESTE SILVA", cpf: "12345678901"}

# Idempotência — mesmo CPF → mesmo UUID
UUID1=$(curl -s -X POST http://staging/api/identity/pessoas \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"nome_completo": "DR TESTE SILVA", "cpf": "12345678901"}' | jq -r '.id')

UUID2=$(curl -s -X POST http://staging/api/identity/pessoas \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"nome_completo": "DR TESTE SILVA", "cpf": "12345678901"}' | jq -r '.id')

[ "$UUID1" = "$UUID2" ] && echo "IDEMPOTÊNCIA OK" || echo "FALHA: UUIDs diferentes"
```

### Paciente com CPF → `pessoa_id` preenchido

```bash
curl -s -X POST http://staging/api/cuidado/patients \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "nome_completo": "Paciente Teste",
    "cpf": "98765432100",
    "data_nascimento": "1990-01-15"
  }' | jq '{id, nome_completo, pessoa_id}'
# Esperado: pessoa_id não-null
```

### CarePlanner Redis (confirmar fix DEM-085)

```bash
docker compose logs careplanner-worker --since=60s | grep -i "redis\|password\|auth\|error" | wc -l
# Esperado: 0 (zero linhas de erro)
```

---

## 4. Suite completa

```bash
pytest -x -v 2>&1 | tail -20
# Esperado: todos passed, zero failed
```

---

## Keycloak — sem novos usuários nesta sync

Nenhum novo role ou usuário Keycloak neste sprint. A identidade centralizada é transparente para o Keycloak — o mesmo `keycloak_id` continua sendo usado para auth.

---

## Gotcha — `platform` schema já existe?

Confirmar antes de aplicar migration 021:
```sql
SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'platform';
```
Se não existir: `CREATE SCHEMA platform;` antes de rodar o script.
Na prática deve existir desde a migration 017 (`prompt_templates`).
