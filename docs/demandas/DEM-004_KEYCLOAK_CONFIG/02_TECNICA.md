---
dem: DEM-004
titulo: Keycloak — Configuração Completa
tipo: TECNICA
status: aprovado
criado: 2026-03-13
---

# DEM-004 · 02 — Especificação Técnica

## Pré-requisitos

| Dependência | Satisfeita por |
|---|---|
| Keycloak rodando em `localhost:8080` | DEM-002 `docker-compose.yml` |
| `infra/.env` com `KEYCLOAK_ADMIN` / `KEYCLOAK_ADMIN_PASSWORD` | DEM-002 `.env.example` |
| Python 3.11+ com `httpx`, `python-jose[cryptography]` | `requirements-dev.txt` |

---

## BLOCO 1 — `infra/keycloak/realm-export.json` (completo)

Substitui a versão mínima criada na DEM-002.  
Importar via Admin UI (Import Realm) ou automaticamente no primeiro boot do Keycloak
(montado em `/opt/keycloak/data/import/` no `docker-compose.yml`).

```json
{
  "id": "intellicare",
  "realm": "intellicare",
  "displayName": "IntelliCare",
  "enabled": true,
  "sslRequired": "external",
  "registrationAllowed": false,
  "loginWithEmailAllowed": true,
  "duplicateEmailsAllowed": false,
  "resetPasswordAllowed": false,
  "editUsernameAllowed": false,
  "bruteForceProtected": true,
  "accessTokenLifespan": 300,
  "refreshTokenMaxReuse": 0,
  "ssoSessionMaxLifespan": 36000,

  "roles": {
    "realm": [
      { "name": "PLATFORM_ADMIN",  "description": "Administrador global da plataforma" },
      { "name": "TENANT_GESTOR",   "description": "Gestor de uma unidade de saúde" },
      { "name": "CLINICO",         "description": "Profissional de saúde (médico, enfermeiro)" },
      { "name": "PACIENTE",        "description": "Paciente vinculado a uma unidade" }
    ]
  },

  "groups": [
    {
      "name": "tenant_dev",
      "attributes": { "tenant_id": ["dev"] },
      "realmRoles": ["TENANT_GESTOR", "CLINICO"]
    }
  ],

  "clients": [
    {
      "clientId": "intellicare-service",
      "name": "IntelliCare Service (Backend)",
      "enabled": true,
      "clientAuthenticatorType": "client-secret",
      "secret": "CHANGE_ME_ON_DEPLOY",
      "bearerOnly": false,
      "publicClient": false,
      "serviceAccountsEnabled": true,
      "standardFlowEnabled": true,
      "directAccessGrantsEnabled": true,
      "redirectUris": ["http://localhost:8000/*"],
      "webOrigins": ["http://localhost:8000"],
      "protocolMappers": [
        {
          "name": "tenant_id-mapper",
          "protocol": "openid-connect",
          "protocolMapper": "oidc-group-attribute-mapper",
          "consentRequired": false,
          "config": {
            "attribute.name": "tenant_id",
            "claim.name": "tenant_id",
            "id.token.claim": "true",
            "access.token.claim": "true",
            "userinfo.token.claim": "true",
            "aggregate.attrs": "false",
            "multivalued": "false"
          }
        }
      ]
    },
    {
      "clientId": "intellicare-frontend",
      "name": "IntelliCare Frontend (SPA — Fase 3)",
      "enabled": true,
      "publicClient": true,
      "standardFlowEnabled": true,
      "directAccessGrantsEnabled": false,
      "redirectUris": ["http://localhost:5173/*", "http://localhost:3000/*"],
      "webOrigins": ["http://localhost:5173", "http://localhost:3000"]
    }
  ],

  "users": [
    {
      "username": "platform-admin",
      "email": "platform-admin@intellicare.dev",
      "firstName": "Platform",
      "lastName": "Admin",
      "enabled": true,
      "emailVerified": true,
      "credentials": [{ "type": "password", "value": "Admin@2025!", "temporary": false }],
      "realmRoles": ["PLATFORM_ADMIN"]
    },
    {
      "username": "gestor-dev",
      "email": "gestor-dev@intellicare.dev",
      "firstName": "Gestor",
      "lastName": "Dev",
      "enabled": true,
      "emailVerified": true,
      "credentials": [{ "type": "password", "value": "Gestor@2025!", "temporary": false }],
      "realmRoles": ["TENANT_GESTOR"],
      "groups": ["tenant_dev"]
    },
    {
      "username": "clinico-dev",
      "email": "clinico-dev@intellicare.dev",
      "firstName": "Clinico",
      "lastName": "Dev",
      "enabled": true,
      "emailVerified": true,
      "credentials": [{ "type": "password", "value": "Clinico@2025!", "temporary": false }],
      "realmRoles": ["CLINICO"],
      "groups": ["tenant_dev"]
    }
  ],

  "scopeMappings": [],
  "clientScopeMappings": {}
}
```

