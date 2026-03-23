---
tipo: finalizacao
demanda: DEM-073
titulo: Prompt Versioning
status: concluida
commit: 60f2619
dev: CODEX
data-entrega: 2026-03-22
---

# DEM-073 — Finalização

## Commit

```
60f2619  feat(prompt-versioning): admin CRUD, cache, fallback e seeds idempotentes
```

---

## O que foi entregue

| Arquivo | O que foi construído |
|---------|---------------------|
| `db/platform_migrations/017_prompt_templates.sql` | Tabela `platform.prompt_templates`, índice de ativo, seeds idempotentes (`ON CONFLICT DO NOTHING`) para 4 slugs |
| `tools/scripts/seed_demo.py` | Apply da migration 017 incorporado ao runner SQL do projeto |
| `modules/shared/llm.py` | `get_active_prompt(slug, fallback)` — leitura do banco com cache em memória + `invalidate_prompt_cache(slug)` |
| `modules/florence/services.py` | Prompts renomeados para `*_FALLBACK`, chamadas migradas para `get_active_prompt()` |
| `modules/oswaldo/services.py` | Prompts renomeados para `*_FALLBACK`, chamadas migradas para `get_active_prompt()` |
| `modules/admin/schemas.py` | `PromptTemplateOut`, `PromptVersionOut`, `PromptUpdateIn` |
| `modules/admin/service.py` | `list_prompts()`, `get_prompt_versions()`, `save_new_version()`, `activate_version()` com invalidação de cache |
| `modules/admin/router.py` | 4 endpoints: GET list, GET versions, POST new version, POST activate |
| `frontend/AdminUI/src/hooks/usePrompts.ts` | Hook react-query para operações de prompt |
| `frontend/AdminUI/src/pages/PromptsPage.tsx` | Página "Prompts IA" — lista slugs, editor monospace, histórico, ativar/rollback |
| `frontend/AdminUI/src/App.tsx` | Rota `/admin/prompts` registrada |
| `packages/intellicare-core/tests/test_prompt_versioning.py` | 24 testes — todos passando |

---

## Cobertura de testes

```bash
pytest test_prompt_versioning.py test_florence_ia.py test_oswaldo_ia.py test_tenant_service.py -q
# 24 passed
```

Inclui testes de: seed idempotente, leitura com fallback, leitura do banco, ativação, rollback, invalidação de cache, regressão Florence IA, regressão Oswaldo IA.

---

## Slugs gerenciados (seeds migration 017)

| Slug | Módulo | Versão inicial |
|------|--------|---------------|
| `florence_soap` | Florence | v1 — prompt migrado do código |
| `florence_free_text` | Florence | v1 — prompt migrado do código |
| `oswaldo_prescription` | Oswaldo | v1 — prompt migrado do código |
| `oswaldo_cid10` | Oswaldo | v1 — prompt migrado do código |

---

## Mecanismo de apply da migration 017

> ⚠️ **Informação crítica para DEM-074**

A migration 017 **não entra automaticamente no startup do container**. O mecanismo real é o runner SQL em `tools/scripts/seed_demo.py`, executado manualmente.

Para staging/produção, o comando direto é:

```bash
psql -U <user> -d <db> -f db/platform_migrations/017_prompt_templates.sql
```

---

## Limitação conhecida

O build do AdminUI (`PromptsPage.tsx`) **não foi validado** via `tsc` neste worktree — ambiente sem `node_modules`. A validação TypeScript é **gate obrigatório no smoke manual do DEM-074** (ver `02_TECNICA.md` §4 — Smoke AdminUI).

---

## Impacto arquitetural

Esta DEM completa o **Bloco 0 do Módulo Marie (ADR-002)**. Com `get_active_prompt()` estável em `shared/llm.py`, a migração futura para Dify será transparente nos `services.py` — apenas a implementação interna da função mudará, o contrato de chamada permanece idêntico.
