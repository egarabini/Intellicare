from fastapi import FastAPI

from admin.api import audit_routes, billing_routes, plan_routes, tenant_routes

app = FastAPI(
    title="IntelliCare Admin API",
    description="API para administração da plataforma IntelliCare",
    version="1.0.0",
)

app.include_router(tenant_routes.router, prefix="/api/v1")
app.include_router(billing_routes.router, prefix="/api/v1")
app.include_router(audit_routes.router, prefix="/api/v1")
app.include_router(plan_routes.plan_router, prefix="/api/v1")
app.include_router(plan_routes.dashboard_router, prefix="/api/v1")
