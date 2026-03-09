# 02 — Especificação Técnica: Keycloak IntelliCare

> **Versão:** 2.0.0 | **Data:** 2026-03-06 | **Status:** ✅ Referência
> **Rastreabilidade:** V2.0.0-KEYCLOAK | **Público-alvo:** Desenvolvedores, Arquitetos

---

## 🏗️ Infraestrutura

### Servidor Keycloak

| Componente | Valor |
|------------|-------|
| Versão | `quay.io/keycloak/keycloak:24.0` |
| Hostname | `auth.intellicare.ia.br` |
| IP | `167.86.97.142` |
| Porta HTTP | `8080` (interna) |
| Porta HTTPS | `8443` (via Traefik) |
| Realm | `bemcuidar` |
| Database | PostgreSQL 15-alpine (container `keycloak-db`) |
| Modo | `start-dev` (dev) → `start` (produção) |

### Variáveis de Ambiente (`.env.keycloak`)

```env
# Hostname
KEYCLOAK_HOSTNAME=auth.intellicare.ia.br

# Admin
KEYCLOAK_ADMIN=admin
KEYCLOAK_ADMIN_PASSWORD=<secret>

# Database
KEYCLOAK_DB_NAME=keycloak_db
KEYCLOAK_DB_USER=keycloak_admin
KEYCLOAK_DB_PASSWORD=<secret>

# Portas
KEYCLOAK_HTTP_PORT=8080
KEYCLOAK_HTTPS_PORT=8443
```

### docker-compose.keycloak.yml — Resumo

```yaml
services:
  keycloak-db:
    image: postgres:15-alpine
    volumes: [keycloak_db_data:/var/lib/postgresql/data]
    healthcheck: pg_isready

  keycloak:
    image: quay.io/keycloak/keycloak:24.0
    command: start-dev --import-realm
    environment:
      KC_DB: postgres
      KC_REALM: bemcuidar
      KC_PROXY: edge            # Traefik termina TLS
      KC_HEALTH_ENABLED: "true"
      KC_METRICS_ENABLED: "true"
    volumes:
      - ./intellicare-auth/keycloak/import:/opt/keycloak/data/import:ro
    ports: ["8080:8080", "8443:8443"]
    labels:
      - "traefik.http.routers.keycloak.rule=Host(`auth.intellicare.ia.br`)"
      - "traefik.http.routers.keycloak.tls.certresolver=letsencrypt"
```

> **Nota:** `--import-realm` importa o arquivo `bemcuidar-realm.json` apenas na primeira inicialização.
> Nas execuções seguintes, o Keycloak ignora silenciosamente se o realm já existe.

---

## 🔑 Realm `bemcuidar` — Configuração

### Realm Settings

```json
{
  "realm": "bemcuidar",
  "displayName": "IntelliCare BemCuidar",
  "enabled": true,
  "sslRequired": "external",
  "registrationAllowed": false,
  "loginWithEmailAllowed": true,
  "duplicateEmailsAllowed": false,
  "resetPasswordAllowed": true,
  "editUsernameAllowed": false,
  "bruteForceProtected": true,
  "rememberMe": false,
  "accessTokenLifespan": 300,
  "ssoSessionIdleTimeout": 1800,
  "ssoSessionMaxLifespan": 2592000,
  "refreshTokenMaxReuse": 0,
  "defaultSignatureAlgorithm": "RS256"
}
```

### Realm Roles

| Role | Descrição | Composite? |
|------|-----------|------------|
| `PLATFORM_ADMIN` | Superadmin da plataforma | Não |
| `PLATFORM_SUPPORT` | Suporte técnico | Não |
| `PLATFORM_BILLING` | Faturamento | Não |
| `TENANT_GESTOR` | Admin do tenant/hospital | Não |
| `TENANT_OPERADOR` | Operador do tenant | Não |
| `CLINICO` | Profissional de saúde | Não |
| `MEDICO` | Médico (inclui CLINICO) | Sim → inclui `CLINICO` |
| `ENFERMEIRO` | Enfermeiro (inclui CLINICO) | Sim → inclui `CLINICO` |
| `RECEPCIONISTA` | Recepcionista | Não |
| `PACIENTE` | Paciente | Não |
| `default-roles-bemcuidar` | Roles padrão | Sim → `offline_access`, `uma_authorization` |

---

