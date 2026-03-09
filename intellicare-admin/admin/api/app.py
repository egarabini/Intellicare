"""FastAPI application bootstrap for intellicare-admin."""

from __future__ import annotations

import importlib
import logging
import os
import uuid
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from intellicare_auth.fastapi import configure_auth
from intellicare_core.tenant.startup import init_tenant_resolver
from sqlalchemy import text

from admin.api.middleware import AuthMiddleware
from admin.db.session import session_factory
from admin.models import Base

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: create tables, set session_factory."""
    init_tenant_resolver()
    app.state.session_factory = session_factory
    try:
        async with session_factory.engine.begin() as conn:
            schema = os.getenv("DB_SCHEMA", "platform")
            if schema:
                await conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema}"'))
            await conn.run_sync(Base.metadata.create_all)
            if schema:
                await conn.execute(
                    text(
                        f"""
                        INSERT INTO "{schema}".plan
                            (id, name, display_name, max_users, max_sms_month, price_monthly, modules_included, active)
                        VALUES
                            (:id, 'trial', 'Trial', 50, 0, 0, '[]'::json, true)
                        ON CONFLICT (name) DO NOTHING
                        """
                    ),
                    {"id": str(uuid.uuid4())},
                )
    except Exception as e:
        logger.warning("create_all skipped or failed: %s", e)
    yield


app = FastAPI(
    title="IntelliCare Admin API",
    description="API para administracao da plataforma IntelliCare",
    version="1.0.0",
    lifespan=lifespan,
)
configure_auth(app, secrets_path="keycloak_client_secrets.json")
app.add_middleware(AuthMiddleware)


@app.get("/api/v1/health")
async def health() -> dict[str, Any]:
    """Liveness/readiness endpoint for container healthcheck."""
    return {"status": "healthy", "module": "intellicare-admin"}


from pathlib import Path

from fastapi.responses import HTMLResponse, FileResponse

_TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


@app.get("/", include_in_schema=False)
async def admin_portal_root():
    """Dashboard do IntelliCare Admin — login Keycloak + CRUD Estabelecimentos/Secretarias."""
    dashboard_path = _TEMPLATES_DIR / "dashboard.html"
    if dashboard_path.exists():
        return FileResponse(dashboard_path, media_type="text/html")
    return HTMLResponse(content="<h1>IntelliCare Admin</h1><p>Template nao encontrado.</p>")


@app.get("/api/v1/info")
async def info() -> dict[str, Any]:
    """Minimal module metadata."""
    return {
        "module": "intellicare-admin",
        "version": "1.0.0",
        "description": "Platform administration module",
    }


from admin.api.tenant_routes import router as tenant_router
from admin.api.billing_routes import router as billing_router
from admin.api.audit_routes import router as audit_router
from admin.api.plan_routes import plan_router, dashboard_router
from admin.api.gestor_routes import router as gestor_router
from admin.api.contrato_routes import router as contrato_router
from admin.api.estabelecimento_routes import router as estabelecimento_router
from admin.api.secretaria_routes import router as secretaria_router
from admin.api.module_probe_routes import router as probe_router
from admin.api.module_test_routes import router as test_router

app.include_router(probe_router, prefix="/api/v1")
app.include_router(test_router, prefix="/api/v1")
app.include_router(tenant_router, prefix="/api/v1")
app.include_router(billing_router, prefix="/api/v1")
app.include_router(audit_router, prefix="/api/v1")
app.include_router(plan_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(gestor_router, prefix="/api/v1/admin")
app.include_router(contrato_router, prefix="/api/v1/admin")
app.include_router(estabelecimento_router, prefix="/api/v1")
app.include_router(secretaria_router, prefix="/api/v1")
