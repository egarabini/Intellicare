# 📦 ONDA_5 — Relatório de Entrega

**Data:** 2026-02-22
**Status:** ✅ CONCLUÍDA — W5-A (CDS Hooks 2.0) + W5-C (Terminology Service)

---

## W5-A: CDS Hooks 2.0 — Clinical Decision Support as a Service

### Objetivo
Implementar o protocolo HL7 CDS Hooks 2.0 no IntelliCare: um servidor de suporte à decisão clínica que pode ser invocado pelo EHR/Portal em pontos chave do fluxo clínico (abertura de prontuário, assinatura de prescrição), retornando **Cards** acionáveis ao clínico.

### Arquivos Criados

#### `intellicare-core/intellicare_core/cds_hooks/`

| Arquivo | Descrição |
|---------|-----------|
| `__init__.py` | Exports públicos do pacote |
| `models.py` | `Card`, `CardSource`, `Suggestion`, `Action`, `Link`, `CDSRequest`, `CDSResponse`, `CDSServiceDefinition`, `FHIRAuthorization` |
| `service.py` | `CDSService` (ABC) — base para implementar serviços |
| `registry.py` | `CDSServiceRegistry` — registro e dispatch de serviços |

#### `intellicare-grahame/grahame/cds_services/`

| Arquivo | Serviço | Hook | Cards |
|---------|---------|------|-------|
| `patient_view.py` | `PatientViewAlertsService` | `patient-view` | Alergias não documentadas, condições de alto risco, prontuário vazio |
| `order_sign.py` | `OrderSignCheckerService` | `order-sign` | AINE+DRC crítico, Metformina+DRC estágio 4/5 crítico, medicamentos de alta vigilância |

#### `intellicare-grahame/grahame/api/routes/cds_hooks_routes.py`

Router FastAPI registrado em `/api/v1/cds-services`:

| Método | Path | Função |
|--------|------|--------|
| `GET` | `/cds-services` | Discovery — lista serviços registrados |
| `POST` | `/cds-services/{service_id}` | Invocar hook → Cards |
| `POST` | `/cds-services/{service_id}/feedback` | Feedback stub (futuro: Kestra) |

### Modelos — `models.py`

**`Card`** — unidade de resposta principal:
```python
Card(
    uuid: str,          # auto-UUID
    summary: str,       # título curto (≤ 140 chars)
    detail: str,        # markdown expandido
    indicator: "info" | "warning" | "critical",
    source: CardSource,
    suggestions: list[Suggestion],
    selectionBehavior: "at-most-one" | "any",
    links: list[Link],
)
```

**`CDSRequest`** — payload recebido do EHR:
```python
CDSRequest(
    hookInstance: str,   # UUID da chamada
    hook: str,           # "patient-view" | "order-sign"
    context: dict,       # patientId, draftOrders, etc.
    prefetch: dict,      # recursos FHIR pré-buscados
    fhirServer: str,
    fhirAuthorization: FHIRAuthorization,
)
```

### PatientViewAlertsService

**Prefetch requerido:**
- `Patient/{{context.patientId}}`
- `Condition?patient={{context.patientId}}&clinical-status=active&_count=50`
- `AllergyIntolerance?patient={{context.patientId}}&_count=10`

**Cards emitidos:**

| Condição | Indicador |
|----------|-----------|
| Sem registro de alergias | `warning` |
| Condição de alto risco ativa (N18.x, E11.x, I10, I50, J44) | `warning` |
| Nenhuma condição ativa registrada | `info` |

**Códigos de alto risco:** N18, N18.3–N18.5, E11, I10, I50, J44

### OrderSignCheckerService

**Prefetch requerido:**
- `Patient/{{context.patientId}}`
- `Condition?patient={{context.patientId}}&clinical-status=active&_count=50`

**Contexto requerido:** `draftOrders` Bundle com MedicationRequests a assinar

**Cards emitidos:**

| Condição | Indicador |
|----------|-----------|
| AINE + DRC ativa (qualquer N18) | `critical` + sugestão paracetamol |
| Metformina + DRC estágio 4/5 (N18.4, N18.5) | `critical` |
| Medicamento de alta vigilância (insulina, varfarina, heparina, amiodarona, lítio, digoxina) | `warning` |

### Testes

| Módulo | Arquivo | Testes |
|--------|---------|--------|
| `intellicare-core` | `tests/cds_hooks/test_models.py` | 14 |
| `intellicare-core` | `tests/cds_hooks/test_registry_and_services.py` | 9 |
| `intellicare-grahame` | `tests/test_cds_services.py` | 11 |
| **Total W5-A** | | **34** |

---

## W5-C: Terminology Service — $lookup, $expand, $validate-code, $translate

### Objetivo
Implementar um servidor de terminologia FHIR R4 in-memory com os vocabulários clínicos mais utilizados no IntelliCare, expondo as operações canônicas `$lookup`, `$expand`, `$validate-code` e `$translate` via FastAPI.

### Arquivos Criados

#### `intellicare-core/intellicare_core/terminology/`

| Arquivo | Descrição |
|---------|-----------|
| `__init__.py` | Exports públicos |
| `models.py` | `CodeSystemConcept`, `ValueSetExpansion`, `TranslationMatch` |
| `registry.py` | `TerminologyRegistry` + `get_registry()` singleton — pré-populado com 5 sistemas |
| `operations.py` | `lookup()`, `expand()`, `validate_code()`, `translate()` — retornam dicts FHIR Parameters |

#### `intellicare-grahame/grahame/api/routes/terminology_routes.py`

Router FastAPI registrado em `/api/v1`:

| Método | Path | Operação FHIR |
|--------|------|---------------|
| `GET` | `/CodeSystem/$lookup` | `CodeSystem/$lookup` |
| `GET` | `/ValueSet/$expand` | `ValueSet/$expand` |
| `GET` | `/ValueSet/$validate-code` | `ValueSet/$validate-code` |
| `GET` | `/ConceptMap/$translate` | `ConceptMap/$translate` |

### Terminologias Pré-carregadas

| Sistema | URI Canônico | Conceitos |
|---------|-------------|-----------|
| **LOINC** | `http://loinc.org` | 20 (sinais vitais + labs: creatinina, eGFR, HbA1c, glicemia, hemograma, lipidograma) |
| **ICD-10/CID-10** | `http://hl7.org/fhir/sid/icd-10` | 21 (DRC, DM2, HAS, IC, DPOC, dislipidemia, depressão, ansiedade) |
| **SNOMED CT** | `http://snomed.info/sct` | 10 (findings clínicos comuns) |
| **TUSS** | `http://www.saude.gov.br/fhir/...` | 10 (procedimentos ambulatoriais e laboratoriais) |
| **RxNorm** | `http://www.nlm.nih.gov/research/umls/rxnorm` | 10 (medicamentos + designação PT-BR) |
| **Total** | | **71 conceitos** |

### ValueSets Pré-definidos

| URL Canônica | Título | Sistema | Códigos |
|-------------|--------|---------|---------|
| `.../ValueSet/vital-signs` | IntelliCare Vital Signs | LOINC | 8 (FC, FR, T, SpO₂, Peso, Altura, PA, IMC) |
| `.../ValueSet/chronic-conditions-icd10` | Chronic Conditions | ICD-10 | 17 (DRC+DM2+HAS+IC+DPOC) |
| `.../ValueSet/lab-kidney` | Lab Kidney Function | LOINC | 3 (Creatinina, eGFR, ACR) |
| `.../ValueSet/lab-metabolic` | Lab Metabolic Panel | LOINC | 6 (Glicemia, HbA1c, Colesterol total/HDL/LDL, TG) |
| `.../ValueSet/high-alert-medications` | High-Alert Medications | RxNorm | 2 (varfarina, insulina glargina) |

### ConceptMaps Pré-definidos

| URL | Mapeamento | Entradas |
|-----|------------|---------|
| `.../ConceptMap/icd10-to-snomed` | ICD-10 → SNOMED CT | 7 (E11, I10, N18, I50, J44, F32, F41.1) |

### Operações — `operations.py`

**`lookup(system, code)`** → `Parameters` dict:
```json
{
  "resourceType": "Parameters",
  "parameter": [
    {"name": "name",       "valueString": "<system>"},
    {"name": "display",    "valueString": "Heart rate"},
    {"name": "definition", "valueString": "..."},
    {"name": "property",   "part": [{"name": "code", "valueCode": "class"}, {"name": "valueString", "valueString": "VITALS"}]},
    {"name": "designation","part": [{"name": "language", "valueCode": "pt-BR"}, {"name": "value", "valueString": "..."}]}
  ]
}
```

**`expand(url, offset, count)`** → `ValueSet` dict com `expansion.contains[]`

**`validate_code(url, system, code)`** → `Parameters` com `result: boolean` + `display` ou `message`

**`translate(concept_map_url, source_system, source_code)`** → `Parameters` com `result: boolean` + `match[]` (equivalence + valueCoding)

### Testes

| Arquivo | Testes |
|---------|--------|
| `tests/terminology/test_registry.py` | 19 |
| `tests/terminology/test_operations.py` | 17 |
| **Total W5-C** | **36** |

---

## Resumo de Testes ONDA_5

| Workstream | Testes |
|------------|--------|
| W5-A — CDS Hooks | 34 |
| W5-C — Terminology | 36 |
| **Total ONDA_5** | **70** |

Todos passando: `34 passed` (core + grahame) + `36 passed` (core terminology).

---

## Acúmulo MEDPLUS_ON

| ONDA | Workstreams | Testes adicionados |
|------|-------------|--------------------|
| ONDA_1 | W1-A (IPS Generator) + W1-B (Policy Engine) | 91 |
| ONDA_2 | W2-A (Audit Trail) + W2-B (Questionnaire Engine) | 105 |
| ONDA_3 | W3-A (FHIR-Native Storage) + W3-B (FHIR Search Engine) | 87 |
| ONDA_4 | W4-A (React Components) + W4-B (SMART-on-FHIR) | 73 |
| ONDA_5 | W5-A (CDS Hooks 2.0) + W5-C (Terminology Service) | 70 |
| **Total** | **10 workstreams** | **~426 testes** |

---

## Próxima ONDA

**ONDA_6** — opções candidatas:
- **W6-A**: FHIR Bulk Data `$export` NDJSON — exportação assíncrona para analytics (Kestra ETL)
- **W6-B**: CDS Hooks — Feedback Loop + Métricas (Prometheus/Grafana) — fechar o ciclo do W5-A
- **W6-C**: FHIR Subscriptions v2 (Backport R5) — WebSocket + Email channels (evolução do W2-A)
