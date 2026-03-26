# DEM-093 — Plano de Execução

## Pré-requisitos

- Acesso SSH ao VPS staging
- Código `origin/main` já no VPS (`git status` deve mostrar em dia — confirmado em DEM-091)
- Diretório de trabalho: `~/INTELLICARE` (raiz do projeto no VPS)

---

## PASSO 0 — Verificação do estado atual

```bash
# Confirmar que o schema platform existe e se 021 já foi aplicada
docker exec intellicare-postgres psql \
  -U intellicare_staging intellicare_staging \
  -c "\dn" | grep platform

# Confirmar ausência de prompt_templates
docker exec intellicare-postgres psql \
  -U intellicare_staging intellicare_staging \
  -c "\dt public.*"

# Confirmar ausência de professionals no tenant
docker exec intellicare-postgres psql \
  -U intellicare_staging intellicare_staging \
  -c "\dt tenant_clinica_alfa.*"
```

**Resultado esperado pré-execução:**
- `platform` schema: ausente (ou presente sem tabelas pessoa*)
- `public.prompt_templates`: ausente
- `tenant_clinica_alfa.professionals`: ausente

---

## PASSO 1 — Migration 017: prompt_templates (public)

```bash
docker exec -i intellicare-postgres psql \
  -U intellicare_staging intellicare_staging \
  < db/platform_migrations/017_prompt_templates.sql
```

**Verificação:**
```bash
docker exec intellicare-postgres psql \
  -U intellicare_staging intellicare_staging \
  -c "SELECT prompt_key, version, is_active FROM public.prompt_templates ORDER BY prompt_key;"
```
Esperado: 4 linhas (florence_free_text, florence_soap, oswaldo_cid10, oswaldo_prescription)

---

## PASSO 2 — Migration 021: identity platform (platform schema)

> **Verificar antes**: se `SELECT COUNT(*) FROM platform.pessoa` retornar número (não erro), pular este passo.

```bash
docker exec -i intellicare-postgres psql \
  -U intellicare_staging intellicare_staging \
  < db/platform_migrations/021_pessoa_identity.sql
```

**Verificação:**
```bash
docker exec intellicare-postgres psql \
  -U intellicare_staging intellicare_staging \
  -c "\dt platform.*"
```
Esperado: `platform.pessoa`, `platform.pessoa_fisica`, `platform.pessoa_juridica`, `platform.pessoa_contato`, `platform.pessoa_estabelecimento`

---

## PASSO 3 — Migration 005: gestão completa (tenant fundacional)

```bash
(echo "SET search_path TO tenant_clinica_alfa;"; \
 cat db/tenant_migrations/005_gestao_completa.sql) | \
 docker exec -i intellicare-postgres psql \
   -U intellicare_staging intellicare_staging
```

**Verificação:**
```bash
docker exec intellicare-postgres psql \
  -U intellicare_staging intellicare_staging \
  -c "SELECT COUNT(*) FROM tenant_clinica_alfa.professionals;"
```
Esperado: `0` (tabela existe, sem dados ainda)

---

## PASSO 4 — Migration 006: clínico gestão (extensões de tenant)

```bash
(echo "SET search_path TO tenant_clinica_alfa;"; \
 cat db/tenant_migrations/006_clinico_gestao.sql) | \
 docker exec -i intellicare-postgres psql \
   -U intellicare_staging intellicare_staging
```

**Verificação:**
```bash
docker exec intellicare-postgres psql \
  -U intellicare_staging intellicare_staging \
  -c "\dt tenant_clinica_alfa.professional_group*"
```

---

## PASSO 5 — Migration 019: certificados digitais (tenant)

```bash
(echo "SET search_path TO tenant_clinica_alfa;"; \
 cat db/platform_migrations/019_professional_certificates.sql) | \
 docker exec -i intellicare-postgres psql \
   -U intellicare_staging intellicare_staging
```

**Verificação:**
```bash
docker exec intellicare-postgres psql \
  -U intellicare_staging intellicare_staging \
  -c "SELECT COUNT(*) FROM tenant_clinica_alfa.professional_certificates;"
```

---

## PASSO 6 — Migration 020: interaction_count em prescriptions

```bash
sed 's/{schema}/tenant_clinica_alfa/g' \
  db/tenant_migrations/020_prescription_interaction_count.sql | \
  docker exec -i intellicare-postgres psql \
    -U intellicare_staging intellicare_staging
```

**Verificação:**
```bash
docker exec intellicare-postgres psql \
  -U intellicare_staging intellicare_staging \
  -c "SELECT column_name, data_type, column_default \
      FROM information_schema.columns \
      WHERE table_schema='tenant_clinica_alfa' \
        AND table_name='prescriptions' \
        AND column_name='interaction_warnings_count';"
```
Esperado: `interaction_warnings_count | integer | 0`

