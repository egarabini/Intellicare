---
tipo: referencia
tecnologia: Keycloak Admin REST API
versao: "26.x"
tags: [referencia, keycloak, auth, oidc, admin-api]
---

# Keycloak Admin REST API — Referência Rápida

> Endpoints da Admin REST API usados no IntelliCare V3 para gerenciar grupos, usuários e roles.

---

## Autenticação

```python
# Obter token de admin
POST /realms/master/protocol/openid-connect/token
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials
&client_id=admin-cli
&client_secret={KEYCLOAK_ADMIN_SECRET}
```

Header em todas as chamadas:
```
Authorization: Bearer {access_token}
```

---

## Realm: `intellicare`

Base URL: `{KEYCLOAK_URL}/admin/realms/intellicare`

---

## Grupos (1 grupo = 1 tenant)

### Criar grupo

```
POST /groups
{"name": "tenant_{slug}"}
```

### Listar grupos

```
GET /groups?search=tenant_&max=100
```

### Adicionar usuário ao grupo

```
PUT /users/{user_id}/groups/{group_id}
```

### Listar membros do grupo

```
GET /groups/{group_id}/members?max=100
```

---

## Usuários

### Criar usuário

```
POST /users
{
  "username": "admin@tenant",
  "email": "admin@tenant.com",
  "enabled": true,
  "credentials": [{"type": "password", "value": "...", "temporary": true}]
}
```

### Buscar usuário por email

```
GET /users?email=admin@tenant.com&exact=true
```

### Listar usuários do realm

```
GET /users?first=0&max=50
```

### Atribuir role ao usuário

```
POST /users/{user_id}/role-mappings/realm
[{"id": "{role_id}", "name": "TENANT_GESTOR"}]
```

---

## Roles

### Listar roles do realm

```
GET /roles
```

### Roles usados no IntelliCare

| Role | Descrição |
|------|-----------|
| `PLATFORM_ADMIN` | Super-admin da plataforma |
| `TENANT_GESTOR` | Gestor de um tenant específico |
| `CLINICO` | Profissional clínico |
| `PACIENTE` | Paciente (acesso limitado) |

---

## Clients (SPAs)

### Listar clients

```
GET /clients?clientId=portal
```

### Configuração padrão para SPAs (IntelliCare)

```json
{
  "clientId": "portal",
  "publicClient": true,
  "directAccessGrantsEnabled": false,
  "standardFlowEnabled": true,
  "attributes": {
    "pkce.code.challenge.method": "S256"
  },
  "redirectUris": ["https://portal.intellicare.ia.br/*"],
  "webOrigins": ["https://portal.intellicare.ia.br"]
}
```

> Todos os SPAs (portal, admin, gestor) usam `publicClient: true` + PKCE S256.

---

## Python Client Helper

```python
import httpx

class KeycloakAdminClient:
    def __init__(self, base_url: str, client_secret: str):
        self.base_url = base_url
        self.secret = client_secret
        self._token = None

    async def _get_token(self):
        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{self.base_url}/realms/master/protocol/openid-connect/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": "admin-cli",
                    "client_secret": self.secret,
                },
            )
            self._token = r.json()["access_token"]

    async def list_group_members(self, group_id: str) -> list:
        ...

    async def create_group(self, name: str) -> str:
        ...
```

---

## Links úteis

- [Admin REST API docs](https://www.keycloak.org/docs-api/latest/rest-api/)
- [Keycloak OIDC endpoints](https://www.keycloak.org/docs/latest/securing_apps/#endpoints)
- [PKCE para SPAs](https://datatracker.ietf.org/doc/html/rfc7636)