---

## BLOCO 2 — `tools/scripts/setup_keycloak.py`

Script Python **idempotente**: pode ser re-executado a qualquer momento sem criar duplicatas.  
Usa a Keycloak Admin REST API diretamente via `httpx`.

```python
#!/usr/bin/env python3
"""
setup_keycloak.py — Configura realm intellicare via Admin REST API.
Idempotente: pode ser re-executado sem efeitos colaterais.

Uso:
    python tools/scripts/setup_keycloak.py
    python tools/scripts/setup_keycloak.py --keycloak-url http://localhost:8080 --admin admin --password admin
"""

import argparse
import sys
import os
import json
from typing import Optional
import httpx

# ---------------------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------------------
DEFAULT_KC_URL      = os.getenv("KEYCLOAK_URL",            "http://localhost:8080")
DEFAULT_ADMIN       = os.getenv("KEYCLOAK_ADMIN",          "admin")
DEFAULT_PASSWORD    = os.getenv("KEYCLOAK_ADMIN_PASSWORD", "admin")
REALM               = "intellicare"
CLIENT_SECRET       = os.getenv("KEYCLOAK_CLIENT_SECRET",  "CHANGE_ME_ON_DEPLOY")


# ---------------------------------------------------------------------------
# Helpers HTTP
# ---------------------------------------------------------------------------
class KeycloakAdmin:
    def __init__(self, base_url: str, admin: str, password: str):
        self.base_url = base_url.rstrip("/")
        self.token = self._get_admin_token(admin, password)
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type":  "application/json",
        }

    def _get_admin_token(self, admin: str, password: str) -> str:
        resp = httpx.post(
            f"{self.base_url}/realms/master/protocol/openid-connect/token",
            data={
                "client_id":  "admin-cli",
                "grant_type": "password",
                "username":   admin,
                "password":   password,
            },
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()["access_token"]

    def get(self, path: str) -> httpx.Response:
        return httpx.get(f"{self.base_url}{path}", headers=self.headers, timeout=15)

    def post(self, path: str, body: dict) -> httpx.Response:
        return httpx.post(f"{self.base_url}{path}", json=body, headers=self.headers, timeout=15)

    def put(self, path: str, body: dict) -> httpx.Response:
        return httpx.put(f"{self.base_url}{path}", json=body, headers=self.headers, timeout=15)

    def delete(self, path: str) -> httpx.Response:
        return httpx.delete(f"{self.base_url}{path}", headers=self.headers, timeout=15)


# ---------------------------------------------------------------------------
# Operações idempotentes
# ---------------------------------------------------------------------------

def ensure_realm(kc: KeycloakAdmin) -> None:
    resp = kc.get(f"/admin/realms/{REALM}")
    if resp.status_code == 200:
        print(f"  [OK] Realm '{REALM}' já existe")
        return

    kc.post("/admin/realms", {
        "id":                       REALM,
        "realm":                    REALM,
        "displayName":              "IntelliCare",
        "enabled":                  True,
        "sslRequired":              "external",
        "registrationAllowed":      False,
        "loginWithEmailAllowed":    True,
        "bruteForceProtected":      True,
        "accessTokenLifespan":      300,
        "ssoSessionMaxLifespan":    36000,
    }).raise_for_status()
    print(f"  [CRIADO] Realm '{REALM}'")


def ensure_role(kc: KeycloakAdmin, role_name: str, description: str = "") -> None:
    resp = kc.get(f"/admin/realms/{REALM}/roles/{role_name}")
    if resp.status_code == 200:
        print(f"  [OK] Role '{role_name}' já existe")
        return
    kc.post(f"/admin/realms/{REALM}/roles", {
        "name": role_name, "description": description
    }).raise_for_status()
    print(f"  [CRIADO] Role '{role_name}'")


def get_role_id(kc: KeycloakAdmin, role_name: str) -> str:
    resp = kc.get(f"/admin/realms/{REALM}/roles/{role_name}")
    resp.raise_for_status()
    return resp.json()["id"]


def ensure_group(kc: KeycloakAdmin, group_name: str, attributes: dict, role_names: list[str]) -> str:
    """Retorna o ID do grupo (cria se não existir)."""
    resp = kc.get(f"/admin/realms/{REALM}/groups?search={group_name}")
    resp.raise_for_status()
    groups = [g for g in resp.json() if g["name"] == group_name]

    if groups:
        group_id = groups[0]["id"]
        print(f"  [OK] Grupo '{group_name}' já existe (id={group_id})")
    else:
        r = kc.post(f"/admin/realms/{REALM}/groups", {"name": group_name, "attributes": attributes})
        r.raise_for_status()
        # Keycloak retorna o id no header Location
        location = r.headers.get("Location", "")
        group_id = location.split("/")[-1]
        print(f"  [CRIADO] Grupo '{group_name}' (id={group_id})")

    # Garantir atributos
    kc.put(f"/admin/realms/{REALM}/groups/{group_id}", {
        "name": group_name, "attributes": attributes
    }).raise_for_status()

    # Associar roles ao grupo
    existing_roles_resp = kc.get(f"/admin/realms/{REALM}/groups/{group_id}/role-mappings/realm")
    existing_roles = {r["name"] for r in existing_roles_resp.json()} if existing_roles_resp.status_code == 200 else set()

    roles_to_add = [
        {"id": get_role_id(kc, rn), "name": rn}
        for rn in role_names
        if rn not in existing_roles
    ]
    if roles_to_add:
        kc.post(f"/admin/realms/{REALM}/groups/{group_id}/role-mappings/realm", roles_to_add).raise_for_status()
        print(f"  [OK] Roles {[r['name'] for r in roles_to_add]} associadas ao grupo '{group_name}'")

    return group_id


def ensure_client(kc: KeycloakAdmin, client_id: str, payload: dict) -> str:
    """Retorna o UUID interno do client."""
    resp = kc.get(f"/admin/realms/{REALM}/clients?clientId={client_id}")
    resp.raise_for_status()
    clients = resp.json()

    if clients:
        uid = clients[0]["id"]
        print(f"  [OK] Client '{client_id}' já existe (id={uid})")
        return uid

    r = kc.post(f"/admin/realms/{REALM}/clients", payload)
    r.raise_for_status()
    location = r.headers.get("Location", "")
    uid = location.split("/")[-1]
    print(f"  [CRIADO] Client '{client_id}' (id={uid})")
    return uid


def ensure_protocol_mapper(kc: KeycloakAdmin, client_uid: str) -> None:
    """Garante que o mapper de tenant_id existe no client intellicare-service."""
    resp = kc.get(f"/admin/realms/{REALM}/clients/{client_uid}/protocol-mappers/models")
    resp.raise_for_status()
    mappers = resp.json()
    names = {m["name"] for m in mappers}

    if "tenant_id-mapper" in names:
        print("  [OK] Protocol mapper 'tenant_id-mapper' já existe")
        return

    kc.post(f"/admin/realms/{REALM}/clients/{client_uid}/protocol-mappers/models", {
        "name":           "tenant_id-mapper",
        "protocol":       "openid-connect",
        "protocolMapper": "oidc-group-attribute-mapper",
        "consentRequired": False,
        "config": {
            "attribute.name":     "tenant_id",
            "claim.name":         "tenant_id",
            "id.token.claim":     "true",
            "access.token.claim": "true",
            "userinfo.token.claim": "true",
            "aggregate.attrs":    "false",
            "multivalued":        "false",
        },
    }).raise_for_status()
    print("  [CRIADO] Protocol mapper 'tenant_id-mapper'")


def ensure_user(kc: KeycloakAdmin, username: str, email: str, first: str, last: str,
                password: str, realm_roles: list[str], group_id: Optional[str] = None) -> None:
    resp = kc.get(f"/admin/realms/{REALM}/users?username={username}")
    resp.raise_for_status()
    users = resp.json()

    if users:
        user_id = users[0]["id"]
        print(f"  [OK] User '{username}' já existe (id={user_id})")
    else:
        r = kc.post(f"/admin/realms/{REALM}/users", {
            "username":      username,
            "email":         email,
            "firstName":     first,
            "lastName":      last,
            "enabled":       True,
            "emailVerified": True,
            "credentials":   [{"type": "password", "value": password, "temporary": False}],
        })
        r.raise_for_status()
        location = r.headers.get("Location", "")
        user_id = location.split("/")[-1]
        print(f"  [CRIADO] User '{username}' (id={user_id})")

    # Roles
    existing_resp = kc.get(f"/admin/realms/{REALM}/users/{user_id}/role-mappings/realm")
    existing = {r["name"] for r in existing_resp.json()} if existing_resp.status_code == 200 else set()
    to_add = [
        {"id": get_role_id(kc, rn), "name": rn}
        for rn in realm_roles if rn not in existing
    ]
    if to_add:
        kc.post(f"/admin/realms/{REALM}/users/{user_id}/role-mappings/realm", to_add).raise_for_status()

    # Grupo
    if group_id:
        kc.put(f"/admin/realms/{REALM}/users/{user_id}/groups/{group_id}", {}).raise_for_status()


# ---------------------------------------------------------------------------
# Fluxo principal
# ---------------------------------------------------------------------------

def main(args: argparse.Namespace) -> None:
    kc = KeycloakAdmin(args.keycloak_url, args.admin, args.password)
    print(f"\n=== Setup Keycloak — realm '{REALM}' ===\n")

    # 1. Realm
    print("1. Realm")
    ensure_realm(kc)

    # 2. Roles
    print("\n2. Roles")
    roles = {
        "PLATFORM_ADMIN": "Administrador global da plataforma",
        "TENANT_GESTOR":  "Gestor de unidade de saúde",
        "CLINICO":        "Profissional de saúde",
        "PACIENTE":       "Paciente vinculado a uma unidade",
    }
    for name, desc in roles.items():
        ensure_role(kc, name, desc)

    # 3. Grupo tenant_dev
    print("\n3. Grupo tenant_dev")
    tenant_dev_id = ensure_group(
        kc,
        group_name="tenant_dev",
        attributes={"tenant_id": ["dev"]},
        role_names=["TENANT_GESTOR", "CLINICO"],
    )

    # 4. Client intellicare-service
    print("\n4. Client intellicare-service")
    svc_uid = ensure_client(kc, "intellicare-service", {
        "clientId":                "intellicare-service",
        "name":                    "IntelliCare Service (Backend)",
        "enabled":                 True,
        "clientAuthenticatorType": "client-secret",
        "secret":                  CLIENT_SECRET,
        "bearerOnly":              False,
        "publicClient":            False,
        "serviceAccountsEnabled":  True,
        "standardFlowEnabled":     True,
        "directAccessGrantsEnabled": True,
        "redirectUris":            ["http://localhost:8000/*"],
        "webOrigins":              ["http://localhost:8000"],
    })
    ensure_protocol_mapper(kc, svc_uid)

    # 5. Client intellicare-frontend
    print("\n5. Client intellicare-frontend")
    ensure_client(kc, "intellicare-frontend", {
        "clientId":              "intellicare-frontend",
        "name":                  "IntelliCare Frontend (SPA — Fase 3)",
        "enabled":               True,
        "publicClient":          True,
        "standardFlowEnabled":   True,
        "directAccessGrantsEnabled": False,
        "redirectUris":          ["http://localhost:5173/*", "http://localhost:3000/*"],
        "webOrigins":            ["http://localhost:5173", "http://localhost:3000"],
    })

    # 6. Usuários dev
    print("\n6. Usuários dev")
    ensure_user(kc, "platform-admin", "platform-admin@intellicare.dev",
                "Platform", "Admin", "Admin@2025!", ["PLATFORM_ADMIN"])
    ensure_user(kc, "gestor-dev", "gestor-dev@intellicare.dev",
                "Gestor", "Dev", "Gestor@2025!", ["TENANT_GESTOR"],
                group_id=tenant_dev_id)
    ensure_user(kc, "clinico-dev", "clinico-dev@intellicare.dev",
                "Clinico", "Dev", "Clinico@2025!", ["CLINICO"],
                group_id=tenant_dev_id)

    print("\n=== Setup concluído com sucesso ===\n")
    print("Próximos passos:")
    print("  1. Obtenha o client-secret: Admin UI → intellicare → Clients → intellicare-service → Credentials")
    print("  2. Atualize infra/.env:  KEYCLOAK_CLIENT_SECRET=<valor>")
    print("  3. Execute o smoke test:  python tools/scripts/test_keycloak.py")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Setup Keycloak para IntelliCare V3")
    parser.add_argument("--keycloak-url", default=DEFAULT_KC_URL)
    parser.add_argument("--admin",        default=DEFAULT_ADMIN)
    parser.add_argument("--password",     default=DEFAULT_PASSWORD)
    main(parser.parse_args())
```

