---
tipo: tecnica
demanda: DEM-085
titulo: Saneamento Técnico
status: planejada
dev: DEV-1
sprint: 2026-05-16
criado: 2026-03-23
---

# DEM-085 — Técnica: Saneamento Técnico

## Item 1 — Auditoria Git (CODEX executa, DEV-1 documenta resultado)

### Comandos de diagnóstico

```bash
# No repositório local do CODEX:

# 1. Listar todos os commits locais não em origin
git fetch origin
git log origin/main..HEAD --oneline --no-merges

# 2. Ver detalhes de cada commit
git log origin/main..HEAD --format="%H %ai %s" --no-merges

# 3. Verificar se algum hash coincide com origin (mesmo conteúdo, hash diferente)
git log origin/main..HEAD --oneline | while read hash msg; do
  git show $hash --stat | head -3
done

# 4. Ver estado de arquivos não commitados
git status
git diff --stat HEAD
```

### Diretório `estudos/`

```bash
# Verificar conteúdo
ls -la estudos/
# Verificar se está no .gitignore
cat .gitignore | grep estudos
```

Se `estudos/` contém material de pesquisa pessoal (não código do produto), adicionar ao `.gitignore`. Se contém código relevante, mover para `docs/estudos/` e documentar como referência.

### Documento de auditoria

Criar `docs/saneamento/AUDITORIA_GIT_2026_05_16.md`:

```markdown
# Auditoria Git — 2026-05-16

## Commits em origin/main..HEAD

| Hash | Data | Mensagem | DEM | Decisão |
|------|------|----------|-----|---------|
| xxxx | ... | ... | DEM-0XX ou N/A | cherry-pick / descartar / nova DEM |

## Diretório estudos/
[conteúdo e decisão]

## Edições em _dashboard.md
[diferença vs origin/main e decisão]

## Estado final
origin/main..HEAD: [vazio / N commits restantes justificados]
```

---

## Item 2 — Redis auth CarePlanner

### Diagnóstico

```bash
# Verificar qual REDIS_PASSWORD o dispatcher usa
grep -r "REDIS" infra/docker-compose.yml
grep -r "REDIS_PASSWORD" modules/careplanner/ --include="*.py"

# Verificar se há conflito de senhas entre Marie Redis e CarePlanner Redis
docker compose exec careplanner-worker env | grep REDIS
docker compose exec marie-worker env | grep REDIS
```

### Fix esperado

O CarePlanner provavelmente usa `redis://:{REDIS_PASSWORD}@redis:6379/0` e o `REDIS_PASSWORD` no `.env.staging` pode ter sido sobrescrito pelo `MARIE_REDIS_PASSWORD` ou vice-versa.

```bash
# Em .env.staging, garantir que existam variáveis distintas:
REDIS_PASSWORD=<senha do Redis CarePlanner>
MARIE_REDIS_PASSWORD=marie_redis_dev_2026

# Em docker-compose.yml, marie-worker deve usar MARIE_REDIS_PASSWORD explicitamente
# CarePlanner deve usar REDIS_PASSWORD
```

### Smoke

```bash
docker compose restart careplanner-worker
sleep 5
docker compose logs careplanner-worker --tail=30 | grep -i "redis\|error\|connect"
# Esperado: nenhuma linha com "invalid username-password pair"
```

---

## Item 3 — `clinical_notes` FK type mismatch

### Diagnóstico

```bash
# Verificar tipo atual da coluna
psql ... -c "\d demo.clinical_notes"
# Verificar tipo da PK de encounters
psql ... -c "\d demo.encounters"
```

### Migration corretiva `023_fix_clinical_notes_encounter_id.sql`

```sql
-- db/tenant_migrations/023_fix_clinical_notes_encounter_id.sql
-- Converte encounter_id de BIGINT para UUID em clinical_notes

DO $$
BEGIN
    -- Verificar se a coluna ainda é BIGINT (pode já ter sido corrigida em alguns schemas)
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = '{schema}'
          AND table_name = 'clinical_notes'
          AND column_name = 'encounter_id'
          AND data_type = 'bigint'
    ) THEN
        -- Adicionar coluna UUID temporária
        ALTER TABLE {schema}.clinical_notes
            ADD COLUMN IF NOT EXISTS encounter_id_uuid UUID;

        -- Não há dados para migrar (coluna FK nunca teve FK física)
        -- Remover coluna BIGINT e renomear UUID
        ALTER TABLE {schema}.clinical_notes DROP COLUMN encounter_id;
        ALTER TABLE {schema}.clinical_notes RENAME COLUMN encounter_id_uuid TO encounter_id;
    END IF;
END $$;

-- Adicionar índice
CREATE INDEX IF NOT EXISTS idx_clinical_notes_encounter_id
    ON {schema}.clinical_notes(encounter_id)
    WHERE encounter_id IS NOT NULL;
```

**Atenção:** se `clinical_notes.encounter_id` tiver dados (BIGINTs reais), a migração acima descarta esses dados. Verificar antes:
```sql
SELECT COUNT(*) FROM demo.clinical_notes WHERE encounter_id IS NOT NULL;
```
Se > 0: fazer cast `encounter_id::text::uuid` apenas se os valores forem UUIDs armazenados como BIGINT (improvável). Caso contrário, NULL-ificar e documentar a perda.

---

## Item 4 — `test_patient_response` fix

### Diagnóstico

```bash
pytest tests/ -k "test_patient_response" -v 2>&1 | tail -30
```

A falha é por field rename — identificar qual campo foi renomeado no schema `PatientOut` e não foi atualizado no test assertion. Fix direto no arquivo de test.

```python
# Padrão esperado de fix:
# Antes: assert response.json()["old_field_name"] == "value"
# Depois: assert response.json()["new_field_name"] == "value"
```

---

## Gotcha — Item 3 pode não ter dados para migrar

Se `clinical_notes` foi criada mas nunca usada em staging (nenhum encontro tem notas Florence), a coluna está NULL em todos os registros. Nesse caso a migration é segura sem análise adicional.

---

## Gotcha — Item 1 pode revelar work não registrado

Se a auditoria git encontrar commits com código funcional não em `origin/main`, esses commits precisam ser avaliados pelo ARQUITETO antes de qualquer cherry-pick. Não fazer push de commits não auditados sem aprovação.