## 🔒 Clients — Configuração Detalhada

### `intellicare-portal` (Public)

```json
{
  "clientId": "intellicare-portal",
  "name": "IntelliCare Portal",
  "publicClient": true,
  "standardFlowEnabled": true,
  "implicitFlowEnabled": false,
  "directAccessGrantsEnabled": false,
  "redirectUris": [
    "https://app.intellicare.ia.br/*",
    "http://localhost:3001/*"
  ],
  "webOrigins": [
    "https://app.intellicare.ia.br",
    "http://localhost:3001"
  ],
  "attributes": {
    "pkce.code.challenge.method": "S256"
  },
  "protocolMappers": [
    "tenant_id_mapper",
    "tenants_mapper",
    "audience_mapper"
  ]
}
```

### `intellicare-admin` (Public)

```json
{
  "clientId": "intellicare-admin",
  "publicClient": true,
  "standardFlowEnabled": true,
  "redirectUris": [
    "https://admin.intellicare.ia.br/*",
    "http://localhost:3002/*"
  ],
  "attributes": {
    "pkce.code.challenge.method": "S256"
  }
}
```

### `intellicare-api` (Bearer-only)

```json
{
  "clientId": "intellicare-api",
  "bearerOnly": true,
  "standardFlowEnabled": false,
  "serviceAccountsEnabled": false
}
```

### Módulos Confidential (Padrão)

Template aplicado a: `intellicare-wanda`, `intellicare-florence`, `intellicare-oswaldo`, `intellicare-donabedian`, `intellicare-comunicacao`, `intellicare-geralda`, `intellicare-zilda`, `intellicare-minerva`, `intellicare-pierre`, `intellicare-grahame`, `intellicare-gestor`, `intellicare-nise`

```json
{
  "clientId": "intellicare-<modulo>",
  "publicClient": false,
  "serviceAccountsEnabled": true,
  "standardFlowEnabled": false,
  "directAccessGrantsEnabled": false,
  "secret": "<ver keycloak_client_secrets.json>"
}
```

### Client Secrets (`keycloak_client_secrets.json`)

```json
{
  "intellicare-admin":       "Adm1nS3cr3t-IC2026",
  "intellicare-portal":      "GGBueXp17E1eIAm0y1MyroZVqx0jJyEX",
  "intellicare-wanda":       "WVmIKFXeJxnyIMcsPvzyeE13lG5uZYfy",
  "intellicare-florence":    "ajjWcAieWJoN9HPYulExgdMsjnRb5N1R",
  "intellicare-oswaldo":     "hJMNZx2bhF1Wfqh31cpGwuphF7W2E340",
  "intellicare-donabedian":  "DKFaLrOoVrmUzsRFN6941x2LVyzjv4Cs",
  "intellicare-geralda":     "kihZ6pvwObfdg3UPoc1wUklbQmQp1PpB",
  "intellicare-zilda":       "VmS5niVQNxNF1gzO83gjbQdqwH13tly3",
  "intellicare-grahame":     "GrhS3cr3t-IC2026",
  "intellicare-comunicacao": "ZLF3w2SuQsJ8YxgCnitKRXYEqvThynTo",
  "intellicare-gestor":      "GstS3cr3t-IC2026",
  "intellicare-minerva":     "MnvS3cr3t-IC2026",
  "intellicare-pierre":      "PrrS3cr3t-IC2026",
  "intellicare-nise":        "NisS3cr3t-IC2026"
}
```

> ⚠️ **SEGURANÇA:** Este arquivo é lido por `configure_auth()` da biblioteca `intellicare-auth`.
> Em produção, usar variáveis de ambiente ou Vault. NUNCA commitá-lo em repositórios públicos.

---

## 📋 Protocol Mappers (Realm)

Os mappers garantem que o JWT contenha as claims necessárias para multi-tenancy:

### Mapper: `tenant_id`

```json
{
  "name": "tenant_id_mapper",
  "protocol": "openid-connect",
  "protocolMapper": "oidc-usermodel-attribute-mapper",
  "config": {
    "user.attribute": "tenant_id",
    "claim.name": "tenant_id",
    "jsonType.label": "String",
    "id.token.claim": "true",
    "access.token.claim": "true",
    "userinfo.token.claim": "true"
  }
}
```

### Mapper: `tenants` (array)

