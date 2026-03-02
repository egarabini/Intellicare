"""Configure Keycloak auth for FastAPI applications.

Usage::

    from intellicare_auth.fastapi import configure_auth, require_role
    from fastapi import FastAPI, Depends

    app = FastAPI()
    configure_auth(app, secrets_path="keycloak_client_secrets.json")

    @app.get("/protected")
    async def protected(user: dict = Depends(require_role("HEALTH_PROFESSIONAL"))):
        return {"user": user["preferred_username"]}
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, status

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# configure_auth
# ---------------------------------------------------------------------------

def configure_auth(
    app: FastAPI,
    secrets_path: str = "keycloak_client_secrets.json",
    public_routes: Optional[list[str]] = None,
) -> None:
    """Configure Keycloak authentication for a FastAPI application.

    Reads ``secrets_path`` (JSON) and sets ``KEYCLOAK_*`` env vars so that
    :class:`intellicare_auth.KeycloakClient` can initialise.  Env vars that
    are already set always take precedence over the file.

    Args:
        app: The FastAPI application instance.
        secrets_path: Path to ``keycloak_client_secrets.json``.
        public_routes: Informational list of public route prefixes (auth is
            enforced per-route via ``Depends``, not via middleware here).
    """
    _load_secrets_file(secrets_path)

    # Eagerly validate the config so start-up fails fast instead of on the
    # first request.
    try:
        from intellicare_auth.middleware import get_keycloak_client  # noqa: PLC0415
        get_keycloak_client()
        logger.info("configure_auth: KeycloakClient ready (realm=%s)", os.environ.get("KEYCLOAK_REALM", "?"))
    except Exception as exc:
        logger.warning("configure_auth: Keycloak unavailable — auth disabled: %s", exc)


def _load_secrets_file(secrets_path: str) -> None:
    """Read secrets JSON and populate missing KEYCLOAK_* env vars."""
    p = Path(secrets_path)
    if not p.exists():
        logger.debug("configure_auth: secrets file not found: %s", secrets_path)
        return

    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        web = data.get("web", {})

        _setenv("KEYCLOAK_CLIENT_ID", web.get("client_id"))
        _setenv("KEYCLOAK_CLIENT_SECRET", web.get("client_secret"))

        # Derive server_url and realm from issuer, e.g.
        # https://auth.intellicare.ia.br/realms/bemcuidar
        issuer: str = web.get("issuer", "")
        if issuer:
            parts = issuer.rstrip("/").split("/realms/")
            if len(parts) == 2:
                _setenv("KEYCLOAK_SERVER_URL", parts[0])
                _setenv("KEYCLOAK_REALM", parts[1])

        logger.info("configure_auth: loaded secrets from %s (client_id=%s)",
                    secrets_path, web.get("client_id"))
    except Exception as exc:
        logger.warning("configure_auth: could not read secrets file %s: %s", secrets_path, exc)


def _setenv(key: str, value: Optional[str]) -> None:
    """Set an env var only when it is not already set and value is not empty."""
    if value and not os.environ.get(key):
        os.environ[key] = value


# ---------------------------------------------------------------------------
# require_role — FastAPI Depends factory
# ---------------------------------------------------------------------------

def require_role(role: str):
    """Return a FastAPI dependency that enforces a realm role.

    Usage::

        @router.delete("/users/{user_id}")
        async def delete_user(
            user_id: str,
            current_user: dict = Depends(require_role("PLATFORM_ADMIN")),
        ):
            ...
    """
    from intellicare_auth.middleware import get_current_user, get_user_roles  # noqa: PLC0415

    async def _check(user: dict = Depends(get_current_user)) -> dict:
        roles = get_user_roles(user)
        if role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role}' required. You have: {', '.join(roles) or 'none'}",
            )
        return user

    return Depends(_check)


def require_any_role(roles: list[str]):
    """Return a FastAPI dependency that enforces at least one of the given roles."""
    from intellicare_auth.middleware import get_current_user, get_user_roles  # noqa: PLC0415

    async def _check(user: dict = Depends(get_current_user)) -> dict:
        user_roles = get_user_roles(user)
        if not any(r in user_roles for r in roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"One of {roles} required. You have: {', '.join(user_roles) or 'none'}",
            )
        return user

    return Depends(_check)

