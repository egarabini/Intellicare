---
tipo: finalizacao
demanda: DEM-079
titulo: Florence via Marie RAG
status: concluida
dev: CODEX
commit: 868cf09
data: 2026-03-23
---

# DEM-079 — Finalização

## Commit

```
feat(florence): SOAP contextualizado via Marie RAG — workflow florence_soap_rag, timeline context, fallback intacto
```

Hash: `868cf09` | Push: `git push origin HEAD:main` ✅ confirmado

---

## Arquivos entregues

| Arquivo | Tipo | Descrição |
|---------|------|-----------|
| `modules/florence/services.py` | Modificado | `suggest_soap()` integra `call_marie("florence_soap_rag", ...)` antes do fallback local |
| `modules/shared/timeline_context.py` | **Novo** | `_get_florence_timeline_context()` — formata histórico clínico para payload RAG (max 3000 chars) |
| `packages/intellicare-core/tests/test_florence_marie.py` | **Novo** | 14 testes cobrindo Marie ativo, fallback, timeline vazia, resposta malformada |

---

## Resultado dos testes

```
14 passed — test_florence_marie.py
Suíte existente Florence: zero regressões
```

---

## Incidentes resolvidos

### Conflito em `services.py`
`modules/florence/services.py` tinha divergência entre branch de entrega e `main` (base DEM-073 prompt versioning). Resolução: Marie entra **primeiro** quando `MARIE_ENABLED=true`; fallback prompt versioning (get_active_prompt + regra local) permanece intacto caso Marie falhe ou retorne resposta inválida.

### Import `_get_florence_timeline_context`
Para evitar import circular `florence ↔ cuidado`, a função foi criada diretamente em `modules/shared/timeline_context.py` — não em `cuidado/services.py`. Solução proativa sem necessidade de intervenção do ARQUITETO.

### Parsing resposta Dify
LLM pode retornar JSON embrulhado em texto. `_parse_marie_soap_response()` usa `re.search(r'\{.*\}', response, re.DOTALL)` para extração robusta — falha silenciosa aciona fallback local.

---

## Estado resultante

| Item | Estado |
|------|--------|
| `suggest_soap()` usa Marie quando `MARIE_ENABLED=true` | ✅ |
| `_get_florence_timeline_context()` em `shared/` | ✅ |
| Workflow `florence_soap_rag` documentado (criar no Dify em DEM-082) | ✅ |
| `MARIE_ENABLED=false` → comportamento idêntico ao sprint anterior | ✅ |
| 14 testes novos passando | ✅ |
| Zero regressões na suíte Florence existente | ✅ |

---

## Pré-condição para DEM-082

O workflow `florence_soap_rag` ainda precisa ser **criado e publicado no Dify** em staging. Isso faz parte do Bloco 2 do plano DEM-082 (passo 5). O código da API já está pronto — apenas o workflow no Dify web está pendente.