```json
{
  "name": "tenants_mapper",
  "protocol": "openid-connect",
  "protocolMapper": "oidc-usermodel-attribute-mapper",
  "config": {
    "user.attribute": "tenants",
    "claim.name": "tenants",
    "jsonType.label": "JSON",
    "multivalued": "true",
    "id.token.claim": "true",
    "access.token.claim": "true"
  }
}
```

### Mapper: `audience`

```json
{
  "name": "audience_mapper",
  "protocol": "openid-connect",
  "protocolMapper": "oidc-audience-mapper",
  "config": {
    "included.client.audience": "intellicare-api",
    "id.token.claim": "false",
    "access.token.claim": "true"
  }
}
```

---

## 🎫 Estrutura do JWT Access Token

```json
{
  "exp": 1741280100,
  "iat": 1741279800,
  "jti": "550e8400-e29b-41d4-a716-446655440000",
  "iss": "https://auth.intellicare.ia.br/realms/bemcuidar",
  "aud": ["intellicare-api", "account"],
  "sub": "f:abc123:user-uuid",
  "typ": "Bearer",
  "azp": "intellicare-portal",
  "session_state": "session-uuid",
  "acr": "1",
  "realm_access": {
    "roles": ["CLINICO", "MEDICO", "offline_access", "uma_authorization"]
  },
  "resource_access": {
    "intellicare-portal": {
      "roles": []
    },
    "account": {
      "roles": ["manage-account", "view-profile"]
    }
  },
  "scope": "openid profile email",
  "sid": "session-uuid",
  "email_verified": true,
  "tenant_id": "hospital-sao-joao",
  "tenants": ["hospital-sao-joao", "clinica-bem-cuidar"],
  "preferred_username": "dr.silva@hospital.com",
  "given_name": "Carlos",
  "family_name": "Silva",
  "name": "Dr. Carlos Silva",
  "email": "dr.silva@hospital.com"
}
```

**Claims principais:**

| Claim | Tipo | Descrição |
|-------|------|-----------|
| `sub` | String | ID único do usuário no Keycloak |
| `iss` | String | Issuer = `https://auth.intellicare.ia.br/realms/bemcuidar` |
| `realm_access.roles` | Array | Roles do realm (ex: `MEDICO`, `PLATFORM_ADMIN`) |
| `resource_access.{client}.roles` | Array | Roles específicas do client |
| `tenant_id` | String | Tenant ativo do usuário (custom claim) |
| `tenants` | Array | Todos os tenants do usuário (custom claim) |
| `preferred_username` | String | Username de login |
| `email` | String | Email do usuário |
| `exp` | Unix timestamp | Expiração do token (5 minutos padrão) |

---

## 📚 intellicare-auth — Biblioteca Python

### Localização

```
intellicare-auth/
├── intellicare_auth/
│   ├── __init__.py                    # Exports: KeycloakClient, configure_auth, etc.
│   ├── client.py                      # KeycloakClient — validação JWT, client credentials
│   ├── config.py                      # KeycloakConfig (pydantic-settings)
│   ├── fastapi.py                     # configure_auth(), require_role(), require_any_role()
│   ├── middleware.py                  # get_current_user(), get_optional_user(), get_user_roles()
│   ├── decorators.py                  # requires_role(), requires_any_role() (decorator style)
│   ├── exceptions.py                  # AuthenticationError, AuthorizationError, InvalidTokenError, KeycloakConnectionError
│   ├── tenant_middleware.py           # get_tenant_context() via JWT (importado por __init__.py)
│   ├── tenant_resolver_middleware.py  # Multi-fonte: JWT + Header + Subdomínio + Path
│   ├── access_middleware.py           # AccessPolicyMiddleware — injeta request.state.access_policy
│   ├── policy_resolver.py             # PolicyResolver — RBAC via Redis + DB
│   └── smart/                         # SMART-on-FHIR 2.0 (✅ implementado)
│       ├── __init__.py                # Exports: SmartConfiguration, EHRLaunchHandler, smart_router
│       ├── models.py                  # SmartConfiguration, LaunchContext, SmartTokenClaims
│       ├── router.py                  # smart_router: /.well-known/smart-configuration, /smart/launch
│       ├── launch_handler.py          # EHRLaunchHandler, StandaloneLaunchHandler
│       └── scope_translator.py        # smart_scopes_to_rules(), parse_smart_scopes()
├── keycloak/
│   └── import/
│       └── bemcuidar-realm.json       # Realm export (auto-importado no start)
├── keycloak_client_secrets.json       # Secrets de todos os módulos
└── pyproject.toml                     # ⚠️ packages path incorreto — ver issue #7
```

