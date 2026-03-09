# 📋 W3-A — Especificação Funcional: FHIR-Native Storage

## 1. Objetivo
Criar um schema PostgreSQL que armazena recursos FHIR nativamente com versionamento, isolamento multi-tenant, e indexação otimizada, eliminando a camada de tradução entre modelos proprietários e FHIR.

## 2. Funcionalidades
- **Armazenamento FHIR nativo:** Recurso completo em JSONB com metadados estruturados
- **Versionamento:** Cada update cria nova versão (auditável, reversível)
- **History:** Endpoint `GET /fhir/Patient/{id}/_history` retorna todas as versões
- **Compartments:** Índices para Patient Compartment (busca por paciente)
- **Search Parameters:** Índices pré-calculados para campos buscáveis (GIN/BTREE)
- **Soft delete:** Recursos deletados mantêm histórico (status=deleted)

## 3. Schema Proposto

```sql
-- Tabela principal de recursos FHIR (uma para todos os tipos)
CREATE TABLE fhir_resources (
    id UUID PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    version_id UUID NOT NULL,
    resource JSONB NOT NULL,            -- Recurso FHIR completo
    last_updated TIMESTAMPTZ NOT NULL,
    author TEXT,                         -- Reference do autor
    compartments TEXT[],                 -- ["Patient/123", "Organization/abc"]
    is_deleted BOOLEAN DEFAULT false,
    
    UNIQUE(tenant_id, resource_type, id, version_id)
);

-- Histórico de versões
CREATE TABLE fhir_resource_history (
    id UUID,
    tenant_id TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    version_id UUID NOT NULL PRIMARY KEY,
    resource JSONB NOT NULL,
    last_updated TIMESTAMPTZ NOT NULL,
    author TEXT,
    interaction TEXT NOT NULL           -- create, update, delete
);

-- Índices para FHIR Search
CREATE INDEX idx_fhir_tenant_type ON fhir_resources(tenant_id, resource_type);
CREATE INDEX idx_fhir_compartment ON fhir_resources USING GIN(compartments);
CREATE INDEX idx_fhir_resource ON fhir_resources USING GIN(resource jsonb_path_ops);
CREATE INDEX idx_fhir_updated ON fhir_resources(tenant_id, resource_type, last_updated);
```

## 4. Referência Medplum
- `fhir/repo.ts` (107KB) — FHIR Repository
- `database.ts` — PostgreSQL pool + migrations

---

# 🔧 W3-A — Especificação Técnica

## Localização
```
intellicare-core/
└── intellicare_core/
    └── fhir_storage/                 # [NOVO]
        ├── __init__.py
        ├── models.py                 # SQLAlchemy models
        ├── repository.py             # FHIRRepository (CRUD + versioning)
        ├── history.py                # History endpoint
        ├── compartments.py           # Compartment indexing
        └── migrations/               # Alembic migrations
```

## FHIRRepository
```python
class FHIRRepository:
    async def create(self, tenant_id, resource) -> dict: ...
    async def read(self, tenant_id, resource_type, id) -> dict: ...
    async def update(self, tenant_id, resource_type, id, resource) -> dict: ...
    async def delete(self, tenant_id, resource_type, id) -> dict: ...
    async def history(self, tenant_id, resource_type, id) -> list: ...
    async def vread(self, tenant_id, resource_type, id, version_id) -> dict: ...
```

## Plano: 14 dias (Dev 1 + Dev 2)
- Dia 1-3: Models + migrations + basic CRUD
- Dia 4-6: Versionamento + history + vread
- Dia 7-9: Compartment indexing + GIN indexes
- Dia 10-12: Integration com Grahame endpoints
- Dia 13-14: Data migration tooling + testes
