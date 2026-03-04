from functools import wraps
from fastapi import HTTPException, status, Request
import logging

logger = logging.getLogger(__name__)

def require_permission(required_permission: str):
    """
    Decorator para verificar se o usuário no Request possui permissão via RBAC.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request: Request = kwargs.get("request")
            if not request:
                # Find request in args if not in kwargs (FastAPI injects it if annotated)
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break

            if not request:
                logger.warning("require_permission decorator used without taking Request dependency.")
                raise HTTPException(status_code=500, detail="Internal server error")

            # Em produção isso vira de uma validação de cache ou serviço real
            # Mock para testes locais (simplificamos já que depende do get_tenant_context)
            user_permissions = getattr(request.state, "user_permissions", [])

            # Check for global admin wildcard
            if "*" in user_permissions:
                return await func(*args, **kwargs)

            # Check specific permission or modular wildcard (e.g. "oswaldo.*")
            module = required_permission.split(".")[0]
            if required_permission not in user_permissions and f"{module}.*" not in user_permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permissão '{required_permission}' requerida."
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator
