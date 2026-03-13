---
dem: DEM-005
titulo: Admin Backend — Especificação Técnica
tipo: TECNICA
status: aprovado
criado: 2026-03-13
---

# DEM-005 · 02 — Especificação Técnica

## Estrutura de arquivos

```
modules/
└── admin/
    ├── __init__.py
    ├── main.py              # class Module(BaseModule)
    ├── router.py            # FastAPI APIRouter com todos os endpoints
    ├── schemas.py           # Pydantic models (request/response)
    ├── service.py           # lógica de negócio (TenantService)
    ├── keycloak_client.py   # wrapper Keycloak Admin API
    └── migrations/
        └── 001_tenant_base.sql   # DDL executado ao provisionar novo tenant

db/
└── platform_migrations/
    └── 001_platform_tables.sql   # DDL para public.tenants + public.platform_audit_log
```

---

## BLOCO 1 — `db/platform_migrations/001_platform_tables.sql`

Executar uma única vez na inicialização do sistema (antes de qualquer tenant).
O `docker-compose.yml` pode montar este arquivo em `/docker-entrypoint-initdb.d/` ou
o `main.py` da aplicação pode rodá-lo na startup.

```sql
-- Tabela global de tenants
CREATE TABLE IF NOT EXISTS public.tenants (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    slug        TEXT        NOT NULL UNIQUE CHECK (slug ~ '^[a-z0-9_]{3,30}$'),
    name        TEXT        NOT NULL,
    status      TEXT        NOT NULL DEFAULT 'active'
                            CHECK (status IN ('active', 'suspended', 'terminated')),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Tabela global de auditoria de plataforma
CREATE TABLE IF NOT EXISTS public.platform_audit_log (
    id          BIGSERIAL   PRIMARY KEY,
    actor_id    TEXT        NOT NULL,
    actor_email TEXT,
    action      TEXT        NOT NULL,
    target_type TEXT,
    target_id   TEXT,
    payload     JSONB,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_audit_log_actor  ON public.platform_audit_log (actor_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_action ON public.platform_audit_log (action, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_tenants_slug     ON public.tenants (slug);
```

---

## BLOCO 2 — `modules/admin/migrations/001_tenant_base.sql`

DDL executado **dentro do schema do tenant** ao provisioná-lo.
O `TenantService.provision_schema()` injeta `search_path` antes de rodar.

```sql
-- Executado com search_path = tenant_{slug}

-- Tabela de usuários local do tenant (espelho leve do Keycloak)
CREATE TABLE IF NOT EXISTS users (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    keycloak_id TEXT        NOT NULL UNIQUE,
    email       TEXT        NOT NULL,
    name        TEXT        NOT NULL,
    role        TEXT        NOT NULL CHECK (role IN ('TENANT_GESTOR','CLINICO','PACIENTE')),
    active      BOOLEAN     NOT NULL DEFAULT true,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Tabela de base de conhecimento (RAG) — base vazia, populada pelo ingest pipeline
CREATE TABLE IF NOT EXISTS knowledge_base (
    id          BIGSERIAL   PRIMARY KEY,
    title       TEXT        NOT NULL,
    content     TEXT        NOT NULL,
    source_path TEXT,
    embedding   vector(768),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_kb_embedding
    ON knowledge_base USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);
```

---

## BLOCO 3 — `modules/admin/schemas.py`

