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


def _safe_include_router(module_name: str, attr_name: str, prefix: str = "/api/v1") -> None:
    """
    Include a router only when import succeeds.
    Keeps admin service online even if a specific route module is temporarily broken.
    """
    try:
        module = importlib.import_module(module_name)
        router = getattr(module, attr_name)
        app.include_router(router, prefix=prefix)
        logger.info("Router loaded: %s.%s", module_name, attr_name)
    except Exception as exc:  # pragma: no cover - defensive startup guard
        logger.warning("Router disabled: %s.%s (%s)", module_name, attr_name, exc)


# Optional routers (best effort)
_safe_include_router("admin.api.tenant_routes", "router")
_safe_include_router("admin.api.billing_routes", "router")
_safe_include_router("admin.api.audit_routes", "router")
_safe_include_router("admin.api.plan_routes", "plan_router")
_safe_include_router("admin.api.plan_routes", "dashboard_router")
