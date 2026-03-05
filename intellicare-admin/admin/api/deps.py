from fastapi import Depends, Request, HTTPException
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordBearer
from intellicare_auth.client import KeycloakClient
from intellicare_auth.exceptions import IntelliCareAuthError

from admin.db.session import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

# Re-use the KeycloakClient instance
kc_client = KeycloakClient()

async def require_platform_admin(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """
    FastAPI Dependency: Ensures the user has the PLATFORM_ADMIN realm role.
    """
    if not token:
        raise HTTPException(status_code=401, detail="Token ausente ou invalido.")

    try:
        payload = await kc_client.validate_token(token)
    except IntelliCareAuthError as e:
        raise HTTPException(status_code=401, detail=f"Token invalido: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Erro de autenticação: {str(e)}")

    roles = payload.get("realm_access", {}).get("roles", [])
    
    if "PLATFORM_ADMIN" not in roles and "admin" not in roles:
        raise HTTPException(
            status_code=403, 
            detail="Acesso negado. Requer privilegios de Administrador da Plataforma."
        )

    return payload

def get_current_user(payload: Dict[str, Any] = Depends(require_platform_admin)) -> Dict[str, Any]:
    return {
        "user_id": payload.get("sub", "anonymous"),
        "email": payload.get("email", ""),
        "roles": payload.get("realm_access", {}).get("roles", [])
    }

def get_actor_id(user: Dict[str, Any] = Depends(get_current_user)) -> str:
    return user["user_id"]

def get_tenant_service(session: AsyncSession = Depends(get_db)):
    from admin.services.tenant_service import TenantService
    return TenantService(session)

def get_provisioning_service(session: AsyncSession = Depends(get_db)):
    from admin.services.provisioning_service import ProvisioningService
    return ProvisioningService(session)
