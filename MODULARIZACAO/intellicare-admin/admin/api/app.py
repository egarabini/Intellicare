"""FastAPI application factory for intellicare-admin."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from admin.config import AdminConfig
from admin.api.tenant_routes import router as tenant_router
from admin.api.plan_routes import plan_router, dashboard_router
from admin.api.billing_routes import router as billing_router
from admin.api.audit_routes import router as audit_router

# Auth integration (optional)
try:
    from intellicare_auth.fastapi import configure_auth
    AUTH_AVAILABLE = True
except ImportError:
    AUTH_AVAILABLE = False

logger = logging.getLogger(__name__)

config = AdminConfig()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Startup: create engine, sessionmaker. Shutdown: dispose."""

    # Database
    engine = create_async_engine(
        config.database_url,
        echo=False,
        pool_size=10,
        max_overflow=5,
    )
    app.state.engine = engine
    app.state.sessionmaker = async_sessionmaker(engine, expire_on_commit=False)

    # Keycloak admin client (optional)
    try:
        from keycloak import KeycloakAdmin
        app.state.kc_admin = KeycloakAdmin(
            server_url=config.keycloak_admin_url,
            username=config.keycloak_admin_username,
            password=config.keycloak_admin_password,
            realm_name=config.keycloak_target_realm,
        )
        logger.info("Keycloak admin client initialized")
    except (ImportError, Exception) as e:
        app.state.kc_admin = None
        logger.warning("Keycloak admin not available: %s", e)

    logger.info(
        "intellicare-admin v%s started (schema=%s, auth=%s, keycloak=%s)",
        config.module_version,
        config.platform_schema,
        AUTH_AVAILABLE,
        app.state.kc_admin is not None,
    )

    yield  # Application runs

    # Shutdown
    await engine.dispose()
    logger.info("intellicare-admin shutdown")


app = FastAPI(
    title="IntelliCare Admin",
    description="Platform administration — tenant management, billing, monitoring",
    version=config.module_version,
    lifespan=lifespan,
)

# Auth
if AUTH_AVAILABLE:
    configure_auth(app)

# Routes
app.include_router(tenant_router)
app.include_router(plan_router)
app.include_router(dashboard_router)
app.include_router(billing_router)
app.include_router(audit_router)


# ── Health & Info ─────────────────────────────────────────────

@app.get("/api/v1/health")
async def health():
    return {
        "status": "healthy",
        "module_name": config.module_name,
        "version": config.module_version,
        "auth_enabled": AUTH_AVAILABLE,
    }


@app.get("/api/v1/info")
async def info():
    return {
        "name": config.module_name,
        "version": config.module_version,
        "description": "Platform administration — SaaS tenant management",
        "capabilities": ["tenant-management", "billing", "provisioning", "audit"],
    }
