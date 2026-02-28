# W11-C — Diário de Execução

## 2026-02-25 — Execução DEV2

### Escopo executado
- Implementado override de display por idioma com `Accept-Language`.

### Entregas
- Parser de `Accept-Language` com ordenação por `q`.
- Resolver de display por `designation` com fallback.
- Aplicação de i18n nas operações:
  - `CodeSystem/$lookup`
  - `CodeSystem/$validate-code`
  - `ValueSet/$expand`
  - `ValueSet/$validate-code`
  - `ConceptMap/$translate`

### Arquivos
- `intellicare-grahame/grahame/utils/accept_language.py`
- `intellicare-grahame/grahame/services/display_resolver.py`
- `intellicare-grahame/grahame/api/routes/terminology_routes.py`
- `intellicare-grahame/tests/test_onda11_terminology.py`

### Testes
- `pytest -q tests/test_onda11_terminology.py tests/test_custom_operations.py tests/test_conceptmap_translate.py`
- Resultado: `14 passed`