### Instalação (em cada módulo)

```toml
# pyproject.toml do módulo
[tool.poetry.dependencies]
intellicare-auth = {path = "../intellicare-auth", develop = true}
```

ou setuptools:

```toml
[project]
dependencies = [
    "intellicare-auth @ file:///${PROJECT_ROOT}/../intellicare-auth",
]
```

### Configuração por Variáveis de Ambiente

```env
# Obrigatórias
KEYCLOAK_CLIENT_ID=intellicare-florence
KEYCLOAK_CLIENT_SECRET=ajjWcAieWJoN9HPYulExgdMsjnRb5N1R

# Derivadas automaticamente do secrets file (ou setar manualmente)
KEYCLOAK_SERVER_URL=https://auth.intellicare.ia.br
KEYCLOAK_REALM=bemcuidar

# Opcionais
KEYCLOAK_JWKS_CACHE_TTL=300      # segundos (padrão: 5min)
KEYCLOAK_TOKEN_CACHE_TTL=60      # segundos (padrão: 1min)
KEYCLOAK_CONNECTION_TIMEOUT=10   # segundos
KEYCLOAK_READ_TIMEOUT=30         # segundos
KEYCLOAK_VERIFY_SSL=true
KEYCLOAK_VALIDATE_AUDIENCE=true
KEYCLOAK_VALIDATE_ISSUER=true
```

### `require_role` vs `requires_role` — Dois helpers distintos

A biblioteca expõe **duas formas** de controle de acesso por role:

| Função | Módulo | Estilo | Uso |
|--------|--------|--------|-----|
| `require_role("ROLE")` | `intellicare_auth.fastapi` | FastAPI `Depends()` | `user = Depends(require_role("PLATFORM_ADMIN"))` |
| `requires_role("ROLE")` | `intellicare_auth.decorators` | Decorator Python | `@requires_role("PLATFORM_ADMIN")` acima da função |

Prefira `require_role` (Depends) em endpoints FastAPI — é o padrão do projeto.

### Uso em FastAPI — Padrão Completo

```python
from fastapi import FastAPI, Depends
from intellicare_auth.fastapi import configure_auth, require_role, require_any_role
from intellicare_auth.middleware import get_current_user, get_optional_user, get_user_roles

app = FastAPI()

# 1. Configurar auth no startup (lê keycloak_client_secrets.json)
configure_auth(app, secrets_path="keycloak_client_secrets.json")


# 2. Endpoint público (sem auth)
@app.get("/api/v1/health")
async def health():
    return {"status": "ok"}


# 3. Endpoint autenticado (qualquer role)
@app.get("/api/v1/info")
async def info(user: dict = Depends(get_current_user)):
    return {
        "user": user["preferred_username"],
        "tenant": user.get("tenant_id"),
        "roles": get_user_roles(user)
    }


# 4. Endpoint com role específica
@app.delete("/api/v1/tenants/{tenant_id}")
async def delete_tenant(
    tenant_id: str,
    user: dict = Depends(require_role("PLATFORM_ADMIN")),
):
    return {"deleted": tenant_id}


# 5. Endpoint com qualquer uma das roles
@app.post("/api/v1/patients")
async def create_patient(
    user: dict = Depends(require_any_role(["MEDICO", "CLINICO", "ENFERMEIRO"]))
):
    return {"created": True}


# 6. Endpoint com autenticação opcional
@app.get("/api/v1/public-data")
async def public_data(user: dict | None = Depends(get_optional_user)):
    if user:
        return {"data": "personalized", "user": user["preferred_username"]}
    return {"data": "public"}
```

### KeycloakClient — API Detalhada

