# ONDA_7 — FHIR Bulk Data $export + CDS Hooks Feedback

**Data:** 2026-02-22
**Track:** MEDPLUS_ON (absorção Medplum → IntelliCare)
**Status:** ✅ ENTREGUE

---

## Escopo

| Work Item | Descrição | Status |
|-----------|-----------|--------|
| W7-A | FHIR Bulk Data Access 2.0 — `$export` endpoints | ✅ Done |
| W7-B | CDS Hooks Feedback real + métricas Prometheus | ✅ Done |

---

## W7-A — FHIR Bulk Data $export

### Referência
HL7 Bulk Data Access 2.0: https://hl7.org/fhir/uv/bulkdata/

### Protocolo implementado
```
GET  /$export               → 202 Accepted + Content-Location (kick-off)
GET  /Patient/$export       → 202 Accepted + Content-Location (kick-off paciente)
GET  /bulk-status/{job_id}  → 202 in-progress | 200 manifest JSON
DELETE /bulk-status/{job_id}→ 202 cancelado
GET  /bulk-data/{job_id}/{rtype} → NDJSON download
```

### Arquivos criados

**intellicare-core — pacote `bulk/`**

| Arquivo | Descrição |
|---------|-----------|
| `intellicare_core/bulk/__init__.py` | Exports do pacote |
| `intellicare_core/bulk/models.py` | `BulkExportStatus`, `BulkOutputFile`, `BulkExportManifest`, `BulkExportJob` |
| `intellicare_core/bulk/manager.py` | `BulkExportManager` + `get_bulk_manager()` singleton |

**intellicare-grahame — rotas**

| Arquivo | Descrição |
|---------|-----------|
| `grahame/api/routes/bulk_export_routes.py` | 5 endpoints bulk (novo) |
| `grahame/api/app.py` | Registra `bulk_router` (atualizado) |

### BulkExportManager — design

```python
class BulkExportManager:
    _jobs: dict[str, BulkExportJob]        # in-memory job store
    _data: dict[str, dict[str, list[str]]] # job → rtype → [ndjson lines]

    def create_job(request_url, resource_types, tenant_id) -> BulkExportJob
    def get_job(job_id) -> Optional[BulkExportJob]
    def cancel_job(job_id) -> bool          # False se COMPLETED/ERROR
    def get_ndjson(job_id, resource_type) -> Optional[str]
    def build_manifest(job, base_url) -> BulkExportManifest
    async def run_export(job_id, session_factory=None) -> None
```

**Tipos de recurso:**
- `DEFAULT_RESOURCE_TYPES` (sistema): Patient, Observation, Condition, MedicationRequest, AllergyIntolerance, Encounter, Procedure, DiagnosticReport
- `PATIENT_RESOURCE_TYPES` (compartimento Patient): Patient, Observation, Condition, MedicationRequest, AllergyIntolerance, Encounter, Procedure

**Graceful degradation:** `session_factory=None` → export concluído com dados vazios (correto para testes e ambiente sem DB)

---

## W7-B — CDS Hooks Feedback real + Prometheus

### Melhorias em `cds_hooks_routes.py`

**Antes:** endpoint `/feedback` era stub (204 sem processamento)

**Depois:**
- Feedback armazenado em `_feedback_store: dict[str, dict[str, int]]` (defaultdict)
- Outcomes válidos: `accepted`, `overridden`, `no-action`; outcomes inválidos mapeados para `unknown`
- Prometheus `Counter` opcional:
  - `cds_cards_generated_total` (labels: `service_id`, `indicator`) — incrementado no invoke
  - `cds_feedback_received_total` (labels: `service_id`, `outcome`) — incrementado no feedback
- Novo endpoint `GET /{service_id}/feedback-stats` → `{service_id, total_feedback, outcomes}`

```python
# Exemplo de resposta
{
    "service_id": "patient-view-alerts",
    "total_feedback": 5,
    "outcomes": {"accepted": 3, "overridden": 1, "no-action": 1}
}
```

---

## Testes

### intellicare-core — `tests/bulk/`

| Arquivo | Testes | Resultado |
|---------|--------|-----------|
| `test_bulk_models.py` | 8 | ✅ 8/8 |
| `test_bulk_manager.py` | 16 | ✅ 16/16 |
| **Total core** | **24** | **✅ 24/24** |

### intellicare-grahame — novos testes ONDA_7

| Arquivo | Testes | Resultado |
|---------|--------|-----------|
| `tests/test_bulk_export.py` | 13 | ✅ 13/13 |
| `tests/test_cds_feedback.py` | 10 | ✅ 10/10 |
| **Total grahame (novos)** | **23** | **✅ 23/23** |

**Suíte completa grahame:** 155/156 (1 falha pré-existente em `test_fhir_operations.py::test_summary_vital_signs_section` — LOINC 8716-3 vs 30954-2, não relacionada a ONDA_7)

### Padrão de teste adotado — minimal app fixture

Para evitar dependência do lifespan do grahame (que requer `aiosqlite` + DB), os testes usam apps mínimas:

```python
def _make_app(manager: BulkExportManager) -> FastAPI:
    _m._manager = manager  # injeta singleton
    app = FastAPI()
    app.include_router(bulk_router, prefix="/api/v1")
    return app

@pytest.fixture
def manager() -> BulkExportManager:
    fresh = BulkExportManager()
    fresh.run_export = _noop  # evita auto-completion por BackgroundTasks
    _m._manager = fresh
    yield fresh
    _m._manager = None
```

---

## Acumulado MEDPLUS_ON

| ONDA | Descrição | Testes adicionados |
|------|-----------|-------------------|
| ONDA_1..5 | Base FHIR, Auth, Terminologia, CDS Hooks, Smart | ~350 |
| ONDA_6 | WAHA webhook + Deploy/Versioning | +12 |
| **ONDA_7** | **Bulk Export + CDS Feedback** | **+47** |
| **TOTAL** | | **~409+ (grahame+core novos)** |

---

## Próximos passos sugeridos

1. **ONDA_8** — FHIR Questionnaire/QuestionnaireResponse (formulários clínicos)
2. **ONDA_9** — Audit Log persistente (AuditEvent FHIR) para rastreabilidade
3. **Deploy** — Testar docker compose up com todos os 13 módulos
4. **Bulk prod** — Migrar in-memory para Redis (jobs) + MinIO/S3 (NDJSON files)
