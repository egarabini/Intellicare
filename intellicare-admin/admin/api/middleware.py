"""Middleware de autenticacao e autorizacao do Admin.
Valida o token JWT e garante que o usuario possua o role de administrador da plataforma.
"""

from fastapi import Request, HTTPException, Depends
try:
    from intellicare_auth.fastapi.middleware import verify_token
except ImportError:
    async def verify_token(token: str) -> dict: return {}

from fastapi.security import OAuth2PasswordBearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

async def require_platform_admin(request: Request, token: str = Depends(oauth2_scheme)):
    """FastAPI Dependency: Ensures user has ADMIN_PLATFORM role."""
    if not token:
        raise HTTPException(status_code=401, detail="Token ausente ou invalido.")
    
    try:
        payload = await verify_token(token)
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token invalido: {str(e)}")
        
    roles = payload.get("realm_access", {}).get("roles", [])
    
    # Check if user is a platform admin (Adjust based on exact Keycloak role naming for platform admin vs tenant admin)
    if "ADMIN" not in roles and "PLATFORM_ADMIN" not in roles:
        raise HTTPException(status_code=403, detail="Acesso negado. Requer privilegios de Administrador da Plataforma.")
        
    request.state.user_id = payload.get("sub")
    request.state.user_email = payload.get("email")
    request.state.user_roles = roles
    return True
