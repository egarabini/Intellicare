---
tipo: finalizacao
demanda: DEM-075
titulo: Marie Bootstrap
status: concluida
commit: 6ed6281
dev: CODEX
data-entrega: 2026-03-22
---

# DEM-075 — Finalização

## Commit

```
6ed6281  feat(marie): bootstrap Dify stack, marie_client.py, MARIE_ENABLED flag, cid10_rag proof-of-concept
```

---

## O que foi entregue

| Arquivo | O que foi construído |
|---------|---------------------|
| `infra/docker-compose.yml` | Stack Marie/Dify — `marie-db`, `marie-redis`, `marie-api`, `marie-worker`, `marie-web` |
| `modules/shared/settings.py` | Variáveis `marie_enabled`, `marie_api_url`, `marie_api_key`, `marie_timeout_seconds` |
| `infra/.env.example` + `.env.staging.example` | Variáveis Marie documentadas com valores placeholder |
| `modules/marie/client.py` | `call_marie()`, `is_marie_enabled()` — fallback automático em timeout/5xx |
| `modules/oswaldo/services.py` | `suggest()` integrado com Marie quando `MARIE_ENABLED=true` e `patient_id` válido como UUID |
| `packages/intellicare-core/tests/test_marie_client.py` | Testes com mock Dify |

**16 testes passando** — `test_marie_client.py` + `test_oswaldo_ia.py` + `test_prompt_versioning.py`

---

## Adaptações ao spec (estrutura real do repo)

| Spec | Real |
|------|------|
| `suggest_cid10()` separada | Integrado no `suggest()` existente |
| `get_settings()` genérico | `get_settings()` de `intellicare_core.config.settings` |
| Chamada quando `patient_id` presente | Só chama Marie quando `patient_id` consegue virar UUID válido |
| Resumo timeline como contexto | `clinical_timeline()` retorna contexto para payload RAG |

---

## Validação pré-commit

`docker compose config --quiet` executado com `.env` temporário (removido antes do commit):
- Exit code 0 ✅
- Warnings de variáveis não preenchidas fora do escopo Marie — não bloqueante
- Sem erro de YAML nem referência inválida no stack Marie

> A validação de containers **realmente subindo** (Dify boot completo) ocorre no DEM-078 Staging Sync.

---

## Limitação conhecida — setup Dify manual no staging

O workflow `cid10_rag` no Dify requer setup manual na interface web após o primeiro `docker compose up`. Documentado no `03_PLANO.md` e no checklist do DEM-078. O `MARIE_ENABLED` permanece `false` por default até o workflow estar configurado e testado.

---

## Impacto arquitetural

Marie está operacional como **feature flag desligada**. O `call_marie()` com `fallback_fn` garante que nenhum comportamento existente é afetado. A ativação é cirúrgica: basta `MARIE_ENABLED=true` + `MARIE_API_KEY` configurada após setup do Dify no staging.
