"""Exemplo completo de integração com FastAPI."""

from typing import Optional

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import JSONResponse

from intellicare_auth import (
    get_current_user,
    get_optional_user,
    get_user_roles,
    requires_any_role,
    requires_role,
)

# Criar aplicação FastAPI
app = FastAPI(
    title="IntelliCare Module Example",
    description="Exemplo de módulo IntelliCare com autenticação Keycloak",
    version="1.0.0",
)


# ============================================================================
# ENDPOINTS PÚBLICOS (sem autenticação)
# ============================================================================


@app.get("/")
async def root():
    """Endpoint raiz - público."""
    return {
        "service": "IntelliCare Module Example",
        "version": "1.0.0",
        "status": "healthy",
    }


@app.get("/health")
async def health():
    """Health check - público."""
    return {"status": "healthy"}


# ============================================================================
# ENDPOINTS COM AUTENTICAÇÃO OPCIONAL
# ============================================================================


@app.get("/api/public-data")
async def public_data(user: Optional[dict] = Depends(get_optional_user)):
    """
    Endpoint com autenticação opcional.
    Retorna dados personalizados se autenticado, dados públicos caso contrário.
    """
    if user:
        return {
            "data": "personalized content",
            "user": user.get("preferred_username"),
            "roles": get_user_roles(user),
        }
    
    return {"data": "public content"}


# ============================================================================
# ENDPOINTS PROTEGIDOS (requer autenticação)
# ============================================================================


@app.get("/api/profile")
async def get_profile(user: dict = Depends(get_current_user)):
    """
    Retorna perfil do usuário autenticado.
    Requer: Token válido
    """
    return {
        "username": user.get("preferred_username"),
        "email": user.get("email"),
        "email_verified": user.get("email_verified"),
        "name": user.get("name"),
        "roles": get_user_roles(user),
        "custom_attributes": {
            "hospital_id": user.get("hospital_id"),
            "specialty": user.get("specialty"),
            "license_number": user.get("license_number"),
            "department": user.get("department"),
        },
    }


@app.get("/api/data")
async def get_data(user: dict = Depends(get_current_user)):
    """
    Endpoint protegido - qualquer usuário autenticado.
    Requer: Token válido
    """
    return {
        "data": ["item1", "item2", "item3"],
        "user": user.get("preferred_username"),
        "timestamp": "2026-02-12T10:00:00Z",
    }


# ============================================================================
# ENDPOINTS COM CONTROLE DE ACESSO POR ROLE
# ============================================================================


@app.post("/api/admin/settings")
@requires_role("intellicare_admin")
async def update_settings(user: dict = Depends(get_current_user)):
    """
    Endpoint administrativo.
    Requer: Role 'intellicare_admin'
    """
    return {
        "message": "Settings updated successfully",
        "updated_by": user.get("preferred_username"),
    }


@app.post("/api/clinical/measurements")
@requires_any_role(["intellicare_doctor", "intellicare_nurse", "intellicare_nutritionist"])
async def create_measurement(user: dict = Depends(get_current_user)):
    """
    Criar medição clínica.
    Requer: Pelo menos uma role: doctor, nurse ou nutritionist
    """
    return {
        "message": "Measurement created",
        "created_by": user.get("preferred_username"),
        "role": get_user_roles(user)[0] if get_user_roles(user) else None,
    }


@app.get("/api/patients")
@requires_any_role(["intellicare_doctor", "intellicare_nurse"])
async def list_patients(user: dict = Depends(get_current_user)):
    """
    Listar pacientes.
    Requer: Role doctor ou nurse
    """
    hospital_id = user.get("hospital_id")
    
    return {
        "patients": [
            {"id": 1, "name": "Patient 1", "hospital_id": hospital_id},
            {"id": 2, "name": "Patient 2", "hospital_id": hospital_id},
        ],
        "hospital_id": hospital_id,
        "accessed_by": user.get("preferred_username"),
    }


# ============================================================================
# TRATAMENTO DE ERROS
# ============================================================================


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handler customizado para HTTPException."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
        },
    )


# ============================================================================
# EXECUTAR
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "fastapi_example:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )

