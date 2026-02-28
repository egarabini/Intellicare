# 🔧 W1-A — Especificação Técnica: Operações FHIR

## 1. Arquitetura

### 1.1 Localização no Código
```
intellicare-grahame/
├── grahame/
│   ├── api/
│   │   ├── app.py                    # FastAPI app existente
│   │   └── routes/
│   │       └── fhir_operations.py    # [NOVO] Router de operações
│   ├── fhir/
│   │   ├── operations/               # [NOVO] Package de operações
│   │   │   ├── __init__.py
│   │   │   ├── patient_everything.py   # $everything
│   │   │   ├── patient_summary.py      # $summary (IPS)
│   │   │   ├── valueset_expand.py      # $expand
│   │   │   ├── resource_validate.py    # $validate
│   │   │   └── measure_evaluate.py     # $evaluate-measure
│   │   ├── compartment.py            # [NOVO] Patient Compartment definitions
│   │   ├── ips_sections.py           # [NOVO] IPS section builder
│   │   └── reference_resolver.py     # [NOVO] Recursive reference resolution
│   └── tests/
│       └── test_fhir_operations.py   # [NOVO]
```

### 1.2 Dependências Existentes
- `intellicare-core` → TenantResolver, DB session
- `intellicare-auth` → JWT middleware
- `fhir.resources` (pip) → Validação FHIR R4
- `httpx` → Comunicação inter-módulo (se necessário)

### 1.3 Dependências Novas
```toml
# pyproject.toml
[project.optional-dependencies]
fhir-operations = [
    "fhir.resources>=7.0",      # Modelos Pydantic FHIR R4
    "fhirpathpy>=0.2",          # FHIRPath evaluation
]
```

---

## 2. Especificação por Operação

### 2.1 `Patient/$everything` — `patient_everything.py`

```python
@dataclass
class EverythingParams:
    start: Optional[date] = None
    end: Optional[date] = None
    _since: Optional[datetime] = None
    _count: int = 100
    _offset: int = 0
    _type: Optional[List[str]] = None  # ResourceTypes a filtrar

async def patient_everything(
    patient_id: str,
    params: EverythingParams,
    db: AsyncSession,
    tenant_id: str,
) -> Bundle:
    """
    1. Ler Patient (verificar acesso)
    2. Buscar recursos do Patient Compartment
    3. Filtrar por _type, _since, start/end
    4. Resolver referências recursivamente
    5. Deduplicar
    6. Retornar Bundle searchset
    """
```

**Patient Compartment — Recursos incluídos:**
```python
PATIENT_COMPARTMENT_RESOURCES = [
    "AllergyIntolerance",   # patient
    "CarePlan",             # patient
    "CareTeam",             # patient
    "Condition",            # patient, subject
    "DiagnosticReport",     # subject
    "Encounter",            # patient
    "Goal",                 # patient
    "Immunization",         # patient
    "MedicationRequest",    # subject
    "Observation",          # subject, patient
    "Procedure",            # subject, patient
    "ServiceRequest",       # subject, patient
]

# Referências a resolver recursivamente
RESOLVE_REFERENCE_TYPES = [
    "Organization", "Location", "Practitioner",
    "PractitionerRole", "Medication", "Device"
]
```

**SQL Strategy:**
```sql
-- Para cada resource type no compartment:
SELECT * FROM fhir_resources
WHERE resource_type = :type
  AND tenant_id = :tenant
  AND (
    resource->'subject'->>'reference' = :patient_ref
    OR resource->'patient'->>'reference' = :patient_ref
  )
  AND (_since IS NULL OR last_updated >= :since)
ORDER BY id
LIMIT :count OFFSET :offset;
```

---

### 2.2 `Patient/$summary` — `patient_summary.py` + `ips_sections.py`

```python
class IPSSectionBuilder:
    """Classifica recursos em seções IPS automaticamente."""

    SECTION_MAP = {
        "AllergyIntolerance": "allergies",
        "Immunization": "immunizations",
        "MedicationRequest": "medications",
        "Procedure": "procedures",
        "Encounter": "encounters",
    }

    def classify_observation(self, obs: dict) -> str:
        """Classifica Observation por category code."""
        category = get_category_code(obs)
        match category:
            case "vital-signs": return "vital_signs"
            case "social-history": return "social_history"
            case "survey": return "functional_status"  # se LOINC disability
            case _: return "results"

    def classify_condition(self, cond: dict) -> str:
        """Classifica Condition: health-concern vs problem-list."""
        if has_loinc_category(cond, LOINC_HEALTH_CONCERNS):
            return "health_concerns"
        return "problem_list"

    def build_composition(self, patient, author, sections) -> Composition:
        """Monta Composition com seções não-vazias."""
```

