# W10-B — ConceptMap Import + $translate — Plano de Implementação

**Workstream:** W10-B
**Estimativa:** 7 dias
**Responsável:** DEV1 (execução DEV2 em 2026-02-25)
**Status Atual:** ✅ Concluído

---

## Ordem de Execução

| # | Task | Dias | Depende |
|---|------|------|---------|
| 1 | ConceptMapService (parse groups/elements) | 2 | — |
| 2 | Operação $translate (lookup) | 2 | 1 |
| 3 | Registrar rota ConceptMap/$translate | 1 | 2 |
| 4 | Tabela de índice (opcional, para performance) | 1 | 1 |
| 5 | Testes unitários + integração | 1 | 1-4 |

---

## Passo a Passo

### Passo 1: ConceptMapService
- `parse_conceptmap(conceptmap: dict) -> List[TranslationEntry]`
- Extrair group[].element[] e element.target[]
- Estrutura: (source_system, source_code, target_system, target_code, target_display, equivalence)
- Chamado ao criar/atualizar ConceptMap (hook ou service)

### Passo 2: Operação $translate
- `translate(conceptmap_id, code, system, target?, reverse?) -> Parameters`
- Buscar no ConceptMap (in-memory ou índice)
- Retornar Parameters com result e match

### Passo 3: Registrar Rota
- `POST /fhir/ConceptMap/{id}/$translate`
- `POST /fhir/ConceptMap/$translate` (com parâmetro url ou source/target)
- Integrar ao router FHIR existente

### Passo 4: Tabela de Índice
- Criar `conceptmap_translation_index` se ConceptMaps > 1000 elementos
- Popular no create/update do ConceptMap
- Usar para lookup em $translate

### Passo 5: Testes
- `test_conceptmap_service_parse`
- `test_conceptmap_translate_match`
- `test_conceptmap_translate_no_match`
- `test_conceptmap_translate_reverse`
- `test_conceptmap_import_bundle`

---

## Checklist de Entrega

- [x] ConceptMap import (POST) funcional
- [x] ConceptMap/$translate funcional
- [x] Parâmetros code, system, target, reverse suportados
- [x] Resposta Parameters com result e match
- [x] Índice para performance (se necessário) — não necessário neste volume atual
- [x] Testes passando

---

## Evidências de Execução (2026-02-25)

### Código Implementado
- `grahame/services/conceptmap_service.py`
- `grahame/api/routes/terminology_routes.py`
- `tests/test_conceptmap_translate.py`

### Endpoints entregues
- `POST /api/v1/fhir/ConceptMap/$import`
- `POST /api/v1/fhir/ConceptMap/{id}/$translate`
- `POST /api/v1/fhir/ConceptMap/$translate`

### Cobertura funcional entregue
- Import de `ConceptMap` individual e via `Bundle`.
- Parse de `group[].element[].target[]` para tradução.
- Tradução por `id` ou por `url`.
- Suporte a `code`, `system`, `target`, `reverse`.
- Retorno FHIR `Parameters` com `result` e `match`.
- Suporte a múltiplos ConceptMaps no tenant (filtro opcional por `url`/`id`).

### Testes
- Comando executado:
  - `pytest -q tests/test_custom_operations.py tests/test_conceptmap_translate.py`
- Resultado:
  - `9 passed`