---

## PASSO 7 — Migration 022: pessoa_id em patients

```bash
sed 's/{schema}/tenant_clinica_alfa/g' \
  db/tenant_migrations/022_paciente_pessoa_id.sql | \
  docker exec -i intellicare-postgres psql \
    -U intellicare_staging intellicare_staging
```

**Verificação:**
```bash
docker exec intellicare-postgres psql \
  -U intellicare_staging intellicare_staging \
  -c "SELECT column_name, data_type \
      FROM information_schema.columns \
      WHERE table_schema='tenant_clinica_alfa' \
        AND table_name='patients' \
        AND column_name='pessoa_id';"
```

---

## PASSO 8 — Migration 023: converter encounter_id BIGINT→UUID em clinical_notes

> ⚠️ **DESTRUTIVA** — valores existentes de `encounter_id` são descartados.
> Verificar se há dados antes:

```bash
docker exec intellicare-postgres psql \
  -U intellicare_staging intellicare_staging \
  -c "SELECT COUNT(*) FROM tenant_clinica_alfa.clinical_notes WHERE encounter_id IS NOT NULL;"
```

Se resultado > 0 e dados forem importantes, fazer backup antes:
```bash
docker exec intellicare-postgres psql \
  -U intellicare_staging intellicare_staging \
  -c "SELECT * FROM tenant_clinica_alfa.clinical_notes" > /tmp/clinical_notes_backup.csv
```

Aplicar migration:
```bash
sed 's/{schema}/tenant_clinica_alfa/g' \
  db/tenant_migrations/023_fix_clinical_notes_encounter_id.sql | \
  docker exec -i intellicare-postgres psql \
    -U intellicare_staging intellicare_staging
```

**Verificação:**
```bash
docker exec intellicare-postgres psql \
  -U intellicare_staging intellicare_staging \
  -c "SELECT column_name, data_type \
      FROM information_schema.columns \
      WHERE table_schema='tenant_clinica_alfa' \
        AND table_name='clinical_notes' \
        AND column_name='encounter_id';"
```
Esperado: `encounter_id | uuid`

---

## PASSO 9 — Migration 024: pessoa_id em professionals

```bash
sed 's/{schema}/tenant_clinica_alfa/g' \
  db/tenant_migrations/024_professionals_pessoa_id.sql | \
  docker exec -i intellicare-postgres psql \
    -U intellicare_staging intellicare_staging
```

**Verificação:**
```bash
docker exec intellicare-postgres psql \
  -U intellicare_staging intellicare_staging \
  -c "SELECT column_name, data_type \
      FROM information_schema.columns \
      WHERE table_schema='tenant_clinica_alfa' \
        AND table_name='professionals' \
        AND column_name='pessoa_id';"
```

---

## PASSO 10 — Verificação global pós-aplicação

```bash
docker exec intellicare-postgres psql \
  -U intellicare_staging intellicare_staging << 'EOF'
-- Platform checks
SELECT 'prompt_templates' AS objeto, COUNT(*) AS count FROM public.prompt_templates WHERE is_active = true
UNION ALL
SELECT 'platform.pessoa', COUNT(*) FROM platform.pessoa
UNION ALL
SELECT 'tenant professionals', COUNT(*) FROM tenant_clinica_alfa.professionals
UNION ALL
SELECT 'tenant professional_certificates', COUNT(*) FROM tenant_clinica_alfa.professional_certificates;

-- Colunas adicionadas
SELECT table_name, column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'tenant_clinica_alfa'
  AND column_name IN ('pessoa_id', 'interaction_warnings_count', 'encounter_id')
ORDER BY table_name, column_name;
EOF
```

---

## PASSO 11 — Reiniciar serviço (se necessário)

Se o serviço principal cacheia schema ao startup:

```bash
docker compose --env-file infra/.env.staging -f infra/docker-compose.yml \
  restart intellicare-service
```

Aguardar ~15s e verificar health:
```bash
curl https://api.intellicare.ia.br/health
```

---

## Critérios de aceite

- [ ] `public.prompt_templates` — 4 templates com `is_active = true`
- [ ] `platform.pessoa` — tabela existe (sem erro)
- [ ] `tenant_clinica_alfa.professionals` — tabela existe
- [ ] `tenant_clinica_alfa.professional_certificates` — tabela existe
- [ ] `prescriptions.interaction_warnings_count` — coluna INTEGER presente
- [ ] `patients.pessoa_id` — coluna UUID presente
- [ ] `clinical_notes.encounter_id` — tipo UUID (não BIGINT)
- [ ] `professionals.pessoa_id` — coluna UUID presente
- [ ] `curl https://api.intellicare.ia.br/health` → `{"status": "ok"}`
- [ ] Plano de Validação seção 1.2/1.3 re-executado com todos os itens ✅
