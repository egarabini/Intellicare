# DEM-093 — Especificação Técnica

## Arquitetura de Migrations

O IntelliCare V3 utiliza três categorias de migration:

| Categoria | Diretório | Schema alvo | Estratégia de execução |
|-----------|-----------|-------------|----------------------|
| Platform | `db/platform_migrations/` | `public.*` e `platform.*` | Executar diretamente — já contém prefixo de schema |
| Tenant (legado) | `db/tenant_migrations/` (baixas numerações) | Schema do tenant | **Sem** `{schema}` placeholder — requer `SET search_path` |
| Tenant (moderno) | `db/tenant_migrations/` (numerações altas) | Schema do tenant | **Com** `{schema}` placeholder — requer `sed` substituição |

## Migrations pendentes — análise detalhada

### `db/platform_migrations/017_prompt_templates.sql`

**Schema alvo:** `public`
**Cria:** `public.prompt_templates` com colunas `id, name, version, content, is_active, created_at, updated_at`
**Inclui seeds:** florence_soap, florence_free_text, oswaldo_cid10, oswaldo_prescription
**Dependências:** nenhuma
**Comando de execução:**
```bash
docker exec -i intellicare-postgres psql \
  -U intellicare_staging intellicare_staging \
  < db/platform_migrations/017_prompt_templates.sql
```

---

### `db/platform_migrations/021_pessoa_identity.sql`

**Schema alvo:** `platform`
**Cria:** `platform.pessoa`, `platform.pessoa_fisica`, `platform.pessoa_juridica`, `platform.pessoa_contato`, `platform.pessoa_estabelecimento`
**Inclui:** `CREATE SCHEMA IF NOT EXISTS platform` *(corrigido em 2026-03-26 — versão original não continha; CODEX adicionou após falha no VPS)*
**Dependências:** nenhuma
**Observação:** Se endpoints `/identity/*` já funcionam no staging, este migration pode já estar aplicado. Verificar com `\dt platform.*` antes de executar.
**Comando de execução:**
```bash
docker exec -i intellicare-postgres psql \
  -U intellicare_staging intellicare_staging \
  < db/platform_migrations/021_pessoa_identity.sql
```

---

### `db/tenant_migrations/005_gestao_completa.sql`

**Schema alvo:** `tenant_clinica_alfa` (e demais tenants ativos)
**Cria:** `professionals`, `units`, `unit_professionals`, `tenant_users`
**Tipo:** SEM placeholder `{schema}` — requer `SET search_path`
**Dependências:** nenhuma (é migration fundacional do tenant)
**Comando de execução:**
```bash
docker exec -i intellicare-postgres psql \
  -U intellicare_staging intellicare_staging \
  -c "SET search_path TO tenant_clinica_alfa; \
      $(cat db/tenant_migrations/005_gestao_completa.sql)"
```
Ou via heredoc (recomendado para evitar problemas de quoting):
```bash
(echo "SET search_path TO tenant_clinica_alfa;"; \
 cat db/tenant_migrations/005_gestao_completa.sql) | \
 docker exec -i intellicare-postgres psql \
   -U intellicare_staging intellicare_staging
```

---

### `db/tenant_migrations/006_clinico_gestao.sql`

**Schema alvo:** `tenant_clinica_alfa` (e demais tenants ativos)
**Cria/altera:** `professional_groups`, `group_members`, extensões em `professionals`
**Tipo:** SEM placeholder `{schema}` — requer `SET search_path`
**Dependências:** `005_gestao_completa.sql` (tabela `professionals`)
**Comando de execução:**
```bash
(echo "SET search_path TO tenant_clinica_alfa;"; \
 cat db/tenant_migrations/006_clinico_gestao.sql) | \
 docker exec -i intellicare-postgres psql \
   -U intellicare_staging intellicare_staging
```

---

### `db/platform_migrations/019_professional_certificates.sql`

**Schema alvo:** `tenant_clinica_alfa` (e demais tenants ativos)
**Cria:** `professional_certificates`
**Tipo:** SEM placeholder `{schema}` — requer `SET search_path`
**Dependências:** `professionals` (criada em 005)
**Observação:** Arquivo está em `platform_migrations/` mas cria tabela de tenant sem prefixo de schema — requer SET search_path igual às migrations tenant legadas.
**Comando de execução:**
```bash
(echo "SET search_path TO tenant_clinica_alfa;"; \
 cat db/platform_migrations/019_professional_certificates.sql) | \
 docker exec -i intellicare-postgres psql \
   -U intellicare_staging intellicare_staging
```

