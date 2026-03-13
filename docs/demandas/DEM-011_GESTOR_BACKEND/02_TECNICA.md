---
dem: DEM-011
titulo: Gestor Backend — Especificação Técnica
tipo: TECNICA
status: aprovado
criado: 2026-03-13
---

# DEM-011 · 02 — Especificação Técnica

## Estrutura

```
modules/gestor/
├── __init__.py
├── main.py
├── router.py
├── schemas.py
└── service.py

db/tenant_migrations/
└── 003_gestor_tables.sql
```

## BLOCO 1 — `db/tenant_migrations/003_gestor_tables.sql`

```sql
CREATE TABLE IF NOT EXISTS unit_profile (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    name        TEXT        NOT NULL,
    address     TEXT,
    city        TEXT,
    state       CHAR(2),
    unit_type   TEXT        DEFAULT 'clinic'
                            CHECK (unit_type IN ('ubs','clinic','hospital','specialty')),
    phone       TEXT,
    email       TEXT,
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS slm_query_log (
    id          BIGSERIAL   PRIMARY KEY,
    user_id     TEXT        NOT NULL,
    query_text  TEXT        NOT NULL,
    latency_ms  INTEGER,
    chunk_count INTEGER,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_slm_log_created ON slm_query_log (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_slm_log_user    ON slm_query_log (user_id, created_at DESC);
```

## BLOCO 2 — `modules/gestor/schemas.py`

```python
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

class UnitProfile(BaseModel):
    name: str
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    unit_type: Literal["ubs","clinic","hospital","specialty"] = "clinic"
    phone: Optional[str] = None
    email: Optional[str] = None

class UnitProfileResponse(UnitProfile):
    id: UUID
    updated_at: datetime

class InviteUserRequest(BaseModel):
    email: EmailStr
    name: str
    role: Literal["CLINICO","PACIENTE"]

class DocumentInfo(BaseModel):
    source_path: str
    chunk_count: int
    last_ingested_at: datetime

class UsageReport(BaseModel):
    period_start: datetime
    period_end: datetime
    total_queries: int
    avg_latency_ms: float
    top_queries: list[str]
```

## BLOCO 3 — `modules/gestor/service.py` (principais métodos)

```python
from sqlalchemy import text
from intellicare_core.contracts.base import TenantContext
from intellicare_core.db.session import tenant_session
from modules.admin.keycloak_client import KeycloakAdminClient
import os, httpx, logging

KC_URL   = os.getenv("KEYCLOAK_URL",   "http://keycloak:8080")
KC_REALM = os.getenv("KEYCLOAK_REALM", "intellicare")
logger   = logging.getLogger("intellicare.gestor.service")

class GestorService:
    def __init__(self): self._kc = KeycloakAdminClient()

    async def get_profile(self, ctx):
        async with tenant_session(ctx) as db:
            row = (await db.execute(text("SELECT * FROM unit_profile LIMIT 1"))).mappings().first()
        return dict(row) if row else None

    async def upsert_profile(self, ctx, data):
        async with tenant_session(ctx) as db:
            exists = (await db.execute(text("SELECT id FROM unit_profile LIMIT 1"))).first()
            if exists:
                row = (await db.execute(text(
                    "UPDATE unit_profile SET name=:name,address=:address,city=:city,"
                    "state=:state,unit_type=:unit_type,phone=:phone,email=:email,updated_at=now() RETURNING *"), data
                )).mappings().first()
            else:
                row = (await db.execute(text(
                    "INSERT INTO unit_profile (name,address,city,state,unit_type,phone,email) "
                    "VALUES (:name,:address,:city,:state,:unit_type,:phone,:email) RETURNING *"), data
                )).mappings().first()
        return dict(row)

    async def list_documents(self, ctx):
        async with tenant_session(ctx) as db:
            rows = (await db.execute(text(
                "SELECT source_path, COUNT(*) AS chunk_count, MAX(created_at) AS last_ingested_at "
                "FROM knowledge_base GROUP BY source_path ORDER BY last_ingested_at DESC"
            ))).mappings().all()
        return [dict(r) for r in rows]

    async def usage_report(self, ctx, days=30):
        async with tenant_session(ctx) as db:
            row = (await db.execute(text("""
                SELECT COUNT(*) AS total_queries,
                       COALESCE(AVG(latency_ms),0) AS avg_latency_ms,
                       MIN(created_at) AS period_start,
                       MAX(created_at) AS period_end
                FROM slm_query_log
                WHERE created_at >= now() - make_interval(days => :days)
            """), {"days": days})).mappings().first()
            top = (await db.execute(text("""
                SELECT query_text FROM slm_query_log
                WHERE created_at >= now() - make_interval(days => :days)
                GROUP BY query_text ORDER BY COUNT(*) DESC LIMIT 5
            """), {"days": days})).fetchall()
        return {**dict(row), "top_queries": [r[0] for r in top]}
```

## BLOCO 4 — `modules/gestor/router.py`

```python
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from intellicare_core.auth.jwt import require_role, get_current_tenant
from intellicare_core.contracts.base import TenantContext
from modules.vector.ingest_service import IngestService
from .schemas import InviteUserRequest, UnitProfile
from .service import GestorService
from typing import Annotated
import os, tempfile

router = APIRouter(prefix="/gestor", tags=["gestor"])
_svc = GestorService(); _ingest = IngestService()
GestorOnly = Annotated[TenantContext, Depends(require_role("TENANT_GESTOR"))]
AnyUser    = Annotated[TenantContext, Depends(get_current_tenant)]

@router.get("/health")
async def health(): return {"status":"healthy","module":"gestor","version":"1.0.0"}

@router.get("/profile")
async def get_profile(ctx: AnyUser):
    p = await _svc.get_profile(ctx)
    if not p: raise HTTPException(404, "Perfil não configurado")
    return p

@router.put("/profile")
async def update_profile(payload: UnitProfile, ctx: GestorOnly):
    return await _svc.upsert_profile(ctx, payload.model_dump())

@router.get("/users")
async def list_users(ctx: GestorOnly):
    from modules.admin.keycloak_client import KeycloakAdminClient
    kc = KeycloakAdminClient()
    gid = await kc.get_tenant_group_id(ctx.tenant_id)
    return await kc.get_group_users(gid) if gid else []

@router.get("/documents")
async def list_documents(ctx: GestorOnly): return await _svc.list_documents(ctx)

@router.post("/documents/upload")
async def upload_document(file: UploadFile = File(...), ctx: GestorOnly = Depends(require_role("TENANT_GESTOR"))):
    suffix = "." + (file.filename or "doc.txt").rsplit(".",1)[-1]
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(await file.read()); tmp_path = tmp.name
    try:
        return await _ingest.ingest_file(tmp_path, ctx, source_label=file.filename)
    finally:
        os.unlink(tmp_path)

@router.delete("/documents/{source_path:path}")
async def delete_document(source_path: str, ctx: GestorOnly):
    return {"deleted_chunks": await _ingest.delete_document(source_path, ctx)}

@router.get("/reports/usage")
async def usage_report(ctx: GestorOnly, days: int = 30):
    return await _svc.usage_report(ctx, days)
```

## BLOCO 5 — Commit

```bash
git add modules/gestor/ db/tenant_migrations/003_gestor_tables.sql docs/demandas/DEM-011_GESTOR_BACKEND/
git commit -m "DEM-011: Gestor Backend - perfil unidade, usuarios Keycloak, documentos RAG, relatorio"
git push origin main
```
