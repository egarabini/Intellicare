from fastapi import FastAPI
from admin.api.v1 import tenants, billing, audit

app = FastAPI(
    title="IntelliCare Admin API",
    description="API para administração da plataforma IntelliCare",
    version="1.0.0",
)

app.include_router(tenants.router, prefix="/api/v1/admin", tags=["estabelecimentos"])
app.include_router(billing.router, prefix="/api/v1/admin", tags=["faturamento"])
app.include_router(audit.router, prefix="/api/v1/admin/auditoria", tags=["auditoria"])