---

## BLOCO 3 — `tools/scripts/test_keycloak.py`

Teste de integração end-to-end: obtém token via password grant → chama `verify_token()` → valida `TenantContext`.

```python
#!/usr/bin/env python3
"""
test_keycloak.py — Teste de integração Keycloak ↔ verify_token().
Valida que o JWT produzido pelo Keycloak é decodificado corretamente
e que tenant_id está presente no TenantContext.

Uso:
    python tools/scripts/test_keycloak.py
"""

import asyncio
import sys
import os
import httpx

KC_URL         = os.getenv("KEYCLOAK_URL",            "http://localhost:8080")
CLIENT_ID      = "intellicare-service"
CLIENT_SECRET  = os.getenv("KEYCLOAK_CLIENT_SECRET",  "CHANGE_ME_ON_DEPLOY")
REALM          = "intellicare"


def get_token(username: str, password: str) -> str:
    resp = httpx.post(
        f"{KC_URL}/realms/{REALM}/protocol/openid-connect/token",
        data={
            "client_id":     CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type":    "password",
            "username":      username,
            "password":      password,
            "scope":         "openid",
        },
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


async def run_tests() -> None:
    # Importa após garantir que sys.path inclui raiz do projeto
    sys.path.insert(0, ".")
    from intellicare_core.auth.jwt import verify_token  # type: ignore

    failures = 0

    for username, password, expected_role, expected_tenant in [
        ("gestor-dev",  "Gestor@2025!", "TENANT_GESTOR",  "dev"),
        ("clinico-dev", "Clinico@2025!", "CLINICO",        "dev"),
    ]:
        print(f"\nTestando user '{username}'...")
        token = get_token(username, password)
        ctx = await verify_token(token)

        assert ctx.tenant_id == expected_tenant, (
            f"FAIL tenant_id: esperado='{expected_tenant}' obtido='{ctx.tenant_id}'"
        )
        assert ctx.has_role(expected_role), (
            f"FAIL role: esperado='{expected_role}' roles={ctx.roles}"
        )
        assert ctx.schema == f"tenant_{expected_tenant}", (
            f"FAIL schema: esperado='tenant_{expected_tenant}' obtido='{ctx.schema}'"
        )

        print(f"  [PASS] tenant_id={ctx.tenant_id}  roles={ctx.roles}  schema={ctx.schema}")

    if failures:
        print(f"\n{failures} teste(s) falharam.")
        sys.exit(1)
    else:
        print("\nTodos os testes passaram.")


if __name__ == "__main__":
    asyncio.run(run_tests())
```

