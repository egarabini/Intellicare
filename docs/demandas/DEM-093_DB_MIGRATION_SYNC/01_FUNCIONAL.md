# DEM-093 — Sincronização de Migrations no Banco Staging

## Contexto

Durante a execução do Plano de Validação Staging (2026-03-25), a inspeção manual do banco `intellicare_staging` revelou que diversas migrations acumuladas desde o início do projeto nunca foram aplicadas ao ambiente de staging.

O ambiente de staging foi provisionado com apenas o schema base (migrations iniciais), e as evoluções subsequentes ao schema `public`, schema `platform` e schemas tenant não foram executadas manualmente após cada sprint.

## Problema identificado

### Schema `public` — tabelas de plataforma

| Tabela esperada | Status |
|----------------|--------|
| `public.tenants` | ✅ Existe |
| `public.prompt_templates` | ❌ Ausente — migration 017 não aplicada |

### Schema `platform` — identidade centralizada (ADR-004)

| Tabela esperada | Status |
|----------------|--------|
| `platform.pessoa` | ⚠️ A verificar (endpoints identity respondem 200, mas tabelas não inspecionadas) |
| `platform.pessoa_fisica` | ⚠️ A verificar |
| `platform.keycloak_user_mapping` | ⚠️ A verificar |

### Schema `tenant_clinica_alfa` — tabelas clínicas

| Tabela/Coluna esperada | Status |
|-----------------------|--------|
| `professionals` | ❌ Ausente — migrations 005/006 não aplicadas |
| `patients.pessoa_id` | ❌ Ausente — migration 022 não aplicada |
| `prescriptions.interaction_warnings_count` | ❌ Ausente — migration 020 não aplicada |
| `clinical_notes` (encounter_id como UUID) | ⚠️ Existe mas encounter_id pode ainda ser BIGINT — migration 023 não aplicada |
| `professional_certificates` | ❌ Ausente — migration 019 não aplicada |

## Impacto

- **ClinicoUI**: módulo de profissionais e agendas não funciona (tabela `professionals` ausente)
- **Receituário Oswaldo**: contador de interações não persiste (coluna ausente)
- **Identidade centralizada**: vínculo paciente ↔ pessoa não funciona (coluna `pessoa_id` ausente)
- **Plano de Validação 110 itens**: 12+ itens bloqueados por gaps de schema

## Entregável

Script SQL de aplicação controlada de todas as migrations pendentes, com rollback seguro, executado no VPS staging via `docker exec`.