```python
from intellicare_auth.client import KeycloakClient
from intellicare_auth.config import KeycloakConfig

config = KeycloakConfig(
    client_id="intellicare-wanda",
    client_secret="WVmIKFXeJxnyIMcsPvzyeE13lG5uZYfy",
    server_url="https://auth.intellicare.ia.br",
    realm="bemcuidar",
)
client = KeycloakClient(config)

# Validar token JWT (local, sem chamar Keycloak)
payload = await client.validate_token(access_token)

# Obter token M2M (client credentials)
token_data = await client.get_client_token()
# → {"access_token": "...", "token_type": "Bearer", "expires_in": 300}

# Obter user info do endpoint /userinfo
user_info = await client.get_user_info(access_token)

# Introspectar token (fallback — chama Keycloak)
info = await client.introspect_token(access_token)

# Limpar caches (útil em testes)
client.clear_caches()
```

### Endpoints JWKS e Validação

```python
# JWKS URI (cacheado por 5min via PyJWKClient)
jwks_uri = "https://auth.intellicare.ia.br/realms/bemcuidar/protocol/openid-connect/certs"

# jwt.decode com PyJWKClient — sem chamada ao Keycloak por request
# ⚠️ ATENÇÃO: audience deve ser o client_id DO MÓDULO que está validando (não "intellicare-api")
# O KeycloakClient usa self.config.client_id como audience — garanta que o audience_mapper
# no Keycloak inclua o client_id do módulo em aud[], ou desative validate_audience.
payload = jwt.decode(
    token,
    signing_key.key,          # Chave pública RS256 do JWKS
    algorithms=["RS256"],
    audience=self.config.client_id,   # Ex: "intellicare-florence", "intellicare-wanda"
    issuer="https://auth.intellicare.ia.br/realms/bemcuidar",
    options={"verify_exp": True, "verify_aud": True, "verify_iss": True}
)
```

> ✅ **Validação de Audience — Resolvido:** `config.py` alterado para `validate_audience: bool = Field(default=False)`.
> A validação de audience está **desabilitada por padrão** — o código acima mostra `verify_aud: True` apenas
> quando `validate_audience=True` estiver configurado. A segurança é garantida pela assinatura RS256 + issuer.
> Para habilitar por módulo, setar `KEYCLOAK_VALIDATE_AUDIENCE=true` e adicionar um audience mapper
> no Keycloak que inclua o `client_id` do módulo em `aud[]`.

### Extração de Roles

```python
from intellicare_auth.middleware import get_user_roles

# Combina realm roles + resource/client roles
def get_user_roles(user: dict) -> list[str]:
    roles = []
    # Realm roles
    roles.extend(user.get("realm_access", {}).get("roles", []))
    # Client roles
    for client_roles in user.get("resource_access", {}).values():
        roles.extend(client_roles.get("roles", []))
    return list(set(roles))

# Exemplo de uso:
# user["realm_access"]["roles"] = ["MEDICO", "offline_access"]
# → get_user_roles(user) = ["MEDICO", "offline_access", "manage-account", ...]
```

---

## 🌐 Frontend — authService.ts (React 19)

### Variáveis de Ambiente (`.env.local` / `.env.production`)

```env
VITE_KEYCLOAK_URL=https://auth.intellicare.ia.br
VITE_KEYCLOAK_REALM=bemcuidar
VITE_KEYCLOAK_CLIENT_ID=intellicare-portal
```

> ⚠️ **ATENÇÃO:** O código atual tem `REALM` com fallback para `'intellicare'` (incorreto).
> Deve ser corrigido para `'bemcuidar'` ou configurado via `.env`.

### PKCE Flow — authService.ts