```python
from __future__ import annotations
from datetime import datetime
from typing import Literal, Optional
from uuid import UUID
import re

from pydantic import BaseModel, field_validator, ConfigDict


SLUG_PATTERN = re.compile(r'^[a-z0-9_]{3,30}$')


# ---------------------------------------------------------------------------
# Tenant
# ---------------------------------------------------------------------------

class TenantCreate(BaseModel):
    slug: str
    name: str
    gestor_email: str  # será o primeiro usuário TENANT_GESTOR

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        if not SLUG_PATTERN.match(v):
            raise ValueError("slug deve ter 3-30 chars: [a-z0-9_]")
        return v

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if len(v.strip()) < 3:
            raise ValueError("name deve ter ao menos 3 caracteres")
        return v.strip()


class TenantStatusUpdate(BaseModel):
    status: Literal["active", "suspended"]


class TenantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    slug: str
    name: str
    status: str
    created_at: datetime
    updated_at: datetime


class TenantListResponse(BaseModel):
    items: list[TenantResponse]
    total: int
    page: int
    size: int


# ---------------------------------------------------------------------------
# Usuário (view do Keycloak)
# ---------------------------------------------------------------------------

class TenantUser(BaseModel):
    keycloak_id: str
    username: str
    email: str
    roles: list[str]
    enabled: bool


class TenantUsersResponse(BaseModel):
    tenant_slug: str
    users: list[TenantUser]
    total: int
```

---

## BLOCO 4 — `modules/admin/keycloak_client.py`

```python
"""Wrapper mínimo para Keycloak Admin REST API, usado pelo módulo admin."""
from __future__ import annotations

import os
from typing import Any

import httpx

KC_URL      = os.getenv("KEYCLOAK_URL",            "http://keycloak:8080")
KC_REALM    = os.getenv("KEYCLOAK_REALM",          "intellicare")
KC_CLIENT   = os.getenv("KEYCLOAK_CLIENT_ID",      "intellicare-service")
KC_SECRET   = os.getenv("KEYCLOAK_CLIENT_SECRET",  "")
KC_ADMIN    = os.getenv("KEYCLOAK_ADMIN",          "admin")
KC_ADMIN_PW = os.getenv("KEYCLOAK_ADMIN_PASSWORD", "admin")


class KeycloakAdminClient:
    """Client assíncrono para Keycloak Admin API."""

    def __init__(self) -> None:
        self._token: str | None = None

    async def _ensure_token(self) -> str:
        if self._token:
            return self._token
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{KC_URL}/realms/master/protocol/openid-connect/token",
                data={
                    "client_id":  "admin-cli",
                    "grant_type": "password",
                    "username":   KC_ADMIN,
                    "password":   KC_ADMIN_PW,
                },
                timeout=15,
            )
            resp.raise_for_status()
            self._token = resp.json()["access_token"]
        return self._token  # type: ignore[return-value]

    async def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {await self._ensure_token()}",
            "Content-Type":  "application/json",
        }

    async def create_tenant_group(self, slug: str) -> str:
        """Cria grupo tenant_{slug} no Keycloak e retorna seu ID."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{KC_URL}/admin/realms/{KC_REALM}/groups",
                json={"name": f"tenant_{slug}", "attributes": {"tenant_id": [slug]}},
                headers=await self._headers(),
                timeout=15,
            )
            resp.raise_for_status()
            return resp.headers["Location"].split("/")[-1]

    async def get_group_users(self, group_id: str) -> list[dict[str, Any]]:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{KC_URL}/admin/realms/{KC_REALM}/groups/{group_id}/members",
                headers=await self._headers(),
                timeout=15,
            )
            resp.raise_for_status()
            return resp.json()

    async def get_tenant_group_id(self, slug: str) -> str | None:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{KC_URL}/admin/realms/{KC_REALM}/groups?search=tenant_{slug}",
                headers=await self._headers(),
                timeout=15,
            )
            resp.raise_for_status()
            groups = [g for g in resp.json() if g["name"] == f"tenant_{slug}"]
            return groups[0]["id"] if groups else None
```

---

## BLOCO 5 — `modules/admin/service.py`

