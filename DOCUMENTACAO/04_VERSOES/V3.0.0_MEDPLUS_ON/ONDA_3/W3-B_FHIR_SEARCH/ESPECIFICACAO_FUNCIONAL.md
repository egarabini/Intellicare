# 📋 W3-B — Especificação Funcional + Técnica: FHIR Search Engine

## 1. Objetivo
Implementar um SQL builder que traduz FHIR Search (RFC) para queries PostgreSQL otimizadas, permitindo buscas como `GET /fhir/Patient?name=Silva&birthdate=gt1990-01-01&_count=20`.

## 2. Funcionalidades
- **Search Parameters padrão:** _id, _lastUpdated, _tag, _profile, _security, _text
- **Tipos de busca:** string, token, date, reference, quantity, number, composite, uri
- **Operadores:** eq, ne, gt, lt, ge, le, sa, eb, ap
- **Modifiers:** :exact, :contains, :missing, :not, :text, :above, :below
- **Especiais:** _include, _revinclude, _sort, _count, _offset, _total, _summary
- **Chaining:** `Observation?subject:Patient.name=Silva`
- **Reverse chaining:** `Patient?_has:Observation:subject:code=glucose`
- **Compartment search:** `Patient/{id}/Observation` (equivalente a $everything sem wrapper)

## 3. Arquitetura

```
intellicare-core/
└── intellicare_core/
    └── fhir_search/                  # [NOVO]
        ├── __init__.py
        ├── parser.py                 # Parse FHIR search string → SearchRequest
        ├── sql_builder.py            # SearchRequest → SQL query
        ├── search_params.py          # Registry de SearchParameters por ResourceType
        ├── operators.py              # Operadores (gt, lt, contains, etc.)
        ├── includes.py               # _include / _revinclude resolver
        └── pagination.py             # Cursor-based + offset pagination
```

## 4. SQL Builder

```python
class FHIRSQLBuilder:
    def build(self, search: SearchRequest, tenant_id: str) -> Tuple[str, list]:
        """
        Input: SearchRequest(resource_type="Patient", filters=[
            Filter(code="name", op="contains", value="Silva"),
            Filter(code="birthdate", op="gt", value="1990-01-01"),
        ], count=20, offset=0, sort=["name"])
        
        Output SQL:
        SELECT resource FROM fhir_resources
        WHERE tenant_id = $1
          AND resource_type = $2
          AND resource->>'name' ILIKE '%' || $3 || '%'
          AND (resource->>'birthDate')::date > $4
        ORDER BY resource->>'name'
        LIMIT $5 OFFSET $6
        """
```

## 5. Referência Medplum
- `fhir/search.ts` (69KB) — FHIR Search → SQL
- `fhir/sql.ts` (37KB) — SQL builder
- `fhir/searchparameter.ts` (9KB) — SearchParameter registry

## 6. Plano: 14 dias (Dev 3 + Dev 4)
- Dia 1-3: Parser de FHIR Search string + SearchRequest model
- Dia 4-6: SQL builder para tipos simples (string, token, date, reference)
- Dia 7-9: Tipos complexos (quantity, composite) + operadores + modifiers
- Dia 10-11: _include / _revinclude / _sort / pagination
- Dia 12-13: Chaining e reverse chaining
- Dia 14: Testes de performance + otimização de índices + merge
