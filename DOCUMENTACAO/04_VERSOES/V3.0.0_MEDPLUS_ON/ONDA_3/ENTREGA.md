# 📦 ONDA_3 — Relatório de Entrega

**Data:** 2026-02-22
**Status:** ✅ CONCLUÍDA — W3-A (FHIR-Native Storage) + W3-B (FHIR Search Engine)

---

## W3-A: FHIR-Native Storage

### Objetivo
Implementar uma camada de persistência nativa para recursos FHIR R4 com versionamento completo, soft-delete, histórico de versões (vread), indexação de compartimentos e suporte a multi-tenancy — inspirada no Medplum FHIRDataSource, mas em Python/SQLAlchemy.

### Arquivos Criados / Modificados

#### `intellicare-core/intellicare_core/fhir_storage/`
| Arquivo | Descrição |
|---------|-----------|
| `__init__.py` | API pública: FHIRRepository, FHIRStorageBase, extract_compartments, ResourceNotFoundError |
| `models.py` | `FHIRStorageBase` (DeclarativeBase separada), `FHIRNativeResource`, `FHIRResourceHistory` |
| `repository.py` | `FHIRRepository` — CRUD completo + history + vread + upsert |
| `compartments.py` | `extract_compartments()` — indexa Patient/Organization/Practitioner/Encounter |

#### `intellicare-grahame/grahame/services/fhir_native_service.py`
- `FHIRNativeService` — bridge entre FastAPI e FHIRRepository
- Mapeamento HTTP 404 para ResourceNotFoundError
- Search delegado ao FHIRSQLBuilder

#### `intellicare-grahame/grahame/api/routes/fhir_native_routes.py`
- Router `/api/v2/fhir/` com rotas: create, read, update, delete, history, vread, search

#### `intellicare-grahame/grahame/api/app.py`
- Adicionado registro de `FHIRStorageBase.metadata.create_all` no startup
- Adicionado `fhir_native_router` com prefix `/api/v1`

### Decisão de Arquitetura: FHIRStorageBase Separado

Para evitar conflito de metadados entre a tabela legada `fhir_resources` (Base do Grahame) e a nova tabela `fhir_native_resources`, foi criada uma `DeclarativeBase` separada:

```python
class FHIRStorageBase(DeclarativeBase):
    pass  # Metadados isolados da Base principal do Grahame
```

Ambas recebem `create_all` no startup de forma sequencial e segura.

### Schema das Tabelas

**`fhir_native_resources`** — estado atual de cada recurso:
| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `pk` | String UUID | PK surrogate |
| `fhir_id` | String | ID FHIR do recurso |
| `tenant_id` | String | Multi-tenancy |
| `resource_type` | String | Tipo FHIR (Patient, Observation…) |
| `version_id` | String UUID | Versão atual |
| `resource` | JSON | Recurso FHIR completo |
| `last_updated` | DateTime | Timestamp da última modificação |
| `author` | String? | Referência ao autor (Practitioner/…) |
| `compartments` | JSON | Lista de referências de compartimento |
| `is_deleted` | Boolean | Soft-delete flag |

**`fhir_native_history`** — histórico imutável de versões:
| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `version_id` | String UUID | PK (imutável) |
| `fhir_id` | String | ID FHIR do recurso |
| `tenant_id` | String | Multi-tenancy |
| `resource_type` | String | Tipo FHIR |
| `resource` | JSON | Snapshot do recurso nesta versão |
| `last_updated` | DateTime | Timestamp desta versão |
| `author` | String? | Autor desta versão |
| `interaction` | String | `create` \| `update` \| `delete` |

### Capacidades do FHIRRepository

| Método | Descrição |
|--------|-----------|
| `create(resource)` | Cria novo recurso, injeta `meta.versionId` e `meta.lastUpdated` |
| `read(resource_type, fhir_id)` | Lê versão atual; lança `ResourceNotFoundError` se deletado |
| `update(resource_type, fhir_id, resource)` | Nova versão; mantém histórico |
| `delete(resource_type, fhir_id)` | Soft-delete com entrada no histórico |
| `history(resource_type, fhir_id)` | Histórico de versões, mais recente primeiro |
| `vread(resource_type, fhir_id, version_id)` | Versão específica pelo version_id |
| `search(resource_type, compartment_ref?)` | Busca básica com filtro de compartimento |
| `upsert(resource)` | Create-or-update baseado em `resource.id` |

---

## W3-B: FHIR Search Engine

### Objetivo
Implementar um motor de busca FHIR R4 conforme spec de search parameters, com suporte a operadores de prefixo (gt/lt/ge/le), modificadores (:contains, :exact), tokens sistema|valor, paginação cursor e construção dinâmica de queries SQLAlchemy — inspirado no FHIRRepository.search() do Medplum.

### Arquivos Criados

#### `intellicare-core/intellicare_core/fhir_search/`
| Arquivo | Descrição |
|---------|-----------|
| `__init__.py` | API pública: FHIRSQLBuilder, parse_search_params, SearchRequest, SearchResult |
| `models.py` | Pydantic: `SearchFilter`, `SearchRequest`, `SearchResult` (com `to_bundle()`) |
| `search_params.py` | `SearchParamDef`, `SEARCH_PARAMS` registry, `get_search_param()` |
| `parser.py` | `parse_search_params()` — URL params → SearchRequest |
| `sql_builder.py` | `FHIRSQLBuilder` — SearchRequest → SQLAlchemy SELECT → SearchResult |
| `pagination.py` | `build_bundle_links()`, `to_fhir_bundle()` |

