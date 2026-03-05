from fastapi import Depends, Request
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from admin.api.middleware import require_platform_admin
from admin.db.session import get_db

def get_current_user(request: Request, _=Depends(require_platform_admin)) -> Dict[str, Any]:
    """
    Retorna usuário atual baseado no token JWT e `require_platform_admin`
    que já injeta o payload no state do Request.
    """
    return {
        "user_id": getattr(request.state, "user_id", "anonymous"),
        "email": getattr(request.state, "user_email", ""),
        "roles": getattr(request.state, "user_roles", [])
    }

def get_actor_id(user: Dict[str, Any] = Depends(get_current_user)) -> str:
    return user["user_id"]

def get_tenant_service(session: AsyncSession = Depends(get_db)):
    from admin.services.tenant_service import TenantService
    return TenantService(session)

def get_provisioning_service(session: AsyncSession = Depends(get_db)):
    from admin.services.provisioning_service import ProvisioningService
    return ProvisioningService(session)