---

## BLOCO 4 — Atualização de `infra/.env`

Adicionar/atualizar estas variáveis após rodar o setup:

```dotenv
# Keycloak — client secret (obter em Admin UI após setup)
KEYCLOAK_CLIENT_SECRET=CHANGE_ME_ON_DEPLOY

# URL interna (usada pelo intellicare-service dentro do docker network)
KEYCLOAK_INTERNAL_URL=http://keycloak:8080

# URL externa (usada pelo frontend e scripts locais)
KEYCLOAK_URL=http://localhost:8080
KEYCLOAK_REALM=intellicare
KEYCLOAK_CLIENT_ID=intellicare-service
```

---

## BLOCO 5 — Sequência de execução

```bash
# 1. Subir infraestrutura (se ainda não estiver rodando)
docker compose -f infra/docker-compose.yml up -d

# 2. Aguardar Keycloak (health check pode levar ~30s)
docker compose -f infra/docker-compose.yml ps keycloak

# 3. Rodar setup (idempotente)
python tools/scripts/setup_keycloak.py

# 4. Obter client-secret via Admin UI:
#    http://localhost:8080 → intellicare → Clients → intellicare-service → Credentials → Secret
#    Copiar o valor e atualizar infra/.env

# 5. Validar integração end-to-end
python tools/scripts/test_keycloak.py

# 6. (Opcional) Re-exportar realm para commitar estado atualizado:
docker exec intellicare-keycloak \
  /opt/keycloak/bin/kc.sh export \
  --realm intellicare \
  --dir /opt/keycloak/data/import \
  --users same_file
# Copiar de volta:
docker cp intellicare-keycloak:/opt/keycloak/data/import/intellicare-realm.json \
  infra/keycloak/realm-export.json
```