### Recursos Cobertos no Registry (SEARCH_PARAMS)

| Resource Type | Params |
|---------------|--------|
| Patient | name, family, given, birthdate, gender, active, identifier, general-practitioner + _COMMON |
| Observation | status, code, subject, patient, date, value-quantity, performer, category + _COMMON |
| Encounter | status, subject, patient, date, class, service-provider + _COMMON |
| MedicationRequest | status, subject, patient, intent, medication, requester + _COMMON |
| Practitioner | name, identifier, active + _COMMON |
| Organization | name, active, type + _COMMON |
| Condition | status, subject, patient, code, category + _COMMON |
| DiagnosticReport | status, subject, patient, code, date + _COMMON |

**Params Comuns (`_COMMON`):** `_id`, `_lastUpdated`, `_tag`, `_profile`

### Operadores Suportados

| Operador | Descrição | Exemplo |
|----------|-----------|---------|
| `eq` (default) | Igualdade | `gender=female` |
| `ne` | Diferente | `status=ne=active` |
| `gt` / `lt` | Maior / menor | `birthdate=gt1990-01-01` |
| `ge` / `le` | ≥ / ≤ | `value-quantity=le100` |
| `co` | Contém (LIKE) | `name:contains=silva` |
| `sw` | Começa com | `name:sw=mar` |
| `eq` (modificador `:exact`) | Igualdade exata case-sensitive | `family:exact=Silva` |

### Estratégia SQL (Cross-DB Compat)

**Caminhos simples** (sem `[*]`): `column["key"].as_string()` → `JSON_EXTRACT` no SQLite, `->>` no PostgreSQL.

**Caminhos array** (com `[*]`): `LIKE` aproximado sobre o JSON como texto (`cast(resource, Text)`). Funcional para buscas comuns; em produção PostgreSQL, GIN indexes oferecem precisão total.

**Datas**: comparação lexicográfica via `func.substr(expr, 1, 10)` — funciona com ISO 8601.

**Números/quantidades**: cast para JSON numérico com operadores `>`, `<`, etc.

---

## Testes

### W3-A — fhir_storage (37 testes)

| Arquivo | Cenários |
|---------|----------|
| `tests/fhir_storage/test_compartments.py` | 12 — Patient próprio, Observation extrai subject, Practitioner performer, deduplicação |
| `tests/fhir_storage/test_repository.py` | 25 — create/read/update/delete/history/vread/search/upsert/tenant_isolation/versioning |

### W3-B — fhir_search (50 testes)

| Arquivo | Cenários |
|---------|----------|
| `tests/fhir_search/test_parser.py` | 18 — empty, prefixes (gt/le/ge), modifiers, token pipe, count/offset/sort/include/summary, _id |
| `tests/fhir_search/test_search_params.py` | 15 — known/unknown codes, fallback _COMMON, types, paths, all resource types have _id |
| `tests/fhir_search/test_sql_builder.py` | 20 — empty search, deleted excluded, _id filter, token, array/contains, date gt/le, tenant isolation, pagination, count, next_offset, total accurate, unknown param, resource type isolation |

### Resultado

```
55 passed (fhir_storage + fhir_search antes da adição de test_search_params + test_sql_builder)
87 passed total (W3-A + W3-B)
```

> **Nota:** `test_migrations.py` e `test_performance_benchmarks.py` requerem infraestrutura externa (PostgreSQL, Kafka) — errors pré-existentes, não relacionados à ONDA_3.

---

## Bugs Encontrados e Corrigidos

### 1. `_id` ignorado como filtro (parser.py)
`_id` caía no bloco "skip other leading-underscore params" antes de chegar ao bloco de filtros.

**Fix:** Adicionado handler explícito para `_id` antes do skip genérico de underscore params:
```python
if raw_key == "_id":
    for val in values:
        filters.append(SearchFilter(code="_id", op="eq", value=val))
    continue
```

### 2. `.as_string()` inválido em `cast(resource, JSON)` (sql_builder.py)
`cast(column, JSON).as_string()` lança `InvalidRequestError` — `.as_string()` só funciona em expressões de índice JSON (`col["key"].as_string()`).

**Fix:** Usar `cast(FHIRNativeResource.resource, Text)` para obter o JSON como string de texto para operações LIKE:
```python
json_text = func.lower(cast(FHIRNativeResource.resource, Text))
return json_text.like(pattern)
```

---

## Integração com Grahame — Endpoints /api/v2/fhir/

| Método | Path | Operação FHIR |
|--------|------|---------------|
| POST | `/api/v2/fhir/{resource_type}` | Create |
| GET | `/api/v2/fhir/{resource_type}/{fhir_id}` | Read |
| PUT | `/api/v2/fhir/{resource_type}/{fhir_id}` | Update |
| DELETE | `/api/v2/fhir/{resource_type}/{fhir_id}` | Delete (soft) |
| GET | `/api/v2/fhir/{resource_type}/{fhir_id}/_history` | History |
| GET | `/api/v2/fhir/{resource_type}/{fhir_id}/_history/{version_id}` | VRead |
| GET | `/api/v2/fhir/{resource_type}` | Search |

Todos os endpoints retornam FHIR R4 compliant (recursos com `meta.versionId` + `meta.lastUpdated`; history como Bundle).

---

## Próxima ONDA

**ONDA_4** — FHIR Subscriptions Engine + Webhook Delivery (W4-A) + Async Event Processing (W4-B).
