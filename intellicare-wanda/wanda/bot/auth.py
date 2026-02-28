"""Bot auth middleware — validates Keycloak roles per command (EF-W012)."""

from __future__ import annotations

import logging
from typing import Any, Optional

from wanda.bot.models import AuthResult, BotCommand

logger = logging.getLogger(__name__)

# Commands that require elevated roles (empty = all authenticated users can run)
COMMAND_ROLES: dict[BotCommand, list[str]] = {
    BotCommand.PACIENTE: ["medico", "enfermeiro", "farmaceutico", "admin"],
    BotCommand.GUIDELINE: ["medico", "enfermeiro", "farmaceutico", "admin"],
    BotCommand.RESUMO: ["medico", "enfermeiro", "admin"],
    BotCommand.ALERTA: ["medico", "enfermeiro", "admin"],
    BotCommand.TELECONSULTA: ["medico", "enfermeiro", "admin"],
    BotCommand.AJUDA: [],   # anyone
    BotCommand.STATUS: ["admin"],
}


class BotAuthMiddleware:
    """Checks Keycloak token roles for each bot command.

    If Keycloak URL is not configured, falls back to allow-all mode
    (useful for development / local testing).
    """

    def __init__(
        self,
        keycloak_url: Optional[str] = None,
        realm: str = "bemcuidar",
        http_client: Optional[Any] = None,
    ) -> None:
        self._keycloak_url = keycloak_url
        self._realm = realm
        self._http = http_client
        self._enabled = bool(keycloak_url)

    async def authorize(
        self, command: BotCommand, user_id: str, rc_token: Optional[str] = None
    ) -> AuthResult:
        """Return AuthResult with authorized=True/False and user roles."""
        required_roles = COMMAND_ROLES.get(command, [])

        if not required_roles:
            return AuthResult(authorized=True, reason="comando publico")

        if not self._enabled:
            logger.debug("Auth disabled — allowing command %s for %s", command, user_id)
            return AuthResult(authorized=True, reason="auth desabilitado (dev mode)")

        try:
            roles = await self._fetch_roles(user_id, rc_token)
        except Exception as exc:
            logger.error("Keycloak role fetch failed: %s", exc)
            return AuthResult(authorized=False, reason=f"Erro ao verificar permissoes: {exc}")

        for role in required_roles:
            if role in roles:
                return AuthResult(authorized=True, user_roles=roles)

        return AuthResult(
            authorized=False,
            user_roles=roles,
            reason=f"Perfil necessario: {required_roles}. Seus perfis: {roles}",
        )

    async def _fetch_roles(
        self, user_id: str, token: Optional[str]
    ) -> list[str]:
        """Introspect token and extract realm roles from Keycloak."""
        if self._http is None or not token:
            return []
        url = f"{self._keycloak_url}/realms/{self._realm}/protocol/openid-connect/userinfo"
        headers = {"Authorization": f"Bearer {token}"}
        resp = await self._http.get(url, headers=headers, timeout=5.0)
        resp.raise_for_status()
        data = resp.json()
        # Keycloak puts realm roles under realm_access.roles
        return data.get("realm_access", {}).get("roles", [])