```python
"""TenantService — lógica de negócio do módulo admin."""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from intellicare_core.contracts.base import TenantContext
from intellicare_core.db.session import get_engine
from .keycloak_client import KeycloakAdminClient
from .schemas import TenantCreate, TenantStatusUpdate

logger = logging.getLogger("intellicare.admin.service")

# Caminho para a migration de schema de tenant
import pathlib
_TENANT_MIGRATION = (
    pathlib.Path(__file__).parent / "migrations" / "001_tenant_base.sql"
).read_text()


class TenantService:
    def __init__(self) -> None:
        self._kc = KeycloakAdminClient()

    # ------------------------------------------------------------------
    # Leitura
    # ------------------------------------------------------------------

    async def list_tenants(
        self,
        page: int,
        size: int,
        actor: TenantContext,
    ) -> tuple[list[dict], int]:
        async with get_engine().connect() as conn:
            count = (await conn.execute(
                text("SELECT COUNT(*) FROM public.tenants")
            )).scalar_one()
            rows = (await conn.execute(
                text("""
                    SELECT id, slug, name, status, created_at, updated_at
                    FROM public.tenants
                    ORDER BY created_at DESC
                    LIMIT :size OFFSET :offset
                """),
                {"size": size, "offset": (page - 1) * size},
            )).mappings().all()
        return [dict(r) for r in rows], count

    async def get_tenant(self, slug: str) -> dict | None:
        async with get_engine().connect() as conn:
            row = (await conn.execute(
                text("SELECT * FROM public.tenants WHERE slug = :slug"),
                {"slug": slug},
            )).mappings().first()
        return dict(row) if row else None

    async def get_tenant_users(self, slug: str) -> list[dict]:
        group_id = await self._kc.get_tenant_group_id(slug)
        if not group_id:
            return []
        return await self._kc.get_group_users(group_id)

    # ------------------------------------------------------------------
    # Escrita
    # ------------------------------------------------------------------

    async def create_tenant(
        self,
        payload: TenantCreate,
        actor: TenantContext,
    ) -> dict:
        """
        Cria tenant de forma transacional:
        1. Verifica slug livre
        2. CREATE SCHEMA + migrations
        3. Registra em public.tenants
        4. Cria grupo no Keycloak
        5. Auditoria
        """
        engine = get_engine()

        async with engine.begin() as conn:
            # 1. Verificar slug
            existing = (await conn.execute(
                text("SELECT 1 FROM public.tenants WHERE slug = :slug"),
                {"slug": payload.slug},
            )).first()
            if existing:
                raise ValueError(f"slug '{payload.slug}' já existe")

            # 2. Schema + migrations
            schema = f"tenant_{payload.slug}"
            await conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema}"'))
            await conn.execute(text(f'SET search_path TO "{schema}", public'))
            await conn.execute(text(_TENANT_MIGRATION))
            await conn.execute(text("SET search_path TO public"))

            # 3. Registrar tenant
            row = (await conn.execute(
                text("""
                    INSERT INTO public.tenants (slug, name)
                    VALUES (:slug, :name)
                    RETURNING id, slug, name, status, created_at, updated_at
                """),
                {"slug": payload.slug, "name": payload.name},
            )).mappings().first()
            tenant = dict(row)  # type: ignore[arg-type]

            # 4. Grupo Keycloak (fora da transação SQL, mas na mesma operação lógica)
            #    Se falhar → rollback do bloco `begin()`
            try:
                group_id = await self._kc.create_tenant_group(payload.slug)
                logger.info("Grupo Keycloak criado: %s (id=%s)", payload.slug, group_id)
            except Exception as exc:
                raise RuntimeError(f"Falha ao criar grupo no Keycloak: {exc}") from exc

            # 5. Auditoria
            await self._audit(conn, actor, "tenant.create", "tenant", payload.slug, {
                "name": payload.name,
                "gestor_email": payload.gestor_email,
            })

        logger.info("Tenant '%s' provisionado por %s", payload.slug, actor.user_id)
        return tenant

    async def update_status(
        self,
        slug: str,
        update: TenantStatusUpdate,
        actor: TenantContext,
    ) -> dict:
        async with get_engine().begin() as conn:
            row = (await conn.execute(
                text("""
                    UPDATE public.tenants
                    SET status = :status, updated_at = now()
                    WHERE slug = :slug
                    RETURNING id, slug, name, status, created_at, updated_at
                """),
                {"slug": slug, "status": update.status},
            )).mappings().first()

            if not row:
                raise LookupError(f"Tenant '{slug}' não encontrado")

            await self._audit(conn, actor, f"tenant.{update.status}", "tenant", slug, {
                "new_status": update.status,
            })

        return dict(row)

    # ------------------------------------------------------------------
    # Auditoria (privada)
    # ------------------------------------------------------------------

    async def _audit(
        self,
        conn: AsyncSession,  # pode ser uma conexão ou sessão
        actor: TenantContext,
        action: str,
        target_type: str,
        target_id: str,
        payload: dict,
    ) -> None:
        await conn.execute(
            text("""
                INSERT INTO public.platform_audit_log
                    (actor_id, actor_email, action, target_type, target_id, payload)
                VALUES
                    (:actor_id, :actor_email, :action, :target_type, :target_id, :payload::jsonb)
            """),
            {
                "actor_id":    actor.user_id,
                "actor_email": actor.email,
                "action":      action,
                "target_type": target_type,
                "target_id":   target_id,
                "payload":     json.dumps(payload),
            },
        )
```

