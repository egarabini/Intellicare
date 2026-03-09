# ✅ W1-A — Entrega: Operações FHIR R4

**Data:** 2026-02-23
**Módulo:** `intellicare-grahame`
**Status:** CONCLUÍDO
**Dev:** DEV0

---

## Resumo

Implementação completa das **5 operações FHIR R4** no `intellicare-grahame`, transformando-o de um simples repositório de recursos JSON em um **CDR (Clinical Data Repository) funcional**, absorvendo a filosofia FHIR-First do Medplum em Python-native.

---

## Operações Implementadas

| Operação | Endpoint | Status |
|---|---|---|
| `Patient/$everything` | `GET /api/v1/fhir/Patient/{id}/$everything` | ✅ |
| `Patient/$summary` | `GET /api/v1/fhir/Patient/{id}/$summary` | ✅ |
| `ValueSet/$expand` | `GET/POST /api/v1/fhir/ValueSet/{id}/$expand` | ✅ |
| `{Resource}/$validate` | `POST /api/v1/fhir/{ResourceType}/$validate` | ✅ |
| `Measure/$evaluate-measure` | `GET /api/v1/fhir/Measure/{id}/$evaluate-measure` | ✅ |

---

## Arquivos Criados

### Fundação (`grahame/fhir/`)

| Arquivo | Descrição |
|---|---|
| `fhir/__init__.py` | Package FHIR core |
| `fhir/compartment.py` | Patient Compartment definitions (20 resource types, campos de referência, `resource_belongs_to_patient()`, `extract_references()`) |
| `fhir/reference_resolver.py` | Resolução recursiva de referências FHIR (Organization, Location, Practitioner, PractitionerRole, Medication, Device, RelatedPerson, Specimen) — até 2 níveis de profundidade |
| `fhir/ips_sections.py` | 18 seções IPS com código LOINC, `classify_observation()`, `classify_condition()`, `classify_resource()`, `build_ips_composition()` |
| `fhir/fhir_error.py` | `fhir_error()` retorna JSONResponse com `OperationOutcome` e `Content-Type: application/fhir+json` |

### Operações (`grahame/fhir/operations/`)

| Arquivo | Responsabilidade |
|---|---|
| `operations/__init__.py` | Package |
| `operations/patient_everything.py` | `patient_everything()` — busca compartmentalizada por tenant, `EverythingParams` (start/end/_since/_count/_offset/_type), resolução de referências, deduplicação, paginação |
| `operations/patient_summary.py` | `patient_summary()` — classifica recursos em seções IPS, monta `Composition` FHIR R4, retorna Bundle do tipo `document` |
| `operations/valueset_expand.py` | `expand_valueset()` — carrega ValueSet por id ou URL canônica, busca conceitos em `fhir_codesystem_concepts`, filtro por texto, paginação |
| `operations/resource_validate.py` | `validate_resource()` — valida campos obrigatórios, status válido, mode create/update, retorna `OperationOutcome` |
| `operations/measure_evaluate.py` | `evaluate_measure()` — carrega Measure, resolve sujeitos (Patient/Group/todos), avalia populações (initial/denominator/numerator), calcula score, retorna `MeasureReport` |

### Router (`grahame/api/routes/`)

| Arquivo | Descrição |
|---|---|
| `api/routes/__init__.py` | Package |
| `api/routes/fhir_operations.py` | 5 endpoints FastAPI com query params tipados, tratamento de erros como `OperationOutcome`, `Content-Type: application/fhir+json` |

### Modelo novo (`grahame/models/`)

| Arquivo | Tabela | Uso |
|---|---|---|
| `models/codesystem_concept.py` | `fhir_codesystem_concepts` | Conceitos pré-carregados de CodeSystems (CID-10, LOINC, TUSS) para o `$expand` |

### Testes (`tests/`)

| Arquivo | Testes |
|---|---|
| `tests/test_fhir_operations.py` | **45 cenários** cobrindo todas as 5 operações + helpers |

### Arquivos atualizados

| Arquivo | Mudança |
|---|---|
| `pyproject.toml` | Adicionado `fhir-resources = "^7.0"` |
| `grahame/models/__init__.py` | Export de `CodeSystemConcept` |
| `grahame/api/app.py` | Import dos modelos + registro do `operations_router`, import condicional de `intellicare_core` |
| `tests/conftest.py` | Import de `CodeSystemConcept` para registrar tabela no `Base.metadata` |

---

## Detalhes Técnicos

### Patient/$everything

```
Parâmetros suportados:
  _since  → filtra recursos modificados a partir de uma datetime ISO 8601
  _count  → máximo de recursos por página (default 100, max 1000)
  _offset → offset para paginação
  _type   → lista de ResourceTypes separados por vírgula
  start   → data início (YYYY-MM-DD) — filtra por effectiveDateTime, recordedDate etc.
  end     → data fim (YYYY-MM-DD)

Compartimento Patient (20 tipos):
  AllergyIntolerance, CarePlan, CareTeam, Condition, DiagnosticReport,
  DocumentReference, Encounter, Goal, Immunization, MedicationAdministration,
  MedicationRequest, Observation, Procedure, ServiceRequest, RiskAssessment,
  NutritionOrder, Coverage, Appointment, Communication, Flag

Referências resolvidas recursivamente (depth=2):
  Organization, Location, Practitioner, PractitionerRole,
  Medication, Device, RelatedPerson, Specimen
```

### Patient/$summary (IPS)

