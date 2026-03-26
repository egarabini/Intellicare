# DEM-093 — Diário de Execução

## 2026-03-25 — Diagnóstico (ARQUITETO)

Durante execução do `PLANO_VALIDACAO_STAGING_2026_03_25.md`, seções 1.2 e 1.3:

**Encontrado:**
- `public.*` — apenas `tenants` existe; `prompt_templates` ausente
- `tenant_clinica_alfa.professionals` — tabela não existe
- `tenant_clinica_alfa.patients` — existe, mas sem coluna `pessoa_id`
- `tenant_clinica_alfa.prescriptions` — existe, mas sem coluna `interaction_warnings_count`
- `tenant_clinica_alfa.clinical_notes` — existe
- `tenant_clinica_alfa.push_subscriptions` — existe
- `tenant_clinica_alfa.encounters` — existe (sem coluna `clinical_notes_id`, que **não deveria existir** — item do plano era incorreto)

**Diagnóstico:** migrations 005, 006, 017, 019, 020, 022, 023, 024 nunca foram aplicadas ao banco staging. O banco foi provisionado com o schema base e não recebeu as evoluções das sprints subsequentes.

**Ação:** DEM-093 criada para documentar e executar todas as migrations pendentes.

---

## Execução — a preencher por Eduardo

| Passo | Data | Executor | Resultado |
|-------|------|----------|-----------|
| PASSO 0 — Verificação estado atual | 2026-03-26 | CODEX | `platform.pessoa` ausente; `public.prompt_templates` ausente; `tenant_clinica_alfa.professionals` ausente; tenant sem colunas `patients.pessoa_id` e `prescriptions.interaction_warnings_count`. |
| PASSO 1 — Migration 017 prompt_templates | 2026-03-26 | CODEX | Aplicada com sucesso. Verificação real precisou usar `prompt_key` em vez de `name`; 4 seeds ativos: `florence_soap`, `florence_free_text`, `oswaldo_cid10`, `oswaldo_prescription`. |
| PASSO 2 — Migration 021 platform/pessoa | 2026-03-26 | CODEX | Arquivo `021_pessoa_identity.sql` falhou inicialmente porque o schema `platform` não era criado pelo SQL versionado. Executado `CREATE SCHEMA IF NOT EXISTS platform;` no VPS e reaplicada a migration com sucesso. Tabelas `platform.pessoa*` criadas. |
| PASSO 3 — Migration 005 gestao_completa | 2026-03-26 | CODEX | Aplicada com `SET search_path TO tenant_clinica_alfa;`. `tenant_clinica_alfa.professionals` criada e retornando `COUNT(*) = 0`. |
| PASSO 4 — Migration 006 clinico_gestao | 2026-03-26 | CODEX | Aplicada com `SET search_path TO tenant_clinica_alfa;`. `tenant_clinica_alfa.professional_groups` criada. |
| PASSO 5 — Migration 019 professional_certificates | 2026-03-26 | CODEX | Aplicada com `SET search_path TO tenant_clinica_alfa;`. `tenant_clinica_alfa.professional_certificates` criada e retornando `COUNT(*) = 0`. |
| PASSO 6 — Migration 020 interaction_count | 2026-03-26 | CODEX | Aplicada com `sed` do `{schema}`. Coluna `prescriptions.interaction_warnings_count INTEGER DEFAULT 0` confirmada. |
| PASSO 7 — Migration 022 paciente pessoa_id | 2026-03-26 | CODEX | Aplicada com `sed` do `{schema}`. Coluna `patients.pessoa_id UUID` confirmada. |
| PASSO 8 — Migration 023 clinical_notes UUID | 2026-03-26 | CODEX | Precheck retornou `COUNT(*) = 0` para `clinical_notes.encounter_id IS NOT NULL`, então não houve necessidade de backup. A migration deixou `clinical_notes.encounter_id` como `uuid`, mas o SQL emitiu erro residual `to_hex(uuid)` ao reencontrar estado já parcialmente migrado. Estado final verificado como correto. |
| PASSO 9 — Migration 024 professionals pessoa_id | 2026-03-26 | CODEX | Aplicada com `sed` do `{schema}`. Coluna `professionals.pessoa_id UUID` confirmada. |
| PASSO 10 — Verificação global | 2026-03-26 | CODEX | Revalidado ao final: `platform.pessoa*` presente; `public.prompt_templates` com 4 linhas ativas; `professionals` e `professional_certificates` presentes; colunas `patients.pessoa_id`, `prescriptions.interaction_warnings_count`, `clinical_notes.encounter_id`, `professionals.pessoa_id` presentes com tipos esperados. |
| PASSO 11 — Restart serviço (se necessário) | 2026-03-26 | CODEX | `docker compose --env-file infra/.env.staging -f infra/docker-compose.yml restart intellicare-service` executado no VPS. Health final: `{\"status\":\"healthy\",\"service\":\"intellicare-service\"}`. |

## Divergências encontradas entre plano/spec e código real

- `db/platform_migrations/021_pessoa_identity.sql` **não** contém `CREATE SCHEMA IF NOT EXISTS platform`, apesar de `02_TECNICA.md` afirmar isso. O schema precisou ser criado manualmente no VPS antes de reaplicar a migration.
- A verificação do PASSO 1 no `03_PLANO.md` usa coluna `name`, mas o schema real de `public.prompt_templates` usa `prompt_key`.
- O item `platform.keycloak_user_mapping` citado no plano de validação geral **não** foi criado por estas migrations e permanece ausente após a sincronização do banco.
