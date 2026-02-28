"""Decorators para controle de acesso baseado em roles."""

import logging
from functools import wraps
from typing import Any, Callable, Dict, List, Union

from fastapi import Depends, HTTPException, status

from intellicare_auth.middleware import get_current_user, get_user_roles

logger = logging.getLogger(__name__)


def requires_role(role: str) -> Callable:
    """
    Decorator que exige uma role específica.
    
    Args:
        role: Nome da role requerida
        
    Returns:
        Decorator function
        
    Raises:
        HTTPException: 403 se usuário não tem a role
        
    Exemplo:
        ```python
        @app.get("/api/admin")
        @requires_role("intellicare_admin")
        async def admin_endpoint(user: dict = Depends(get_current_user)):
            return {"message": "Admin access granted"}
        ```
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Obter usuário dos kwargs (injetado pelo Depends)
            user = kwargs.get("user")
            if not user:
                # Tentar obter de args (caso seja posicional)
                for arg in args:
                    if isinstance(arg, dict) and "sub" in arg:
                        user = arg
                        break
            
            if not user:
                logger.error("User not found in decorator context")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Erro interno: usuário não encontrado",
                )
            
            # Verificar role
            user_roles = get_user_roles(user)
            if role not in user_roles:
                logger.warning(
                    f"User {user.get('preferred_username')} missing required role: {role}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Role '{role}' requerida. Você tem: {', '.join(user_roles)}",
                )
            
            logger.debug(f"User {user.get('preferred_username')} has required role: {role}")
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def requires_any_role(roles: List[str]) -> Callable:
    """
    Decorator que exige pelo menos uma das roles especificadas.
    
    Args:
        roles: Lista de roles (usuário precisa ter pelo menos uma)
        
    Returns:
        Decorator function
        
    Raises:
        HTTPException: 403 se usuário não tem nenhuma das roles
        
    Exemplo:
        ```python
        @app.get("/api/clinical")
        @requires_any_role(["doctor", "nurse", "nutritionist"])
        async def clinical_endpoint(user: dict = Depends(get_current_user)):
            return {"message": "Clinical access granted"}
        ```
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Obter usuário dos kwargs
            user = kwargs.get("user")
            if not user:
                for arg in args:
                    if isinstance(arg, dict) and "sub" in arg:
                        user = arg
                        break
            
            if not user:
                logger.error("User not found in decorator context")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Erro interno: usuário não encontrado",
                )
            
            # Verificar se tem alguma das roles
            user_roles = get_user_roles(user)
            has_role = any(role in user_roles for role in roles)
            
            if not has_role:
                logger.warning(
                    f"User {user.get('preferred_username')} missing any of required roles: {roles}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Uma das roles requeridas: {', '.join(roles)}. Você tem: {', '.join(user_roles)}",
                )
            
            logger.debug(f"User {user.get('preferred_username')} has one of required roles")
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def requires_all_roles(roles: List[str]) -> Callable:
    """
    Decorator que exige TODAS as roles especificadas.
    
    Args:
        roles: Lista de roles (usuário precisa ter todas)
        
    Returns:
        Decorator function
        
    Raises:
        HTTPException: 403 se usuário não tem todas as roles
        
    Exemplo:
        ```python
        @app.get("/api/super-admin")
        @requires_all_roles(["admin", "superuser"])
        async def super_admin_endpoint(user: dict = Depends(get_current_user)):
            return {"message": "Super admin access granted"}
        ```
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            user = kwargs.get("user")
            if not user:
                for arg in args:
                    if isinstance(arg, dict) and "sub" in arg:
                        user = arg
                        break
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Erro interno: usuário não encontrado",
                )
            
            # Verificar se tem todas as roles
            user_roles = get_user_roles(user)
            missing_roles = [role for role in roles if role not in user_roles]
            
            if missing_roles:
                logger.warning(
                    f"User {user.get('preferred_username')} missing roles: {missing_roles}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Roles faltando: {', '.join(missing_roles)}",
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator

