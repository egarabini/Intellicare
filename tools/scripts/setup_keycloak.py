#!/usr/bin/env python3
"""
setup_keycloak.py - Configura realm intellicare via Admin REST API.
Idempotente: pode ser re-executado sem efeitos colaterais.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

import httpx

ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = ROOT / "infra" / ".env"
REALM = "intellicare"


def load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


load_env_file(ENV_PATH)

DEFAULT_KC_URL = os.getenv("KEYCLOAK_URL", "http://localhost:8080")
DEFAULT_ADMIN = os.getenv("KEYCLOAK_ADMIN", "admin")
DEFAULT_PASSWORD = os.getenv("KEYCLOAK_ADMIN_PASSWORD", "admin")
CLIENT_SECRET = os.getenv("KEYCLOAK_CLIENT_SECRET", "CHANGE_ME_ON_DEPLOY")


class KeycloakAdmin:
    def __init__(self, base_url: str, admin: str, password: str):
        self.base_url = base_url.rstrip("/")
        self.token = self._get_admin_token(admin, password)
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    def _get_admin_token(self, admin: str, password: str) -> str:
        response = httpx.post(
            f"{self.base_url}/realms/master/protocol/openid-connect/token",
            data={
                "client_id": "admin-cli",
                "grant_type": "password",
                "username": admin,
                "password": password,
            },
            timeout=20,
        )
        response.raise_for_status()
        return response.json()["access_token"]

    def get(self, path: str, **params: Any) -> httpx.Response:
        return httpx.get(
            f"{self.base_url}{path}",
            headers=self.headers,
            params=params or None,
            timeout=20,
        )

    def post(self, path: str, body: dict[str, Any]) -> httpx.Response:
        return httpx.post(f"{self.base_url}{path}", json=body, headers=self.headers, timeout=20)

    def put(self, path: str, body: dict[str, Any]) -> httpx.Response:
        return httpx.put(f"{self.base_url}{path}", json=body, headers=self.headers, timeout=20)


def ensure_realm(kc: KeycloakAdmin) -> None:
    response = kc.get(f"/admin/realms/{REALM}")
    if response.status_code == 200:
        print(f"  [OK] Realm '{REALM}' ja existe")
        return

    kc.post(
        "/admin/realms",
        {
            "id": REALM,
            "realm": REALM,
            "displayName": "IntelliCare",
            "enabled": True,
            "sslRequired": "external",
            "registrationAllowed": False,
            "loginWithEmailAllowed": True,
            "bruteForceProtected": True,
            "accessTokenLifespan": 300,
            "ssoSessionMaxLifespan": 36000,
        },
    ).raise_for_status()
    print(f"  [CRIADO] Realm '{REALM}'")


def ensure_role(kc: KeycloakAdmin, role_name: str, description: str) -> None:
    response = kc.get(f"/admin/realms/{REALM}/roles/{role_name}")
    if response.status_code == 200:
        print(f"  [OK] Role '{role_name}' ja existe")
        return
    kc.post(f"/admin/realms/{REALM}/roles", {"name": role_name, "description": description}).raise_for_status()
    print(f"  [CRIADO] Role '{role_name}'")


def get_role(kc: KeycloakAdmin, role_name: str) -> dict[str, Any]:
    response = kc.get(f"/admin/realms/{REALM}/roles/{role_name}")
    response.raise_for_status()
    payload = response.json()
    return {"id": payload["id"], "name": payload["name"]}


def ensure_group(
    kc: KeycloakAdmin,
    group_name: str,
    attributes: dict[str, list[str]],
    role_names: list[str],
) -> str:
    response = kc.get(f"/admin/realms/{REALM}/groups", search=group_name)
    response.raise_for_status()
    groups = [group for group in response.json() if group["name"] == group_name]

    if groups:
        group_id = groups[0]["id"]
        print(f"  [OK] Grupo '{group_name}' ja existe (id={group_id})")
    else:
        created = kc.post(
            f"/admin/realms/{REALM}/groups",
            {"name": group_name, "attributes": attributes},
        )
        created.raise_for_status()
        group_id = created.headers["Location"].rstrip("/").split("/")[-1]
        print(f"  [CRIADO] Grupo '{group_name}' (id={group_id})")

    kc.put(
        f"/admin/realms/{REALM}/groups/{group_id}",
        {"name": group_name, "attributes": attributes},
    ).raise_for_status()

    existing = kc.get(f"/admin/realms/{REALM}/groups/{group_id}/role-mappings/realm")
    existing.raise_for_status()
    existing_names = {role["name"] for role in existing.json()}
    to_add = [get_role(kc, role_name) for role_name in role_names if role_name not in existing_names]
    if to_add:
        kc.post(f"/admin/realms/{REALM}/groups/{group_id}/role-mappings/realm", to_add).raise_for_status()
        print(f"  [OK] Roles {[role['name'] for role in to_add]} associadas ao grupo '{group_name}'")

    return group_id


def tenant_id_mapper_payload() -> dict[str, Any]:
    return {
        "name": "tenant_id-mapper",
        "protocol": "openid-connect",
        "protocolMapper": "oidc-usermodel-attribute-mapper",
        "consentRequired": False,
        "config": {
            "user.attribute": "tenant_id",
            "claim.name": "tenant_id",
            "id.token.claim": "true",
            "access.token.claim": "true",
            "userinfo.token.claim": "true",
            "jsonType.label": "String",
        },
    }


def ensure_client(kc: KeycloakAdmin, client_id: str, payload: dict[str, Any]) -> str:
    response = kc.get(f"/admin/realms/{REALM}/clients", clientId=client_id)
    response.raise_for_status()
    clients = response.json()
    if clients:
        client_uuid = clients[0]["id"]
        updated_payload = {**clients[0], **payload}
        existing_mappers = {mapper["name"]: mapper for mapper in clients[0].get("protocolMappers", [])}
        requested_mappers = {mapper["name"]: mapper for mapper in payload.get("protocolMappers", [])}
        updated_payload["protocolMappers"] = list({**existing_mappers, **requested_mappers}.values())
        kc.put(f"/admin/realms/{REALM}/clients/{client_uuid}", updated_payload).raise_for_status()
        print(f"  [OK] Client '{client_id}' ja existe (id={client_uuid})")
        return client_uuid

    created = kc.post(f"/admin/realms/{REALM}/clients", payload)
    created.raise_for_status()
    client_uuid = created.headers["Location"].rstrip("/").split("/")[-1]
    print(f"  [CRIADO] Client '{client_id}' (id={client_uuid})")
    return client_uuid


def ensure_user(
    kc: KeycloakAdmin,
    username: str,
    email: str,
    first_name: str,
    last_name: str,
    password: str,
    realm_roles: list[str],
    group_id: str | None = None,
    attributes: dict[str, list[str]] | None = None,
) -> None:
    response = kc.get(f"/admin/realms/{REALM}/users", username=username)
    response.raise_for_status()
    users = [user for user in response.json() if user["username"] == username]

    if users:
        user_id = users[0]["id"]
        kc.put(
            f"/admin/realms/{REALM}/users/{user_id}",
            {
                **users[0],
                "email": email,
                "firstName": first_name,
                "lastName": last_name,
                "enabled": True,
                "emailVerified": True,
                "attributes": attributes or {},
            },
        ).raise_for_status()
        print(f"  [OK] User '{username}' ja existe (id={user_id})")
    else:
        created = kc.post(
            f"/admin/realms/{REALM}/users",
            {
                "username": username,
                "email": email,
                "firstName": first_name,
                "lastName": last_name,
                "enabled": True,
                "emailVerified": True,
                "attributes": attributes or {},
                "credentials": [{"type": "password", "value": password, "temporary": False}],
            },
        )
        created.raise_for_status()
        user_id = created.headers["Location"].rstrip("/").split("/")[-1]
        print(f"  [CRIADO] User '{username}' (id={user_id})")

    kc.put(
        f"/admin/realms/{REALM}/users/{user_id}/reset-password",
        {"type": "password", "value": password, "temporary": False},
    ).raise_for_status()

    existing_roles = kc.get(f"/admin/realms/{REALM}/users/{user_id}/role-mappings/realm")
    existing_roles.raise_for_status()
    existing_names = {role["name"] for role in existing_roles.json()}
    to_add = [get_role(kc, role_name) for role_name in realm_roles if role_name not in existing_names]
    if to_add:
        kc.post(f"/admin/realms/{REALM}/users/{user_id}/role-mappings/realm", to_add).raise_for_status()

    if group_id:
        group_members = kc.get(f"/admin/realms/{REALM}/users/{user_id}/groups")
        group_members.raise_for_status()
        if all(group["id"] != group_id for group in group_members.json()):
            httpx.put(
                f"{kc.base_url}/admin/realms/{REALM}/users/{user_id}/groups/{group_id}",
                headers=kc.headers,
                timeout=20,
            ).raise_for_status()


def export_realm(kc: KeycloakAdmin) -> dict[str, Any]:
    response = kc.get(
        f"/admin/realms/{REALM}/partial-export",
        exportClients="true",
        exportGroupsAndRoles="true",
    )
    response.raise_for_status()
    return response.json()


def main(args: argparse.Namespace) -> None:
    kc = KeycloakAdmin(args.keycloak_url, args.admin, args.password)
    print(f"\n=== Setup Keycloak - realm '{REALM}' ===\n")

    print("1. Realm")
    ensure_realm(kc)

    print("\n2. Roles")
    roles = {
        "PLATFORM_ADMIN": "Administrador global da plataforma",
        "TENANT_GESTOR": "Gestor de unidade de saude",
        "CLINICO": "Profissional de saude",
        "PACIENTE": "Paciente vinculado a uma unidade",
    }
    for role_name, description in roles.items():
        ensure_role(kc, role_name, description)

    print("\n3. Grupo tenant_dev")
    tenant_dev_group_id = ensure_group(
        kc,
        group_name="tenant_dev",
        attributes={"tenant_id": ["dev"]},
        role_names=["TENANT_GESTOR", "CLINICO"],
    )

    print("\n4. Client intellicare-service")
    service_client_uuid = ensure_client(
        kc,
        "intellicare-service",
        {
            "clientId": "intellicare-service",
            "name": "IntelliCare Service (Backend)",
            "enabled": True,
            "clientAuthenticatorType": "client-secret",
            "secret": CLIENT_SECRET,
            "bearerOnly": False,
            "publicClient": False,
            "serviceAccountsEnabled": True,
            "standardFlowEnabled": True,
            "directAccessGrantsEnabled": True,
            "redirectUris": ["http://localhost:8000/*"],
            "webOrigins": ["http://localhost:8000"],
            "protocolMappers": [tenant_id_mapper_payload()],
        },
    )

    print("\n5. Client intellicare-frontend")
    ensure_client(
        kc,
        "intellicare-frontend",
        {
            "clientId": "intellicare-frontend",
            "name": "IntelliCare Frontend (SPA - Fase 3)",
            "enabled": True,
            "publicClient": True,
            "standardFlowEnabled": True,
            "directAccessGrantsEnabled": False,
            "redirectUris": ["http://localhost:5173/*", "http://localhost:3000/*"],
            "webOrigins": ["http://localhost:5173", "http://localhost:3000"],
        },
    )

    print("\n6. Client admin-ui")
    ensure_client(
        kc,
        "admin-ui",
        {
            "clientId": "admin-ui",
            "name": "Admin UI",
            "enabled": True,
            "publicClient": True,
            "standardFlowEnabled": True,
            "directAccessGrantsEnabled": False,
            "redirectUris": ["http://localhost:5174/*", "http://localhost:8000/admin-ui/*"],
            "webOrigins": ["http://localhost:5174", "http://localhost:8000"],
        },
    )

    print("\n7. Client gestor-ui")
    ensure_client(
        kc,
        "gestor-ui",
        {
            "clientId": "gestor-ui",
            "name": "Gestor UI",
            "enabled": True,
            "publicClient": True,
            "standardFlowEnabled": True,
            "directAccessGrantsEnabled": False,
            "redirectUris": ["http://localhost:5175/*", "http://localhost:8000/gestor-ui/*"],
            "webOrigins": ["http://localhost:5175", "http://localhost:8000"],
        },
    )

    print("\n8. Client clinico-ui")
    ensure_client(
        kc,
        "clinico-ui",
        {
            "clientId": "clinico-ui",
            "name": "Clinico UI",
            "enabled": True,
            "publicClient": True,
            "standardFlowEnabled": True,
            "directAccessGrantsEnabled": False,
            "redirectUris": ["http://localhost:5173/*", "http://localhost:8000/clinico-ui/*"],
            "webOrigins": ["http://localhost:5173", "http://localhost:8000"],
        },
    )

    print("\n9. Client portal")
    ensure_client(
        kc,
        "portal",
        {
            "clientId": "portal",
            "name": "IntelliCare Portal",
            "enabled": True,
            "publicClient": True,
            "standardFlowEnabled": True,
            "directAccessGrantsEnabled": False,
            "redirectUris": ["http://localhost:5176/*", "http://localhost:8000/*"],
            "webOrigins": ["http://localhost:5176", "http://localhost:8000"],
        },
    )

    print("\n10. Usuarios dev")
    ensure_user(
        kc,
        "platform-admin",
        "platform-admin@intellicare.dev",
        "Platform",
        "Admin",
        "Admin@2025!",
        ["PLATFORM_ADMIN"],
    )
    ensure_user(
        kc,
        "gestor-dev",
        "gestor-dev@intellicare.dev",
        "Gestor",
        "Dev",
        "Gestor@2025!",
        ["TENANT_GESTOR"],
        group_id=tenant_dev_group_id,
        attributes={"tenant_id": ["dev"]},
    )
    ensure_user(
        kc,
        "clinico-dev",
        "clinico-dev@intellicare.dev",
        "Clinico",
        "Dev",
        "Clinico@2025!",
        ["CLINICO"],
        group_id=tenant_dev_group_id,
        attributes={"tenant_id": ["dev"]},
    )

    try:
        exported = export_realm(kc)
    except httpx.HTTPStatusError as exc:
        print(f"\n  [WARN] Export via Admin API indisponivel: {exc.response.status_code}")
    else:
        export_path = ROOT / "infra" / "keycloak" / "realm-export.json"
        export_path.write_text(json.dumps(exported, indent=2), encoding="utf-8")
        print(f"\n  [EXPORTADO] {export_path}")

    print("\n=== Setup concluido com sucesso ===\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Setup Keycloak para IntelliCare V3")
    parser.add_argument("--keycloak-url", default=DEFAULT_KC_URL)
    parser.add_argument("--admin", default=DEFAULT_ADMIN)
    parser.add_argument("--password", default=DEFAULT_PASSWORD)
    main(parser.parse_args())