---

## BLOCO 6 — `modules/admin/router.py`

```python
"""Admin Router — endpoints REST do módulo admin."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from intellicare_core.auth.jwt import require_role
from intellicare_core.contracts.base import TenantContext
from .schemas import (
    TenantCreate,
    TenantListResponse,
    TenantResponse,
    TenantStatusUpdate,
    TenantUsersResponse,
)
from .service import TenantService

router = APIRouter(prefix="/admin", tags=["admin"])
_service = TenantService()

AdminRequired = Annotated[TenantContext, Depends(require_role("PLATFORM_ADMIN"))]


@router.get("/health")
async def health() -> dict:
    return {"status": "healthy", "module": "admin", "version": "1.0.0"}


@router.get("/tenants", response_model=TenantListResponse)
async def list_tenants(
    actor: AdminRequired,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
) -> TenantListResponse:
    items, total = await _service.list_tenants(page, size, actor)
    return TenantListResponse(
        items=[TenantResponse(**i) for i in items],
        total=total,
        page=page,
        size=size,
    )


@router.get("/tenants/{slug}", response_model=TenantResponse)
async def get_tenant(slug: str, actor: AdminRequired) -> TenantResponse:
    tenant = await _service.get_tenant(slug)
    if not tenant:
        raise HTTPException(status_code=404, detail=f"Tenant '{slug}' não encontrado")
    return TenantResponse(**tenant)


@router.post("/tenants", response_model=TenantResponse, status_code=201)
async def create_tenant(
    payload: TenantCreate,
    actor: AdminRequired,
) -> TenantResponse:
    try:
        tenant = await _service.create_tenant(payload, actor)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return TenantResponse(**tenant)


@router.patch("/tenants/{slug}/status", response_model=TenantResponse)
async def update_tenant_status(
    slug: str,
    update: TenantStatusUpdate,
    actor: AdminRequired,
) -> TenantResponse:
    try:
        tenant = await _service.update_status(slug, update, actor)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return TenantResponse(**tenant)


@router.get("/tenants/{slug}/users", response_model=TenantUsersResponse)
async def list_tenant_users(slug: str, actor: AdminRequired) -> TenantUsersResponse:
    users = await _service.get_tenant_users(slug)
    mapped = [
        {
            "keycloak_id": u["id"],
            "username":    u.get("username", ""),
            "email":       u.get("email", ""),
            "roles":       u.get("realmRoles", []),
            "enabled":     u.get("enabled", True),
        }
        for u in users
    ]
    return TenantUsersResponse(tenant_slug=slug, users=mapped, total=len(mapped))
```

---

## BLOCO 7 — `modules/admin/main.py`

```python
"""Módulo Admin — ponto de entrada compatível com BaseModule."""
from __future__ import annotations

from fastapi import APIRouter

from intellicare_core.contracts.base import BaseModule, HealthResponse
from .router import router as admin_router


class Module(BaseModule):
    """Módulo de gestão de plataforma (PLATFORM_ADMIN only)."""

    @property
    def name(self) -> str:
        return "admin"

    @property
    def version(self) -> str:
        return "1.0.0"

    def get_router(self) -> APIRouter:
        return admin_router

    async def health(self) -> HealthResponse:
        return HealthResponse(
            status="healthy",
            module=self.name,
            version=self.version,
        )
```