---

### `db/tenant_migrations/020_prescription_interaction_count.sql`

**Schema alvo:** `tenant_clinica_alfa`
**Altera:** `{schema}.prescriptions` — adiciona `interaction_warnings_count INTEGER NOT NULL DEFAULT 0`
**Tipo:** COM placeholder `{schema}` — requer `sed`
**Dependências:** tabela `prescriptions` (já existe no staging)
**Comando de execução:**
```bash
sed 's/{schema}/tenant_clinica_alfa/g' \
  db/tenant_migrations/020_prescription_interaction_count.sql | \
  docker exec -i intellicare-postgres psql \
    -U intellicare_staging intellicare_staging
```

---

### `db/tenant_migrations/022_paciente_pessoa_id.sql`

**Schema alvo:** `tenant_clinica_alfa`
**Altera:** `{schema}.patients` — adiciona `pessoa_id UUID`, cria índice parcial `idx_patients_pessoa_id`
**Tipo:** COM placeholder `{schema}` — requer `sed`
**Dependências:** tabela `patients` (já existe)
**Comando de execução:**
```bash
sed 's/{schema}/tenant_clinica_alfa/g' \
  db/tenant_migrations/022_paciente_pessoa_id.sql | \
  docker exec -i intellicare-postgres psql \
    -U intellicare_staging intellicare_staging
```

---

### `db/tenant_migrations/023_fix_clinical_notes_encounter_id.sql`

**Schema alvo:** `tenant_clinica_alfa`
**Altera:** `{schema}.clinical_notes` — converte `encounter_id` de BIGINT para UUID
**Tipo:** COM placeholder `{schema}` — requer `sed`
**Dependências:** tabela `clinical_notes` (já existe)
**⚠️ ATENÇÃO — migration destrutiva:**
- Adiciona coluna `encounter_id_new UUID`
- Dropa a coluna antiga `encounter_id BIGINT`
- Renomeia `encounter_id_new` para `encounter_id`
- Adiciona FK `NOT VALID` para `encounters.id`
- **Todos os valores existentes de `encounter_id` são perdidos (sem conversão possível)**
- Se `clinical_notes` já tiver dados, verificar impacto antes de executar
**Comando de execução:**
```bash
sed 's/{schema}/tenant_clinica_alfa/g' \
  db/tenant_migrations/023_fix_clinical_notes_encounter_id.sql | \
  docker exec -i intellicare-postgres psql \
    -U intellicare_staging intellicare_staging
```

---

### `db/tenant_migrations/024_professionals_pessoa_id.sql`

**Schema alvo:** `tenant_clinica_alfa`
**Altera:** `{schema}.professionals` — adiciona `pessoa_id UUID`, cria índice parcial `idx_professionals_pessoa_id`
**Tipo:** COM placeholder `{schema}` — requer `sed`
**Dependências:** tabela `professionals` (criada em 005 — **aplicar 005 antes**)
**Comando de execução:**
```bash
sed 's/{schema}/tenant_clinica_alfa/g' \
  db/tenant_migrations/024_professionals_pessoa_id.sql | \
  docker exec -i intellicare-postgres psql \
    -U intellicare_staging intellicare_staging
```

---

## Ordem de aplicação obrigatória

```
017 (platform) → 021 (platform, se ausente)
→ 005 (tenant) → 006 (tenant) → 019 (tenant/platform)
→ 020 (tenant) → 022 (tenant) → 023 (tenant) → 024 (tenant)
```

## Verificação pós-aplicação

```sql
-- Schema public
SELECT COUNT(*) FROM public.prompt_templates;

-- Schema platform
SELECT COUNT(*) FROM platform.pessoa;

-- Schema tenant
SET search_path TO tenant_clinica_alfa;
SELECT COUNT(*) FROM professionals;
SELECT column_name FROM information_schema.columns
  WHERE table_schema = 'tenant_clinica_alfa'
    AND table_name IN ('patients','prescriptions','professionals')
    AND column_name IN ('pessoa_id','interaction_warnings_count')
  ORDER BY table_name, column_name;
```

## Notas de segurança

- Todas as migrations usam `CREATE TABLE IF NOT EXISTS` e `ADD COLUMN IF NOT EXISTS` — são **idempotentes** (exceto migration 023 que é destrutiva)
- Executar em horário de baixo tráfego (staging tem carga mínima)
- Migration 023 deve ser executada com staging em manutenção se houver dados clínicos reais