---

## BLOCO 6 — Commit

```bash
git add infra/keycloak/realm-export.json \
        tools/scripts/setup_keycloak.py \
        tools/scripts/test_keycloak.py \
        infra/.env.example \
        docs/demandas/DEM-004_KEYCLOAK_CONFIG/

git commit -m "DEM-004: Keycloak realm intellicare - config completa, setup script e teste e2e"
git push origin main
```

---

## Critérios de Aceite

| # | Critério | Como verificar |
|---|---|---|
| AC-1 | Realm `intellicare` existe | `GET /admin/realms/intellicare` → 200 |
| AC-2 | 4 roles criadas | Admin UI → Realm Roles → lista tem as 4 |
| AC-3 | Grupo `tenant_dev` com `tenant_id=dev` | Admin UI → Groups → tenant_dev → Attributes |
| AC-4 | Protocol mapper injeta `tenant_id` no JWT | Decodificar token de `gestor-dev` |
| AC-5 | `verify_token()` retorna `TenantContext` correto | `test_keycloak.py` passa |
| AC-6 | `TenantContext.schema == "tenant_dev"` | `test_keycloak.py` → assert schema |
| AC-7 | Setup é idempotente | Rodar `setup_keycloak.py` 2× sem erros |
| AC-8 | Usuários dev conseguem obter token | Password grant com cada usuário dev |
