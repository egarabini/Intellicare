#!/usr/bin/env python3
"""
Carrega usuários de staging no Keycloak (realm bemcuidar).

Cria:
- 1 PLATFORM_ADMIN
- 4 TENANT_GESTOR (um por secretaria/estabelecimento)
- Profissionais (MEDICO, ENFERMEIRO) com tenant_id e vínculo à unidade

Uso:
  python scripts/seed_keycloak_staging.py
  python scripts/seed_keycloak_staging.py --kc-url http://localhost:8080 --realm bemcuidar
"""

import argparse
import json
import sys
from pathlib import Path

try:
    import requests
except ImportError:
    print("Instale requests: pip install requests")
    sys.exit(1)

REPO_ROOT = Path(__file__).parent.parent
USUARIOS_PATH = REPO_ROOT / "data" / "V2.0.0-KEYCLOAK" / "keycloak" / "usuarios_staging.json"


def ensure_user_profile_attrs(kc_url: str, realm: str, token: str) -> None:
    """Registra tenant_id e tenants no User Profile (KC 24+)."""
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    url = f"{kc_url}/admin/realms/{realm}/users/profile"
    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        return
    config = r.json()
    attrs = {a["name"]: a for a in config.get("attributes", [])}
    for name, display in [("tenant_id", "Tenant ID"), ("tenants", "Tenants")]:
        if name not in attrs:
            config["attributes"].append({
                "name": name,
                "displayName": display,
                "permissions": {"view": ["admin"], "edit": ["admin"]},
                "multivalued": name == "tenants",
                "group": "user-metadata",
            })
    requests.put(url, headers=headers, json=config)


def create_user(kc_url: str, realm: str, token: str, user_data: dict, default_password: str) -> bool:
    """Cria usuário no Keycloak."""
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {
        "username": user_data["username"],
        "email": user_data["email"],
        "firstName": user_data.get("firstName", ""),
        "lastName": user_data.get("lastName", ""),
        "enabled": True,
        "emailVerified": True,
        "credentials": [{"type": "password", "value": default_password, "temporary": True}],
        "attributes": {},
    }
    for k, v in user_data.get("attributes", {}).items():
        payload["attributes"][k] = v if isinstance(v, list) else [str(v)]

    r = requests.post(f"{kc_url}/admin/realms/{realm}/users", headers=headers, json=payload)
    if r.status_code == 201:
        return True
    if r.status_code == 409:
        return False  # já existe
    print(f"  Erro {user_data['username']}: {r.status_code} {r.text[:200]}")
    return False


def assign_roles(kc_url: str, realm: str, token: str, user_id: str, roles: list[str]) -> None:
    """Atribui realm roles ao usuário."""
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    roles_payload = []
    for role_name in roles:
        r = requests.get(f"{kc_url}/admin/realms/{realm}/roles/{role_name}", headers=headers)
        if r.status_code == 200:
            roles_payload.append(r.json())
    if roles_payload:
        requests.post(
            f"{kc_url}/admin/realms/{realm}/users/{user_id}/role-mappings/realm",
            headers=headers,
            json=roles_payload,
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Carrega usuários de staging no Keycloak")
    parser.add_argument("--kc-url", default="http://localhost:8080", help="URL do Keycloak")
    parser.add_argument("--realm", default="bemcuidar", help="Realm")
    parser.add_argument("--admin-user", default="admin", help="Admin username")
    parser.add_argument("--admin-pass", help="Admin password (ou env KEYCLOAK_ADMIN_PASSWORD)")
    args = parser.parse_args()

    import os
    admin_pass = args.admin_pass or os.environ.get("KEYCLOAK_ADMIN_PASSWORD")
    if not admin_pass:
        print("Use --admin-pass SENHA ou exporte KEYCLOAK_ADMIN_PASSWORD")
        sys.exit(1)

    if not USUARIOS_PATH.exists():
        print(f"Arquivo não encontrado: {USUARIOS_PATH}")
        sys.exit(1)

    with open(USUARIOS_PATH, encoding="utf-8") as f:
        data = json.load(f)

    kc_url = args.kc_url.rstrip("/")
    realm = data.get("realm", args.realm)
    default_password = data.get("default_password", "Staging@2026!")
    users = data.get("users", [])

    # Token admin
    r = requests.post(
        f"{kc_url}/realms/master/protocol/openid-connect/token",
        data={
            "client_id": "admin-cli",
            "username": args.admin_user,
            "password": admin_pass,
            "grant_type": "password",
        },
    )
    if r.status_code != 200:
        print(f"Erro ao obter token: {r.status_code}")
        sys.exit(1)
    token = r.json()["access_token"]

    ensure_user_profile_attrs(kc_url, realm, token)

    created = 0
    for u in users:
        roles = u.pop("roles", [])
        practitioner_id = u.pop("practitioner_id", None)
        if create_user(kc_url, realm, token, u, default_password):
            created += 1
            # Buscar user_id
            r = requests.get(
                f"{kc_url}/admin/realms/{realm}/users",
                headers={"Authorization": f"Bearer {token}"},
                params={"username": u["username"]},
            )
            if r.status_code == 200 and r.json():
                user_id = r.json()[0]["id"]
                assign_roles(kc_url, realm, token, user_id, roles)
                print(f"  OK: {u['username']} ({', '.join(roles)})")
        else:
            print(f"  (existente): {u['username']}")

    print(f"\nUsuários processados: {len(users)}, novos: {created}")
    print(f"Senha padrão: {default_password} (temporária — trocar no primeiro login)")


if __name__ == "__main__":
    main()
