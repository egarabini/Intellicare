# GRAHAME — Especificacoes Tecnicas
**Data:** 2026-03-04
**Versao:** 1.0.0
**Modulo:** intellicare-grahame (porta 8012)

---

## 1. Stack Tecnologica

| Componente | Tecnologia |
|-----------|-----------|
| Runtime | Python 3.11 |
| Framework | FastAPI |
| ORM | SQLAlchemy 2.x async |
| Banco | PostgreSQL 15 (JSONB para recursos FHIR) |
| Auth | intellicare-auth (Keycloak/JWT) |
| Multi-tenant | intellicare-core TenantContext |
| Testes | pytest + pytest-asyncio + aiosqlite (CI) |

---

## 2. Schema do Banco de Dados

```sql
-- Tabela generica para todos os recursos FHIR
CREATE TABLE fhir_resources (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fhir_id     VARCHAR(64) UNIQUE NOT NULL,    -- id do recurso FHIR
    resource_type VARCHAR(64) NOT NULL,          -- Patient, Observation, etc
    resource     JSONB NOT NULL,                 -- recurso completo serializado
    tenant_id    VARCHAR(64) NOT NULL,
    patient_id   VARCHAR(64),                    -- denormalizacao para busca rapida
    created_at   TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at   TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at   TIMESTAMP WITH TIME ZONE       -- soft delete
);

CREATE INDEX idx_fhir_type_patient ON fhir_resources(resource_type, patient_id);
CREATE INDEX idx_fhir_tenant ON fhir_resources(tenant_id);
CREATE INDEX idx_fhir_resource_gin ON fhir_resources USING GIN(resource jsonb_path_ops);
```

---

## 3. Endpoints API

```
# Padrao BaseAgent
GET  /api/v1/health
GET  /api/v1/info
POST /api/v1/analyze

# FHIR R4 REST API
GET    /api/v1/Patient                    → Bundle (search)
POST   /api/v1/Patient                    → Patient (create)
GET    /api/v1/Patient/{id}               → Patient (read)
PUT    /api/v1/Patient/{id}               → Patient (update)
DELETE /api/v1/Patient/{id}               → 204 (soft delete)
GET    /api/v1/Patient/{id}/$everything   → Bundle (summary)

GET    /api/v1/Observation                → Bundle
POST   /api/v1/Observation                → Observation
GET    /api/v1/Observation/{id}           → Observation

GET    /api/v1/Condition                  → Bundle
POST   /api/v1/Condition                  → Condition
GET    /api/v1/Condition/{id}             → Condition

GET    /api/v1/MedicationRequest          → Bundle
POST   /api/v1/MedicationRequest          → MedicationRequest

# CDS Hooks
GET    /cds-services                      → discovery endpoint
POST   /cds-services/patient-view         → cards response
POST   /cds-services/order-sign           → cards response
```

---

## 4. Padroes de Implementacao

### 4.1 Rota Generica FHIR
```python
# grahame/api/routes/fhir_generic.py
# Rota parametrizada que serve qualquer resource_type
router = APIRouter(prefix="/api/v1")

@router.get("/{resource_type}")
async def search_resource(
    resource_type: str,
    patient: Optional[str] = Query(None, alias="patient"),
    db: AsyncSession = Depends(get_db),
    tenant: TenantContext = Depends(get_tenant)
) -> dict:  # FHIR Bundle
    ...

@router.post("/{resource_type}")
async def create_resource(
    resource_type: str,
    resource: dict,
    db: AsyncSession = Depends(get_db),
    tenant: TenantContext = Depends(get_tenant)
) -> dict:  # FHIR Resource
    ...
```

### 4.2 FHIR Bundle Builder
```python
# grahame/fhir/bundle.py
def build_bundle(resources: list[dict], total: int,
                 bundle_type: str = "searchset") -> dict:
    return {
        "resourceType": "Bundle",
        "type": bundle_type,
        "total": total,
        "entry": [
            {"resource": r, "fullUrl": f"urn:uuid:{r['id']}"}
            for r in resources
        ]
    }
```

---

## 5. Configuracao

```env
DATABASE_URL=postgresql+asyncpg://intellicare:password@localhost:5432/intellicare
REDIS_URL=redis://redis:6379/0
PORT=8000   # externo: 8012
TENANT_HEADER=X-Tenant-ID
ENABLE_CDS_HOOKS=true
LOG_LEVEL=INFO
```

---

## 6. Testes

```python
# Estrategia: aiosqlite in-memory para CI (nao requer PostgreSQL)

# test_patient_routes.py
test_create_patient_retorna_201()
test_get_patient_por_id()
test_search_patient_por_nome()
test_delete_patient_soft_delete()
test_patient_everything_bundle()

# test_observation_routes.py
test_create_observation_laboratorial()
test_search_observation_por_patient()
test_search_observation_por_codigo_loinc()

# test_cds_hooks.py
test_patient_view_hook_retorna_cards()
test_order_sign_alerta_contraindicacao()
```

---

*GRAHAME v2.0 — Especificacoes Tecnicas — 2026-03-04*
