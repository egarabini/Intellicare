---
tipo: plano-execucao
demanda: DEM-079
titulo: Florence via Marie RAG
status: em-execucao
dev: CODEX
criado: 2026-03-22
---

# DEM-079 — Plano de Execução

## Estimativa

Tempo estimado: ~3.5h | Complexidade: média

O padrão já está estabelecido pelo DEM-075 (`call_marie` + `fallback_fn`). O maior esforço é o helper `_get_florence_timeline_context()` e a criação do workflow `florence_soap_rag` no Dify.

---

## Ordem de execução

### Bloco 1 — Helper de contexto (45min)
1. Implementar `_get_florence_timeline_context(patient_id, ctx)` em `florence/services.py`
2. Importar `clinical_timeline()` do módulo `cuidado` — verificar se há acoplamento circular (se houver, usar chamada HTTP interna ou mover helper para `shared/`)
3. Testar isolado: `_get_florence_timeline_context()` com paciente de teste retorna string formatada

### Bloco 2 — Integração `suggest_soap()` (30min)
4. Importar `call_marie`, `is_marie_enabled` em `florence/services.py`
5. Modificar `suggest_soap()` conforme `02_TECNICA.md`
6. `pytest test_florence_ia.py -v` com `MARIE_ENABLED=false` — zero regressões

### Bloco 3 — Workflow Dify `florence_soap_rag` (45min)
7. No Dify web (staging), criar workflow `florence_soap_rag`
8. Configurar nós: Input → LLM → Output (ver `02_TECNICA.md` §Workflow)
9. Publicar → testar via curl direto no Dify antes de integrar com a API
10. Anotar o `workflow_id` gerado (pode ser necessário para future routing)

### Bloco 4 — Testes (45min)
11. Criar `test_florence_marie.py` com os 4 testes
12. `pytest test_florence_marie.py test_florence_ia.py -v` — todos passando

---

## Gotcha — acoplamento circular `florence` ↔ `cuidado`

`florence/services.py` importar `clinical_timeline()` de `cuidado/services.py` pode criar ciclo de importação se `cuidado` já importa `florence`. Verificar antes de implementar.

Se houver ciclo: mover `_get_florence_timeline_context()` para `modules/shared/timeline_context.py` — módulo sem dependências de domínio.

---

## Gotcha — `suggest_soap` sem `patient_id`

Se o encounter não tiver `patient_id` associado (caso raro mas possível), `_get_florence_timeline_context()` deve retornar string vazia sem lançar exception. Marie será chamado com `patient_history=""` — ainda funciona, só sem contexto longitudinal.

---

## Gotcha — resposta do Dify nem sempre é JSON puro

O LLM pode retornar texto com o JSON embutido (ex: `"Aqui está a nota SOAP: {...}"`). O `_parse_marie_soap_response()` deve usar `re.search(r'\{.*\}', response, re.DOTALL)` para extrair o JSON antes de `json.loads()`.

---

## Entrega

```
feat(florence): SOAP via Marie RAG — timeline context, florence_soap_rag workflow, fallback preservado
```
Hash → enviar ao ARQUITETO após `git push origin HEAD:main` confirmado.
