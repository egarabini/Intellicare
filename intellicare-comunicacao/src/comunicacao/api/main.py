from fastapi import FastAPI

# Integração intellicare-auth (opcional)
try:
    from intellicare_auth.fastapi import configure_auth
    AUTH_AVAILABLE = True
except ImportError:
    AUTH_AVAILABLE = False

from .endpoints import router as comunicacao_router

app = FastAPI(title="IntelliCare Comunicação API", version="0.1.0")

# Configura autenticação IAM/Keycloak (se disponível)
if AUTH_AVAILABLE:
    configure_auth(app)

# Registra endpoints principais
app.include_router(comunicacao_router)

@app.get("/api/v1/health")
def health():
    return {"status": "ok", "auth_enabled": AUTH_AVAILABLE}