**Seções LOINC IPS:**
```python
IPS_SECTIONS = {
    "allergies":          {"code": "48765-2", "display": "Allergies"},
    "immunizations":      {"code": "11369-6", "display": "Immunizations"},
    "medications":        {"code": "10160-0", "display": "Medications"},
    "problem_list":       {"code": "11450-4", "display": "Problem List"},
    "results":            {"code": "30954-2", "display": "Results"},
    "vital_signs":        {"code": "8716-3",  "display": "Vital Signs"},
    "social_history":     {"code": "29762-2", "display": "Social History"},
    "procedures":         {"code": "47519-4", "display": "Procedures"},
    "encounters":         {"code": "46240-8", "display": "Encounters"},
    "plan_of_treatment":  {"code": "18776-5", "display": "Plan of Treatment"},
    "goals":              {"code": "61146-7", "display": "Goals"},
    "health_concerns":    {"code": "75310-3", "display": "Health Concerns"},
    "functional_status":  {"code": "47420-5", "display": "Functional Status"},
    "notes":              {"code": "11488-4", "display": "Notes"},
    "assessments":        {"code": "51848-0", "display": "Assessments"},
    "reason_for_referral":{"code": "42349-1", "display": "Reason for Referral"},
    "insurance":          {"code": "48768-6", "display": "Insurance"},
    "devices":            {"code": "46264-8", "display": "Devices"},
}
```

---

### 2.3 `ValueSet/$expand` — `valueset_expand.py`

```python
async def expand_valueset(
    valueset_id: Optional[str],
    url: Optional[str],
    filter_text: Optional[str],
    count: int = 100,
    offset: int = 0,
    db: AsyncSession,
) -> ValueSet:
    """
    1. Carregar ValueSet por id ou url canônica
    2. Resolver includes (CodeSystem references)
    3. Filtrar conceitos por filter_text (case-insensitive, contains)
    4. Aplicar paginação
    5. Retornar ValueSet com expansion
    """
```

**Tabelas necessárias:**
```sql
-- Tabela de CodeSystems pré-carregados
CREATE TABLE fhir_codesystem_concepts (
    id UUID PRIMARY KEY,
    codesystem_url TEXT NOT NULL,
    code TEXT NOT NULL,
    display TEXT,
    tenant_id TEXT NOT NULL,
    UNIQUE(codesystem_url, code, tenant_id)
);
CREATE INDEX idx_concept_search ON fhir_codesystem_concepts(codesystem_url, display text_pattern_ops);
```

---

### 2.4 `Resource/$validate` — `resource_validate.py`

```python
async def validate_resource(
    resource_type: str,
    resource_data: dict,
    profile: Optional[str] = None,
    mode: str = "create",
) -> OperationOutcome:
    """
    1. Validar contra StructureDefinition do resource_type
    2. Se profile fornecido, validar contra profile
    3. Validar terminologia (códigos em ValueSets)
    4. Retornar OperationOutcome com issues
    """
```

**Usa `fhir.resources` para validação Pydantic:**
```python
from fhir.resources.patient import Patient
try:
    Patient.model_validate(resource_data)
except ValidationError as e:
    # Converter Pydantic errors → FHIR OperationOutcome issues
```

---

### 2.5 `Measure/$evaluate-measure` — `measure_evaluate.py`

```python
async def evaluate_measure(
    measure_id: str,
    period_start: date,
    period_end: date,
    subject: Optional[str] = None,  # Patient/{id} ou Group/{id}
    db: AsyncSession,
) -> MeasureReport:
    """
    1. Carregar Measure por id
    2. Para cada population group:
       a. Avaliar critérios initial-population
       b. Avaliar denominator
       c. Avaliar numerator
       d. Calcular score
    3. Montar MeasureReport
    """
```

**Integração com Donabedian:**
- Measures podem ser criadas/editadas pelo módulo Donabedian
- Evaluate-measure roda no Grahame com acesso direto ao CDR
- MeasureReports são persistidos e consultáveis

---

## 3. Router FastAPI

```python
# grahame/api/routes/fhir_operations.py
from fastapi import APIRouter, Depends, Query

router = APIRouter(prefix="/fhir", tags=["FHIR Operations"])

@router.get("/Patient/{patient_id}/$everything")
async def everything(patient_id: str, ...):
    ...

@router.get("/Patient/{patient_id}/$summary")
async def summary(patient_id: str, ...):
    ...

@router.post("/ValueSet/{valueset_id}/$expand")
@router.get("/ValueSet/{valueset_id}/$expand")
async def expand(valueset_id: str, ...):
    ...

@router.post("/{resource_type}/$validate")
async def validate(resource_type: str, ...):
    ...

@router.get("/Measure/{measure_id}/$evaluate-measure")
async def evaluate_measure(measure_id: str, ...):
    ...
```

---

## 4. Tratamento de Erros

Todos os erros retornam `OperationOutcome`:
```python
def fhir_error(status: int, code: str, diagnostics: str) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content={
            "resourceType": "OperationOutcome",
            "issue": [{
                "severity": "error",
                "code": code,
                "diagnostics": diagnostics
            }]
        },
        media_type="application/fhir+json"
    )
```

---

## 5. Testes

Cada operação deve ter:
- Testes unitários com mocks do DB
- Testes de integração com dados FHIR reais
- Testes de validação de conformidade FHIR (output correto)
- Testes de multi-tenancy (isolamento entre tenants)
- Testes de paginação