```typescript
const KEYCLOAK_URL = import.meta.env.VITE_KEYCLOAK_URL;
const REALM = import.meta.env.VITE_KEYCLOAK_REALM || 'bemcuidar';  // CORRETO
const CLIENT_ID = import.meta.env.VITE_KEYCLOAK_CLIENT_ID || 'intellicare-portal';

// 1. Gerar code_verifier + code_challenge (SHA-256)
function generateCodeVerifier(): string {
    const array = new Uint32Array(56 / 2);
    window.crypto.getRandomValues(array);
    return Array.from(array, dec => ('0' + dec.toString(16)).substr(-2)).join('');
}

async function generateCodeChallenge(verifier: string): Promise<string> {
    const data = new TextEncoder().encode(verifier);
    const digest = await window.crypto.subtle.digest('SHA-256', data);
    return btoa(String.fromCharCode(...new Uint8Array(digest)))
        .replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

// 2. Iniciar login — redireciona para Keycloak
export async function iniciarLogin(redirectAfter?: string): Promise<void> {
    const verifier = generateCodeVerifier();
    const challenge = await generateCodeChallenge(verifier);
    sessionStorage.setItem("pkce_verifier", verifier);
    if (redirectAfter) sessionStorage.setItem("redirect_after", redirectAfter);

    const params = new URLSearchParams({
        client_id: CLIENT_ID,
        redirect_uri: `${window.location.origin}/auth/callback`,
        response_type: "code",
        scope: "openid profile email",
        code_challenge: challenge,
        code_challenge_method: "S256",
        state: crypto.randomUUID(),
    });
    window.location.href = `${KEYCLOAK_URL}/realms/${REALM}/protocol/openid-connect/auth?${params}`;
}

// 3. Processar callback — troca code por tokens
export async function handleCallback(code: string): Promise<void> {
    const verifier = sessionStorage.getItem("pkce_verifier");
    if (!verifier) throw new Error("PKCE verifier not found");

    const resp = await fetch(`${KEYCLOAK_URL}/realms/${REALM}/protocol/openid-connect/token`, {
        method: "POST",
        headers: {"Content-Type": "application/x-www-form-urlencoded"},
        body: new URLSearchParams({
            grant_type: "authorization_code",
            code,
            redirect_uri: `${window.location.origin}/auth/callback`,
            client_id: CLIENT_ID,
            code_verifier: verifier,
        }),
    });
    const data = await resp.json();
    useAuthStore.getState().setTokens(data);  // Zustand — memória apenas
    sessionStorage.removeItem("pkce_verifier");
}

// 4. Refresh token
export async function refreshToken(): Promise<boolean> {
    const refresh_token = sessionStorage.getItem("refresh_token");
    if (!refresh_token) return false;
    const resp = await fetch(`${KEYCLOAK_URL}/realms/${REALM}/protocol/openid-connect/token`, {
        method: "POST",
        headers: {"Content-Type": "application/x-www-form-urlencoded"},
        body: new URLSearchParams({
            grant_type: "refresh_token",
            client_id: CLIENT_ID,
            refresh_token,
        }),
    });
    if (!resp.ok) { useAuthStore.getState().clear(); return false; }
    useAuthStore.getState().setTokens(await resp.json());
    return true;
}

// 5. Logout — invalida sessão SSO
export function logout(): void {
    useAuthStore.getState().clear();
    window.location.href = `${KEYCLOAK_URL}/realms/${REALM}/protocol/openid-connect/logout`
        + `?client_id=${CLIENT_ID}&post_logout_redirect_uri=${window.location.origin}/login`;
}
```

### RoleRouter.tsx

```tsx
import { Navigate } from 'react-router-dom';
import { useAuthStore } from '@store/authStore';
import { decodeToken } from '@utils/jwt';

export function RoleRouter() {
    const { token } = useAuthStore();
    if (!token) return <Navigate to="/login" />;

    const decoded = decodeToken(token);
    const roles: string[] = decoded?.realm_access?.roles ?? [];

    if (roles.includes('PLATFORM_ADMIN') ||
        roles.includes('PLATFORM_SUPPORT') ||
        roles.includes('PLATFORM_BILLING')) {
        return <Navigate to="/admin" />;
    }
    if (roles.includes('TENANT_GESTOR')) {
        return <Navigate to="/gestor" />;
    }
    if (roles.some(r => ['MEDICO', 'CLINICO', 'ENFERMEIRO', 'RECEPCIONISTA'].includes(r))) {
        return <Navigate to="/dashboard" />;
    }
    if (roles.includes('PACIENTE')) {
        return <Navigate to="/paciente" />;
    }

    return <Navigate to="/sem-acesso" />;
}
```

### TenantContext — Token Exchange

```typescript
// services/tokenExchange.ts
const WANDA_URL = import.meta.env.VITE_WANDA_URL || 'http://localhost:8004';

export async function exchangeTokenForTenant(
    token: string,
    tenantId: string
): Promise<string> {
    const resp = await fetch(`${WANDA_URL}/api/v1/token/exchange`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ tenant_id: tenantId }),
    });
    if (!resp.ok) throw new Error(`Token exchange failed: ${resp.status}`);
    const data = await resp.json();
    return data.access_token;
}
```

---

## 🏥 SMART-on-FHIR 2.0

