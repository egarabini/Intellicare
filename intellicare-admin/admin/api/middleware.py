from fastapi import Request, HTTPException, status
import logging

logger = logging.getLogger(__name__)

async def require_platform_admin(request: Request):
    """
    Middleware para validar JWT e requer role PLATFORM_ADMIN
    Esta função é utilizada nas rotas e precisa do intellicare_auth instalado.
    Para os propósitos deste esqueleto, ela usa o intellicare_auth fictício.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header"
        )

    token = auth_header.split(" ")[1]

    try:
        # Mock do validate_token enquanto intellicare_auth não está presente ou testando local
        # payload = await validate_token(token)
        # Para fins de simulação/smoke test da implementação:
        payload = {
            "realm_access": {"roles": ["PLATFORM_ADMIN"]},
            "sub": "00000000-0000-0000-0000-000000000000",
            "email": "admin@intellicare.ia.br"
        }
        
        roles = payload.get("realm_access", {}).get("roles", [])

        if "PLATFORM_ADMIN" not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="PLATFORM_ADMIN role required"
            )

        # Adiciona user info ao request state
        request.state.user_id = payload.get("sub")
        request.state.user_email = payload.get("email")
        request.state.user_roles = roles

    except Exception as e:
        logger.error(f"Token validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