```
Seções IPS implementadas (18):
  allergies (48765-2), immunizations (11369-6), medications (10160-0),
  problem_list (11450-4), results (30954-2), vital_signs (8716-3),
  social_history (29762-2), procedures (47519-4), encounters (46240-8),
  plan_of_treatment (18776-5), goals (61146-7), health_concerns (75310-3),
  functional_status (47420-5), notes (11488-4), assessments (51848-0),
  reason_for_referral (42349-1), insurance (48768-6), devices (46264-8)

Classificação automática:
  Observation (vital-signs) → vital_signs
  Observation (social-history) → social_history
  Observation (disability LOINC 89572-3) → functional_status
  Observation (default) → results
  Condition (health-concern) → health_concerns
  Condition (default) → problem_list
```

### ValueSet/$expand

```
Tabela: fhir_codesystem_concepts
  - codesystem_url: URL do sistema (ex: http://loinc.org)
  - code: código do conceito
  - display: descrição legível
  - tenant_id: isolamento multi-tenant

Alimentação:
  - Script de seed (a implementar) para CID-10, LOINC, TUSS
  - Endpoint POST futuro para importar CodeSystem
```

### Resource/$validate

```
Validações implementadas:
  1. resourceType presente e corresponde ao endpoint
  2. Campos obrigatórios por tipo (Patient, Observation, Condition, Encounter,
     MedicationRequest, DiagnosticReport, Procedure, Immunization,
     AllergyIntolerance, CarePlan, Measure, ValueSet, CodeSystem)
  3. Status válido contra enum por tipo
  4. id obrigatório no modo "update"

HTTP 200 → válido
HTTP 422 → inválido com issues
```

### Measure/$evaluate-measure

```
Parâmetros:
  periodStart (obrigatório) → data início
  periodEnd   (obrigatório) → data fim
  subject     (opcional)   → Patient/{id} | Group/{id} | omitir para todos

Populações suportadas: initial-population, denominator, numerator
Score = numerator / denominator (retornado como measureScore)

Integração planejada:
  Donabedian cria/edita Measures via sua API
  Grahame executa evaluate-measure com acesso direto ao CDR
  MeasureReports persistidos são consultáveis pelo Donabedian
```

---

## Critérios de Aceite — Verificação

| # | Critério | Status |
|---|---|---|
| 1 | Todos os 5 endpoints retornam JSON FHIR R4 válido | ✅ |
| 2 | Erros retornam `OperationOutcome` padronizado | ✅ |
| 3 | Multi-tenancy funcional (dados isolados por tenant_id) | ✅ |
| 4 | Paginação funcional em `$everything` e `$expand` | ✅ |
| 5 | `$summary` gera Composition com as 18 seções IPS | ✅ |
| 6 | `$validate` retorna HTTP 200 para válido, 422 para inválido | ✅ |
| 7 | Cobertura de testes: 45 cenários, SQLite in-memory | ✅ |
| 8 | `Content-Type: application/fhir+json` em todos os endpoints | ✅ |
| 9 | Autenticação JWT — dependência de `intellicare-auth` declarada no `pyproject.toml` | ⚠️ Middleware pendente (fase posterior) |

---

## Decisões de Implementação

### 1. Filtro Python-side vs SQL-side
O compartiment search (verificar `resource.subject.reference == Patient/X`) foi implementado **Python-side** para garantir compatibilidade SQLite nos testes. Em produção PostgreSQL, pode ser otimizado com queries `jsonb_path_query` sem alterar a interface.

### 2. `$validate` sem `fhir.resources`
A dependência `fhir-resources>=7.0` foi adicionada ao `pyproject.toml`, mas a validação estrutural atual usa verificações internas para evitar complexidade na fase inicial. A integração completa com `fhir.resources.Patient.model_validate()` fica para hardening posterior.

### 3. `$evaluate-measure` — CQL heurístico
A avaliação completa de critérios `Measure.group.population.criteria.expression` requer um engine CQL (Clinical Quality Language). A implementação atual usa heurística (presença de recursos no período) com a flag `expression="true"` como caso base. CQL completo é escopo da Onda 2+.

### 4. Import condicional de `intellicare_core`
O `app.py` usa `try/except ImportError` para os imports de `intellicare_core` (TenantResolver, Prometheus metrics), garantindo que o módulo funciona standalone sem o core instalado — alinhado com o princípio LEGO.

---

## Próximos Passos

- **W1-B FHIR Subscriptions** — engine de eventos FHIR (REST-hook + WebSocket)
- **Script de seed** para `fhir_codesystem_concepts` (CID-10, LOINC, TUSS)
- **Middleware JWT** para autenticação nos endpoints `/fhir/`
- **Otimização SQL** para `$everything` em PostgreSQL (jsonb operators)
- **CQL Engine** básico para `$evaluate-measure` (Onda 2)

---

## Referência Medplum

| Conceito absorvido | Arquivo Medplum | Implementação IntelliCare |
|---|---|---|
| Patient Compartment | `repo.ts` (compartment search) | `fhir/compartment.py` |
| Patient $everything | `patienteverything.ts` (220 linhas) | `operations/patient_everything.py` |
| Patient $summary IPS | `patientsummary.ts` (875 linhas) | `operations/patient_summary.py` + `ips_sections.py` |
| ValueSet $expand | `expand.ts` | `operations/valueset_expand.py` |
| $validate | `codesystemvalidatecode.ts` | `operations/resource_validate.py` |
| $evaluate-measure | `evaluatemeasure.ts` | `operations/measure_evaluate.py` |
| OperationOutcome errors | padrão global Medplum | `fhir/fhir_error.py` |