> ✅ **Módulo já implementado** em `intellicare_auth/smart/`. Pendente: montar o `smart_router`
> no app.py do GRAHAME. Variáveis necessárias no `.env` do GRAHAME:
> `KEYCLOAK_BASE_URL` (⚠️ não `KEYCLOAK_SERVER_URL`) e `KEYCLOAK_REALM`.

### Variáveis de Ambiente do Módulo SMART

```env
# Usado por intellicare_auth/smart/router.py — nome DIFERENTE do padrão KeycloakConfig!
KEYCLOAK_BASE_URL=https://auth.intellicare.ia.br   # NÃO é KEYCLOAK_SERVER_URL
KEYCLOAK_REALM=bemcuidar
FHIR_BASE_URL=https://fhir.intellicare.ia.br
```

### Montar smart_router no GRAHAME

```python
# intellicare-grahame/grahame/api/app.py
from intellicare_auth.smart import smart_router

app = FastAPI()
app.include_router(smart_router)
# Expõe: GET /.well-known/smart-configuration
#         POST /smart/launch
#         GET  /smart/launch/validate/{token}
```

### Well-Known Configuration

```
GET https://auth.intellicare.ia.br/realms/bemcuidar/.well-known/smart-configuration
```

```json
{
  "issuer": "https://auth.intellicare.ia.br/realms/bemcuidar",
  "jwks_uri": "https://auth.intellicare.ia.br/realms/bemcuidar/protocol/openid-connect/certs",
  "authorization_endpoint": "https://auth.intellicare.ia.br/realms/bemcuidar/protocol/openid-connect/auth",
  "token_endpoint": "https://auth.intellicare.ia.br/realms/bemcuidar/protocol/openid-connect/token",
  "capabilities": [
    "launch-ehr",
    "launch-standalone",
    "client-public",
    "client-confidential-symmetric",
    "context-ehr-patient",
    "context-ehr-encounter",
    "permission-patient",
    "permission-user",
    "sso-openid-connect"
  ],
  "scopes_supported": [
    "openid", "profile", "email", "offline_access",
    "launch", "launch/patient", "launch/encounter",
    "patient/*.read", "patient/*.write",
    "user/*.read", "user/*.write",
    "system/*.read"
  ]
}
```

### EHR Launch Flow (GRAHAME)

```python
# intellicare-grahame/grahame/smart/launch.py
from intellicare_auth.smart.launch import SMARTLaunchHandler

handler = SMARTLaunchHandler(
    client_id="intellicare-grahame",
    client_secret="GrhS3cr3t-IC2026",
    redirect_uri="https://fhir.intellicare.ia.br/smart/callback",
)

# 1. Receber launch request do EHR
@router.get("/smart/launch")
async def smart_launch(launch: str, iss: str):
    auth_url = handler.build_auth_url(
        launch_token=launch,
        iss=iss,
        scope="launch openid profile patient/*.read",
    )
    return RedirectResponse(auth_url)

# 2. Processar callback
@router.get("/smart/callback")
async def smart_callback(code: str, state: str):
    token_response = await handler.exchange_code(code)
    patient_id = token_response.get("patient")
    encounter_id = token_response.get("encounter")
    # Usar patient_id/encounter_id para queries FHIR
    return {"patient": patient_id, "encounter": encounter_id}
```

---

## 🔧 Multi-Tenancy — Detalhamento Técnico

### Dois Middlewares de Tenant — Qual Usar?

| Arquivo | Importado por `__init__.py`? | Fontes de resolução | Quando usar |
|---------|------------------------------|---------------------|-------------|
| `tenant_middleware.py` | ✅ Sim (padrão) | JWT (`tenant_id` claim) | Todos os módulos com login obrigatório |
| `tenant_resolver_middleware.py` | ❌ Não (avançado) | JWT + Header `X-Tenant-ID` + Subdomínio + Path | Endpoints que precisam resolver tenant sem JWT (ex: login page, webhooks) |

Use sempre `from intellicare_auth import get_tenant_context` — vem de `tenant_middleware.py` via `__init__.py`.
Use `tenant_resolver_middleware.py` explicitamente apenas quando precisar de resolução multi-fonte.

### Fluxo no Backend Python

