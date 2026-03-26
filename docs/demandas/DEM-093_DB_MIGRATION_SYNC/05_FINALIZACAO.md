# DEM-093 — Finalização

## Entrega

- **Commit:** (pendente — a preencher após execução no VPS)
- **Data:** 2026-03-26
- **Dev:** CODEX + Eduardo (handoff ARQUITETO) — execução no VPS staging

## Status

> ✅ **Migrations sincronizadas no VPS staging**

## Resultado objetivo

- `public.prompt_templates` criado e populado com 4 seeds ativos
- `platform.pessoa`, `platform.pessoa_fisica`, `platform.pessoa_juridica`, `platform.pessoa_contato`, `platform.pessoa_estabelecimento` criadas
- `tenant_clinica_alfa.professionals` e `tenant_clinica_alfa.professional_certificates` criadas
- `patients.pessoa_id`, `professionals.pessoa_id`, `prescriptions.interaction_warnings_count` presentes
- `clinical_notes.encounter_id` confirmado como `uuid`
- `intellicare-service` reiniciado com health final `{"status":"healthy","service":"intellicare-service"}`

## Divergências do real vs spec

- `021_pessoa_identity.sql` não cria o schema `platform`; foi necessário executar `CREATE SCHEMA IF NOT EXISTS platform;` manualmente no VPS antes de reaplicar a migration.
- O check do PASSO 1 no plano usa `name`, mas o schema real de `public.prompt_templates` usa `prompt_key`.
- A migration 023 deixou o estado final correto, mas emitiu erro residual `to_hex(uuid)` ao reencontrar `encounter_id` já em `uuid`.
- `platform.keycloak_user_mapping` continua ausente; este objeto não é criado pela `021` versionada e, por isso, o re-run formal completo das seções 1.2/1.3 do plano de validação continua pendente.

## Critérios de aceite — status final

- [x] `public.prompt_templates` — 4 templates com `is_active = true`
- [x] `platform.pessoa` — tabela existe
- [x] `tenant_clinica_alfa.professionals` — tabela existe
- [x] `tenant_clinica_alfa.professional_certificates` — tabela existe
- [x] `prescriptions.interaction_warnings_count` — coluna INTEGER presente
- [x] `patients.pessoa_id` — coluna UUID presente
- [x] `clinical_notes.encounter_id` — tipo UUID
- [x] `professionals.pessoa_id` — coluna UUID presente
- [x] `curl https://api.intellicare.ia.br/health` → serviço saudável
- [ ] Plano de Validação seções 1.2 e 1.3 re-executadas com todos os itens ✅

## Observações

Migrations sem `{schema}` placeholder (005, 006, 019) requerem `SET search_path` antes da execução.
Migrations com `{schema}` placeholder (020, 022, 023, 024) requerem `sed` substituição.
Migration 023 é destrutiva — converter `encounter_id` de BIGINT para UUID descarta valores existentes.
Ver `02_TECNICA.md` para detalhes completos de cada migration.
