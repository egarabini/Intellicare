"""FastAPI application bootstrap for intellicare-admin."""

from __future__ import annotations

import importlib
import logging
from typing import Any

from fastapi import FastAPI

logger = logging.getLogger(__name__)

app = FastAPI(
    title="IntelliCare Admin API",
    description="API para administracao da plataforma IntelliCare",
    version="1.0.0",
)


@app.get("/api/v1/health")
async def health() -> dict[str, Any]:
    """Liveness/readiness endpoint for container healthcheck."""
    return {"status": "healthy", "module": "intellicare-admin"}


@app.get("/api/v1/info")
async def info() -> dict[str, Any]:
    """Minimal module metadata."""
    return {
        "module": "intellicare-admin",
        "version": "1.0.0",
        "description": "Platform administration module",
    }


from admin.api.tenant_routes import router as tenant_router
# from admin.api.billing_routes import router as billing_router
# from admin.api.audit_routes import router as audit_router
# from admin.api.plan_routes import plan_router, dashboard_router

app.include_router(tenant_router, prefix="/api/v1")
# app.include_router(billing_router, prefix="/api/v1")
# app.include_router(audit_router, prefix="/api/v1")
# app.include_router(plan_router, prefix="/api/v1")
# app.include_router(dashboard_router, prefix="/api/v1")