---

## BLOCO 8 — `tests/admin/test_tenant_service.py`

```python
"""Testes unitários do TenantService."""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from modules.admin.schemas import TenantCreate, TenantStatusUpdate
from modules.admin.service import TenantService
from intellicare_core.contracts.base import TenantContext

# TenantContext fictício para actor nos testes
ADMIN_CTX = TenantContext(
    tenant_id="platform",
    schema="public",
    user_id="test-admin-id",
    roles=["PLATFORM_ADMIN"],
    email="admin@test.dev",
)


@pytest.mark.asyncio
async def test_create_tenant_slug_invalido():
    """Slug com caracteres inválidos deve falhar na validação Pydantic."""
    with pytest.raises(ValueError, match="slug"):
        TenantCreate(slug="Slug Inválido!", name="Teste", gestor_email="g@x.com")


@pytest.mark.asyncio
async def test_create_tenant_slug_curto():
    with pytest.raises(ValueError, match="slug"):
        TenantCreate(slug="ab", name="Teste", gestor_email="g@x.com")


@pytest.mark.asyncio
async def test_create_tenant_nome_curto():
    with pytest.raises(ValueError, match="name"):
        TenantCreate(slug="valid_slug", name="ab", gestor_email="g@x.com")


@pytest.mark.asyncio
@patch("modules.admin.service.get_engine")
@patch("modules.admin.service.KeycloakAdminClient")
async def test_create_tenant_slug_duplicado(mock_kc_cls, mock_engine):
    """Slug já existente deve levantar ValueError."""
    # Simula engine retornando slug existente
    mock_conn = AsyncMock()
    mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_conn.__aexit__ = AsyncMock(return_value=False)
    # execute retorna row (slug existe)
    mock_conn.execute = AsyncMock(return_value=MagicMock(first=MagicMock(return_value=("exists",))))

    mock_engine_inst = MagicMock()
    mock_engine_inst.begin = MagicMock(return_value=mock_conn)
    mock_engine.return_value = mock_engine_inst

    svc = TenantService()
    with pytest.raises(ValueError, match="já existe"):
        await svc.create_tenant(
            TenantCreate(slug="already_there", name="Dup Tenant", gestor_email="g@x.com"),
            ADMIN_CTX,
        )


@pytest.mark.asyncio
async def test_status_update_schema_invalido():
    """Status fora dos valores permitidos deve falhar no Pydantic."""
    with pytest.raises(ValueError):
        TenantStatusUpdate(status="deleted")  # type: ignore[arg-type]
```

---

## BLOCO 9 — Commit

```bash
git add modules/admin/ \
        db/platform_migrations/ \
        tests/admin/ \
        docs/demandas/DEM-005_ADMIN_BACKEND/

git commit -m "DEM-005: Admin Backend - CRUD tenants, provisioning schema, auditoria, Keycloak integration"
git push origin main
```

---

## Critérios de Aceite (técnicos)

| # | Critério | Verificação |
|---|---|---|
| AC-1 | POST `/admin/tenants` → schema criado | `SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'tenant_{slug}'` |
| AC-2 | POST com slug duplicado → 409 | `curl -X POST ... -d '{"slug":"dev",...}'` → HTTP 409 |
| AC-3 | POST com slug inválido → 422 | `slug="AB CD"` → HTTP 422 |
| AC-4 | Auditoria registrada | `SELECT * FROM public.platform_audit_log WHERE action = 'tenant.create'` |
| AC-5 | Rota sem token → 401 | `curl /admin/tenants` sem `Authorization` |
| AC-6 | Rota com token CLINICO → 403 | token de `clinico-dev` → HTTP 403 |
| AC-7 | `GET /admin/tenants` paginado | `?page=1&size=5` → campo `total` correto |
| AC-8 | `GET /admin/health` → 200 | `{"status":"healthy","module":"admin"}` |
| AC-9 | Testes unitários passam | `pytest tests/admin/ -v` sem erros |
