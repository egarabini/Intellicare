# DEM-061 — Oswaldo IA — Finalização

## Status: ✅ CONCLUÍDA

- **Commit:** `9d14751` (`9d14751e27cd87dcbf23aebf7a43b9eb49099f783`)
- **Entregador:** DEV-2
- **Data:** 2026-04-11

---

## O que foi entregue

| Camada | Mudança |
|---|---|
| **Contracts** | `OswaldoSuggestRequest` + `OswaldoSuggestion` em `modules/oswaldo/contracts.py` |
| **Services** | `suggest()` → `_call_llm()` via `modules/shared/llm` (sem duplicação com Florence) + `_rule_based_suggestion()` |
| **Routes** | `POST /oswaldo/suggest` — role `CLINICO` obrigatório |
| **Frontend** | Botão "Sugerir CID-10 e prescrição com IA" + campo motivo + badge `confidence: low` em `OswaldoPrescriptionEditor` |

## Decisão arquitetural — `shared/llm`

DEV-2 extraiu `_call_llm()` para `modules/shared/llm.py` em vez de duplicar de Florence.
Decisão correta — Florence e Oswaldo compartilham o mesmo wrapper OpenAI-compatible.
Se o LLM precisar ser trocado, um único ponto de mudança.

## Testes — 5 (acima do mínimo de 2)

| Teste | Cobertura |
|---|---|
| HTTP 422 | `chief_complaint` ausente — validação Pydantic |
| HTTP 403 | Role não-CLINICO bloqueado |
| Rule-based fallback | Sem `FLORENCE_LLM_URL` — retorna `model: rule-based` |
| Conteúdo do fallback | `cid10_code` presente na resposta |
| LLM mock | Simula chamada com resposta válida |

---

## Critérios de aceite — verificação final

- [x] `POST /oswaldo/suggest` retorna `OswaldoSuggestion` com CID-10 + itens
- [x] Fallback rule-based funciona sem LLM configurado
- [x] Botão "Sugerir com IA" no `OswaldoPrescriptionEditor`
- [x] CID-10 e itens preenchidos são editáveis antes de salvar
- [x] Badge `confidence: low` quando fallback
- [x] 5 testes passando
- [x] `shared/llm` sem duplicação com Florence
