"""Wrapper minimo para Keycloak Admin REST API, usado pelo modulo admin."""
from __future__ import annotations

import os
import secrets
from typing import Any

import httpx

from intellicare_core.config.settings import get_settings

_settings = get_settings()

KC_URL = os.getenv("KEYCLOAK_ADMIN_URL") or _settings.keycloak_url
KC_REALM = _settings.keycloak_realm
KC_ADMIN = os.getenv("KEYCLOAK_ADMIN_USER") or os.getenv("KEYCLOAK_ADMIN", "admin")
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
                    "client_id": "admin-cli",
                    "grant_type": "password",
                    "username": KC_ADMIN,
                    "password": KC_ADMIN_PW,
                },
                timeout=15,
            )
            resp.raise_for_status()
            self._token = resp.json()["access_token"]
        return self._token

    async def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        headers = kwargs.pop("headers", {})
        merged_headers = {
            "Authorization": f"Bearer {await self._ensure_token()}",
            "Content-Type": "application/json",
            **headers,
        }
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method,
                f"{KC_URL}{path}",
                headers=merged_headers,
                timeout=20,
                **kwargs,
            )
            if response.status_code == 401:
                self._token = None
                merged_headers["Authorization"] = f"Bearer {await self._ensure_token()}"
                response = await client.request(
                    method,
                    f"{KC_URL}{path}",
                    headers=merged_headers,
                    timeout=20,
                    **kwargs,
                )
            response.raise_for_status()
            return response

    async def create_tenant_group(self, slug: str) -> str:
        response = await self._request(
            "POST",
            f"/admin/realms/{KC_REALM}/groups",
            json={"name": f"tenant_{slug}", "attributes": {"tenant_id": [slug]}},
        )
        return response.headers["Location"].split("/")[-1]

    async def get_group_users(self, group_id: str) -> list[dict[str, Any]]:
        response = await self._request(
            "GET",
            f"/admin/realms/{KC_REALM}/groups/{group_id}/members",
        )
        users = response.json()
        
        import asyncio
        async def _fetch_roles(u: dict[str, Any]) -> None:
            uid = u["id"]
            resp = await self._request("GET", f"/admin/realms/{KC_REALM}/users/{uid}/role-mappings/realm")
            u["realmRoles"] = [r["name"] for r in resp.json()]
            
        if users:
            await asyncio.gather(*(_fetch_roles(u) for u in users))
            
        return users

    async def get_tenant_group_id(self, slug: str) -> str | None:
        response = await self._request(
            "GET",
            f"/admin/realms/{KC_REALM}/groups",
            params={"search": f"tenant_{slug}"},
        )
        groups = [g for g in response.json() if g["name"] == f"tenant_{slug}"]
        return groups[0]["id"] if groups else None

    async def invite_user(
        self,
        group_id: str,
        email: str,
        name: str,
        role: str,
    ) -> str:
        first_name, _, last_name = name.partition(" ")
        payload = {
            "email": email,
            "username": email,
            "firstName": first_name,
            "lastName": last_name,
            "enabled": True,
            "groups": [group_id],
            "realmRoles": [role],
            "requiredActions": ["UPDATE_PASSWORD"],
        }
        response = await self._request(
            "POST",
            f"/admin/realms/{KC_REALM}/users",
            json=payload,
        )
        return response.headers["Location"].split("/")[-1]

    async def deactivate_user(self, user_id: str) -> None:
        user = await self.get_user(user_id)
        await self._request(
            "PUT",
            f"/admin/realms/{KC_REALM}/users/{user_id}",
            json={**user, "enabled": False},
        )

    async def delete_group(self, group_id: str) -> None:
        await self._request("DELETE", f"/admin/realms/{KC_REALM}/groups/{group_id}")

    async def get_user(self, user_id: str) -> dict[str, Any]:
        response = await self._request("GET", f"/admin/realms/{KC_REALM}/users/{user_id}")
        return response.json()

    async def find_user_by_email(self, email: str) -> dict[str, Any] | None:
        response = await self._request(
            "GET",
            f"/admin/realms/{KC_REALM}/users",
            params={"email": email},
        )
        for user in response.json():
            if user.get("email", "").lower() == email.lower():
                return user
        return None

    async def get_realm_role(self, role_name: str) -> dict[str, Any]:
        response = await self._request(
            "GET",
            f"/admin/realms/{KC_REALM}/roles/{role_name}",
        )
        return response.json()

    async def assign_realm_roles(self, user_id: str, role_names: list[str]) -> None:
        if not role_names:
            return
        roles = [await self.get_realm_role(name) for name in role_names]
        await self._request(
            "POST",
            f"/admin/realms/{KC_REALM}/users/{user_id}/role-mappings/realm",
            json=roles,
        )

    async def create_admin_user(
        self,
        email: str,
        name: str,
        enabled: bool = True,
    ) -> dict[str, str]:
        existing = await self.find_user_by_email(email)
        if existing:
            await self.assign_realm_roles(existing["id"], ["PLATFORM_ADMIN"])
            return {
                "id": existing["id"],
                "temporary_password": "",
                "created": "false",
            }

        first_name, _, last_name = name.partition(" ")
        temp_password = f"Tmp@{secrets.token_urlsafe(8)}"
        payload = {
            "email": email,
            "username": email,
            "firstName": first_name,
            "lastName": last_name,
            "enabled": enabled,
            "emailVerified": False,
            "requiredActions": ["UPDATE_PASSWORD"],
            "credentials": [{
                "type": "password",
                "value": temp_password,
                "temporary": True,
            }],
        }
        response = await self._request(
            "POST",
            f"/admin/realms/{KC_REALM}/users",
            json=payload,
        )
        user_id = response.headers["Location"].split("/")[-1]
        await self.assign_realm_roles(user_id, ["PLATFORM_ADMIN"])
        try:
            await self._request(
                "PUT",
                f"/admin/realms/{KC_REALM}/users/{user_id}/send-verify-email",
            )
        except httpx.HTTPStatusError:
            pass
        return {"id": user_id, "temporary_password": temp_password, "created": "true"}

    async def update_admin_user(
        self,
        user_id: str,
        *,
        name: str | None = None,
        enabled: bool | None = None,
    ) -> None:
        user = await self.get_user(user_id)
        first_name = user.get("firstName", "")
        last_name = user.get("lastName", "")
        if name is not None:
            first_name, _, last_name = name.partition(" ")
        payload = {
            **user,
            "firstName": first_name,
            "lastName": last_name,
            "enabled": user.get("enabled", True) if enabled is None else enabled,
        }
        await self._request(
            "PUT",
            f"/admin/realms/{KC_REALM}/users/{user_id}",
            json=payload,
        )

    async def delete_user(self, user_id: str) -> None:
        await self._request("DELETE", f"/admin/realms/{KC_REALM}/users/{user_id}")