```python
# Padrão: importar via __init__.py (usa tenant_middleware.py internamente)
from intellicare_auth import get_tenant_context

async def get_tenant_context(user: dict = Depends(get_current_user)) -> TenantContext:
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(
            status_code=428,  # Precondition Required
            detail="tenant_id ausente no token. Faça token exchange via /api/v1/token/exchange"
        )
    return TenantContext(tenant_id=tenant_id, schema=f"tenant_{tenant_id}")

# Uso em endpoint
@router.get("/api/v1/patients")
async def list_patients(
    user: dict = Depends(get_current_user),
    tenant: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    # db já está configurado para o schema do tenant via TenantAwareSessionFactory
    patients = await PatientRepository(db, tenant.schema).list()
    return patients
```

### Token Exchange em WANDA

```python
# intellicare-wanda/wanda/api/token_exchange.py
@router.post("/api/v1/token/exchange")
async def exchange_token(
    request: TokenExchangeRequest,
    current_user: dict = Depends(get_current_user),
):
    tenant_id = request.tenant_id
    # Validar que usuário tem acesso ao tenant solicitado
    user_tenants = current_user.get("tenants", [])
    if tenant_id not in user_tenants:
        raise HTTPException(403, "Acesso negado ao tenant solicitado")

    # Criar token enriquecido com tenant_id
    # (implementação via Keycloak Token Exchange ou JWT customizado)
    new_token = await create_tenant_token(current_user, tenant_id)
    return {"access_token": new_token, "tenant_id": tenant_id}
```

---

## 📊 Endpoints OIDC Keycloak — Referência Completa

```
# Realm base
https://auth.intellicare.ia.br/realms/bemcuidar

# OIDC Discovery
GET /realms/bemcuidar/.well-known/openid-configuration

# Authorization (login)
GET /realms/bemcuidar/protocol/openid-connect/auth
    ?client_id=intellicare-portal
    &response_type=code
    &redirect_uri=https://app.intellicare.ia.br/auth/callback
    &scope=openid profile email
    &code_challenge=<S256_challenge>
    &code_challenge_method=S256
    &state=<random>

# Token exchange
POST /realms/bemcuidar/protocol/openid-connect/token
    grant_type=authorization_code
    code=<code>
    redirect_uri=<same_as_auth>
    client_id=intellicare-portal
    code_verifier=<original_verifier>

# Refresh
POST /realms/bemcuidar/protocol/openid-connect/token
    grant_type=refresh_token
    client_id=intellicare-portal
    refresh_token=<refresh_token>

# Client Credentials (M2M)
POST /realms/bemcuidar/protocol/openid-connect/token
    grant_type=client_credentials
    client_id=intellicare-wanda
    client_secret=WVmIKFXeJxnyIMcsPvzyeE13lG5uZYfy

# UserInfo
GET /realms/bemcuidar/protocol/openid-connect/userinfo
    Authorization: Bearer <access_token>

# JWKS (chaves públicas)
GET /realms/bemcuidar/protocol/openid-connect/certs

# Introspection
POST /realms/bemcuidar/protocol/openid-connect/token/introspect
    token=<access_token>
    client_id=<client_id>
    client_secret=<secret>

# Logout
GET /realms/bemcuidar/protocol/openid-connect/logout
    ?client_id=intellicare-portal
    &post_logout_redirect_uri=https://app.intellicare.ia.br/login

# Admin REST API (requer token de admin)
GET  /admin/realms/bemcuidar/users
POST /admin/realms/bemcuidar/users
GET  /admin/realms/bemcuidar/users/{id}/role-mappings/realm
POST /admin/realms/bemcuidar/users/{id}/role-mappings/realm

# Health
GET /health/ready    → {"status": "UP"}
GET /health/live     → {"status": "UP"}
GET /metrics         → Prometheus metrics
```

---

## ⚙️ Configuração Traefik (Produção)

```yaml
# traefik/dynamic/keycloak.yml
http:
  routers:
    keycloak:
      rule: "Host(`auth.intellicare.ia.br`)"
      entrypoints: ["websecure"]
      service: keycloak
      tls:
        certResolver: letsencrypt
      middlewares:
        - keycloak-headers

  middlewares:
    keycloak-headers:
      headers:
        customRequestHeaders:
          X-Forwarded-Proto: "https"
        forceSTSHeader: true
        stsSeconds: 31536000

  services:
    keycloak:
      loadBalancer:
        servers:
          - url: "http://keycloak-intellicare:8080"
```

---

*Gerado em: 2026-03-06 | Responsável: Eduardo Garabini*
