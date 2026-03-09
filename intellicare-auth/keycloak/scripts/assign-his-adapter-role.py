#!/usr/bin/env python3
"""
Atribui a role HIS_ADAPTER ao service account intellicare-bridge-dev.
Uso em container ou localmente (sem dependência de jq).
"""
import json
import os
import sys
import urllib.request
import urllib.error

KEYCLOAK_URL = os.environ.get("KEYCLOAK_URL", "http://localhost:8080")
ADMIN_USER = os.environ.get("KEYCLOAK_ADMIN", "admin")
ADMIN_PASSWORD = os.environ.get("KEYCLOAK_ADMIN_PASSWORD", "changeme")
REALM = os.environ.get("KEYCLOAK_REALM", "bemcuidar")
CLIENT_ID = "intellicare-bridge-dev"
ROLE_NAME = "HIS_ADAPTER"


def req(method, path, data=None, token=None):
    url = f"{KEYCLOAK_URL.rstrip('/')}{path}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode() if data else None
    r = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r, timeout=30) as resp:
            body = resp.read().decode()
            return resp.status, json.loads(body) if body.strip() else None
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        return e.code, json.loads(body) if body.strip() else None


def main():
    print(f"=== Atribuindo role {ROLE_NAME} ao service account {CLIENT_ID} ===")
    print(f"Keycloak: {KEYCLOAK_URL} | Realm: {REALM}")

    # 1. Token admin
    print("\n[1/4] Obtendo token admin...")
    body = f"grant_type=password&client_id=admin-cli&username={ADMIN_USER}&password={ADMIN_PASSWORD}"
    r = urllib.request.Request(
        f"{KEYCLOAK_URL}/realms/master/protocol/openid-connect/token",
        data=body.encode(),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(r, timeout=30) as resp:
            token = json.loads(resp.read().decode())["access_token"]
    except urllib.error.HTTPError as e:
        print(f"ERRO: Falha ao obter token. HTTP {e.code}")
        sys.exit(1)
    print("   Token obtido.")

    # 2. Client UUID
    print("\n[2/4] Buscando client...")
    status, clients = req("GET", f"/admin/realms/{REALM}/clients?clientId={CLIENT_ID}", token=token)
    if status != 200 or not clients:
        print(f"ERRO: Client '{CLIENT_ID}' não encontrado.")
        sys.exit(1)
    client_uuid = clients[0]["id"]
    print(f"   Client UUID: {client_uuid}")

    # 3. Service account user
    print("\n[3/4] Obtendo service account user...")
    status, sa_user = req("GET", f"/admin/realms/{REALM}/clients/{client_uuid}/service-account-user", token=token)
    if status != 200:
        print("ERRO: Service account não encontrado.")
        sys.exit(1)
    user_id = sa_user["id"]
    print(f"   User ID: {user_id}")

    # 4. Role e atribuição
    print(f"\n[4/4] Atribuindo role {ROLE_NAME}...")
    status, role = req("GET", f"/admin/realms/{REALM}/roles/{ROLE_NAME}", token=token)
    if status != 200:
        print(f"ERRO: Role '{ROLE_NAME}' não encontrada.")
        sys.exit(1)
    status, _ = req("POST", f"/admin/realms/{REALM}/users/{user_id}/role-mappings/realm", [role], token=token)
    if status in (200, 204):
        print("   Role atribuída com sucesso.")
    else:
        status, current = req("GET", f"/admin/realms/{REALM}/users/{user_id}/role-mappings/realm", token=token)
        if current and any(r.get("name") == ROLE_NAME for r in current):
            print("   Role já estava atribuída.")
        else:
            print(f"ERRO: HTTP {status} ao atribuir role.")
            sys.exit(1)

    print("\n=== Concluído ===")
    print(f"O service account {CLIENT_ID} agora tem a role {ROLE_NAME}.")


if __name__ == "__main__":
    main()
