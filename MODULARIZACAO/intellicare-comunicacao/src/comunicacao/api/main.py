from fastapi import FastAPI
from intellicare_auth.fastapi import configure_auth
from .endpoints import router as comunicacao_router

app = FastAPI(title="IntelliCare Comunicação API", version="0.1.0")

# Configura autenticação IAM/Keycloak
configure_auth(app)

# Registra endpoints principais
app.include_router(comunicacao_router)

@app.get("/api/v1/health")
def health():
    return {"status": "ok"}
