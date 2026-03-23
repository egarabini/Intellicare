---
tipo: plano-execucao
demanda: DEM-077
titulo: Oswaldo — Interação Medicamentosa
status: em-execucao
dev: DEV-1
criado: 2026-03-22
---

# DEM-077 — Plano de Execução

## Estimativa

Tempo estimado: ~4h | Complexidade: média

O core lógico é simples (lookup em JSON + LLM fallback). O maior esforço é popular `drug_interactions.json` com pares relevantes e garantir que o matching por aliases funciona corretamente para nomes genéricos e comerciais.

---

## Ordem de execução

### Bloco 1 — Tabela de interações `drug_interactions.json` (60min)
1. Criar `data/drug_interactions.json` com ao menos **30 pares** para o sprint (os ~150 completos são roadmap):
   - Focar nos mais graves: anticoagulantes, IECA/poupadores K+, serotoninérgicos, digitálicos, nitratos/vasodilatadores
   - Para cada par: `drug_a`, `drug_b`, `aliases_a[]`, `aliases_b[]`, `severity`, `effect`, `recommendation`
2. Testar manualmente o matching com variações de escrita: "AAS", "aspirina", "ácido acetilsalicílico"

### Bloco 2 — `interactions.py` e schemas (45min)
3. Criar `modules/oswaldo/interactions.py` com `check_interactions()`, `_lookup_static()`, `_llm_fallback()`
4. Criar `InteractionWarning`, `CheckInteractionsRequest`, `CheckInteractionsResponse` em `schemas.py`
5. Testar isolado: `check_interactions(["varfarina", "AAS"])` → retorna 1 warning GRAVE

### Bloco 3 — Endpoint (20min)
6. Adicionar `POST /oswaldo/check-interactions` em `routes.py`
7. Proteger com role `CLINICO` (não expor ao paciente)
8. Smoke manual: `curl -X POST .../oswaldo/check-interactions -d '{"medications":["varfarina","AAS"]}'`

### Bloco 4 — Frontend (60min)
9. Criar `InteractionWarningBanner.tsx` com Alert Mantine, cores por severidade, botão "Entendido"
10. Em `OswaldoPrescriptionEditor.tsx`:
    - Extrair lista de nomes dos medicamentos do estado atual
    - Chamar `POST /oswaldo/check-interactions` com debounce 500ms
    - Renderizar `<InteractionWarningBanner>` se `warnings.length > 0`
11. Testar no browser: adicionar Varfarina + AAS → banner vermelho aparece

### Bloco 5 — Testes (45min)
12. Criar `test_oswaldo_interactions.py`:
    - `test_grave_interaction_detected` — varfarina + AAS → GRAVE
    - `test_moderate_interaction_detected` — IECA + espironolactona → MODERADO
    - `test_no_interaction` — atenolol + amoxicilina → lista vazia
    - `test_llm_fallback_called_when_not_in_static` — par desconhecido → LLM mockado chamado
    - `test_case_insensitive_matching` — "VARFARINA" == "varfarina" == "Warfarina"
13. `pytest test_oswaldo_interactions.py test_oswaldo_ia.py -v` — sem regressões

---

## Gotcha — aliases vs. DCB vs. nome comercial

O clínico pode digitar "Coumadin" (nome comercial) ou "warfarina" (grafia alternativa) ou "varfarina" (grafia DCB). O `aliases_a/b` deve cobrir as variações mais comuns. O `_normalize()` já remove acentos e converte para lowercase, mas as variações ortográficas precisam estar nos aliases.

---

## Gotcha — debounce no frontend é obrigatório

Sem debounce, cada keystroke no campo de medicamento dispara um POST. Com 3 medicamentos na prescrição, isso gera 3 chamadas por segundo enquanto o usuário digita. Implementar `useDebounce(medications, 500)` antes de chamar o endpoint.

---

## Gotcha — LLM fallback pode retornar falso positivo

O LLM às vezes inventa interações que não existem. A resposta do LLM deve ter `source: "llm"` explícito no banner, com texto adicional: *"Verificação por IA — confirmar com fontes clínicas."* Isso diferencia do checker estático (curado) e avisa o clínico sobre a confiabilidade.

---

## Entrega

```
feat(oswaldo): interação medicamentosa — checker estático + LLM fallback + InteractionWarningBanner
```
Hash → enviar ao ARQUITETO após `git push origin HEAD:main` confirmado.
