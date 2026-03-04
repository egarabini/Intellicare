from fastapi import Depends, Request
from typing import Dict, Any

from admin.api.middleware import require_platform_admin

def get_current_user(request: Request, _=Depends(require_platform_admin)) -> Dict[str, Any]:
    """
    Retorna usuário atual baseado no token JWT e `require_platform_admin`
    que já injeta o payload no state do Request.
    """
    return {
        "user_id": request.state.user_id,
        "email": request.state.user_email,
        "roles": request.state.user_roles
    }
