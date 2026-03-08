from fastapi import Depends
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from intellicare_auth.fastapi import require_role

from admin.db.session import get_db

async def require_platform_admin(payload: Dict[str, Any] = require_role("PLATFORM_ADMIN")) -> Dict[str, Any]:
    """
    FastAPI Dependency: Ensures the user has the PLATFORM_ADMIN realm role.
    """
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
