# W11-B — Terminology ($lookup, $validate-code) — Plano de Implementação

**Workstream:** W11-B
**Estimativa:** 7 dias
**Responsável:** DEV1 (execução DEV2 em 2026-02-25)
**Status Atual:** ✅ Concluído

---

## Ordem de Execução

| # | Task | Dias | Depende |
|---|------|------|---------|
| 1 | LookupService (buscar código no CodeSystem) | 2 | — |
| 2 | Operação CodeSystem/$lookup | 1 | 1 |
| 3 | Operação CodeSystem/$validate-code | 1 | 1 |
| 4 | ValueSet/$validate-code (expand + membership) | 2 | 1 |
| 5 | Registrar rotas + testes | 1 | 2-4 |

---

## Passo a Passo

### Passo 1: LookupService
- lookup(code, system, version?) -> display, properties
- Integrar com FHIR Store (CodeSystem) ou Terminology Service
- Retornar designations e properties do CodeSystem.concept

### Passo 2: CodeSystem/$lookup
- POST /fhir/CodeSystem/$lookup e /fhir/CodeSystem/{id}/$lookup
- Extrair Parameters, chamar LookupService
- Retornar Parameters com name, display, property[]

### Passo 3: CodeSystem/$validate-code
- POST /fhir/CodeSystem/$validate-code
- Verificar se código existe no CodeSystem
- Retornar result (boolean), display (se encontrado)

### Passo 4: ValueSet/$validate-code
- POST /fhir/ValueSet/$validate-code
- Expandir ValueSet (reutilizar $expand)
- Verificar se code está no conjunto expandido
- Retornar result

### Passo 5: Testes
- test_codesystem_lookup_found
- test_codesystem_lookup_not_found
- test_codesystem_validate_code
- test_valueset_validate_code

---

## Checklist de Entrega

- [x] CodeSystem/$lookup funcional
- [x] CodeSystem/$validate-code funcional
- [x] ValueSet/$validate-code funcional
- [x] Integração com Terminology Service
- [x] Testes passando

---

## Evidências de Execução (2026-02-25)

### Endpoints entregues
- `POST /api/v1/fhir/CodeSystem/$lookup`
- `POST /api/v1/fhir/CodeSystem/{id}/$lookup`
- `POST /api/v1/fhir/CodeSystem/$validate-code`
- `POST /api/v1/fhir/CodeSystem/{id}/$validate-code`
- `POST /api/v1/fhir/ValueSet/$validate-code`

### Implementação
- Arquivos:
  - `intellicare-grahame/grahame/api/routes/terminology_routes.py`
  - `intellicare-grahame/tests/test_onda11_terminology.py`

### Testes
- Comando:
  - `pytest -q tests/test_onda11_terminology.py tests/test_custom_operations.py tests/test_conceptmap_translate.py`
- Resultado:
  - `14 passed`
