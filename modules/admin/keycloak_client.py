"""Wrapper minimo para Keycloak Admin REST API, usado pelo modulo admin."""
from __future__ import annotations

import os
from typing import Any

import httpx

from intellicare_core.config.settings import get_settings

_settings = get_settings()

KC_URL      = _settings.keycloak_url
KC_REALM    = _settings.keycloak_realm
KC_ADMIN    = os.getenv("KEYCLOAK_ADMIN",          "admin")
KC_ADMIN_PW = os.getenv("KEYCLOAK_ADMIN_PASSWORD", "admin_dev_password")


class KeycloakAdminClient:
    """Client assincrono para Keycloak Admin API."""

    def __init__(self) -> None:
        self._token: str | None = None

    async def _ensure_token(self) -> str:
        if self._token:
            return self._token
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{KC_URL}/realms/master/protocol/openid-connect/token",
                data={
                    "client_id":  "admin-cli",
                    "grant_type": "password",
                    "username":   KC_ADMIN,
                    "password":   KC_ADMIN_PW,
                },
                timeout=15,
            )
            resp.raise_for_status()
            self._token = resp.json()["access_token"]
        return self._token  # type: ignore[return-value]

    async def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {await self._ensure_token()}",
            "Content-Type":  "application/json",
        }

    async def create_tenant_group(self, slug: str) -> str:
        """Cria grupo tenant_{slug} no Keycloak e retorna seu ID."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{KC_URL}/admin/realms/{KC_REALM}/groups",
                json={"name": f"tenant_{slug}", "attributes": {"tenant_id": [slug]}},
                headers=await self._headers(),
                timeout=15,
            )
            resp.raise_for_status()
            return resp.headers["Location"].split("/")[-1]

    async def get_group_users(self, group_id: str) -> list[dict[str, Any]]:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{KC_URL}/admin/realms/{KC_REALM}/groups/{group_id}/members",
                headers=await self._headers(),
                timeout=15,
            )
            resp.raise_for_status()
            return resp.json()

    async def get_tenant_group_id(self, slug: str) -> str | None:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{KC_URL}/admin/realms/{KC_REALM}/groups?search=tenant_{slug}",
                headers=await self._headers(),
                timeout=15,
            )
            resp.raise_for_status()
            groups = [g for g in resp.json() if g["name"] == f"tenant_{slug}"]
            return groups[0]["id"] if groups else None

