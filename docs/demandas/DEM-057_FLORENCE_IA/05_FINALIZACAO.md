# DEM-057 — Florence IA — Finalização

## Status: ✅ CONCLUÍDA

- **Commit:** `29df484`
- **Mensagem:** implícita no summary — `feat(florence): DEM-057 sugestão SOAP com IA`
- **Entregador:** DEV-2
- **Data:** 2026-04-04
- **Volume:** 6 arquivos, +338 linhas

---

## O que foi entregue

| Camada | Mudança |
|---|---|
| **Contracts** | `SuggestRequest` + `SOAPSuggestion` Pydantic models |
| **Services** | `suggest_soap()` → tenta `_call_llm()` (OpenAI-compatible), fallback para `_rule_based_suggestion()` |
| **Routes** | `POST /florence/notes/suggest` — role `CLINICO` obrigatório |
| **Frontend** | Botão "Sugerir SOAP com IA" + campo motivo da consulta + badge `confidence: low` quando rule-based |
| **Env** | `FLORENCE_LLM_URL`, `FLORENCE_LLM_API_KEY`, `FLORENCE_LLM_MODEL` — todos opcionais |

## Testes

5 testes passando — acima do critério mínimo de 2:
- Rule-based fallback (sem `FLORENCE_LLM_URL`)
- Validação de campo obrigatório (`chief_complaint`)
- Autorização de role (`CLINICO` only)
- Conteúdo do campo `soap_s` no fallback
- Mock de LLM configurado

## Design Hybrid confirmado

Nunca auto-salva. A IA preenche os campos SOAP no frontend; o clínico edita livremente
antes de clicar "Salvar nota". Classificação Hybrid do ADR-001 respeitada.

---

## Critérios de aceite — verificação final

- [x] `POST /florence/notes/suggest` retorna `SOAPSuggestion` com os 4 campos
- [x] Fallback rule-based funciona sem `FLORENCE_LLM_URL` configurada
- [x] Botão "Sugerir SOAP com IA" visível no `FlorenceNoteEditor` (modo SOAP)
- [x] Campos preenchidos pela IA editáveis antes de salvar
- [x] Badge `confidence: low` exibido no fallback
- [x] 5 testes passando
