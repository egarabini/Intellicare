# ESPECIFICAÇÃO TÉCNICA — Admin + Gestor + Portal Auth

**Data**: 2026-03-05
**Status**: 🟡 Em Especificação
**Prioridade**: 🚀 P0 — Crítica
**Versão**: 2.0.2
**Rastreabilidade**: 01_ESPECIFICACAO_FUNCIONAL.md

---

## 📋 Índice

1. [Arquitetura dos Módulos](#1-arquitetura-dos-módulos)
2. [Fluxo PKCE — Detalhe Técnico](#2-fluxo-pkce--detalhe-técnico)
3. [intellicare-admin — Backend](#3-intellicare-admin--backend)
4. [intellicare-gestor — Backend](#4-intellicare-gestor--backend)
5. [Portal Frontend](#5-portal-frontend)
6. [Keycloak — Configuração Completa](#6-keycloak--configuração-completa)
7. [CORS e Segurança](#7-cors-e-segurança)

---

## 🏗️ 1. Arquitetura dos Módulos

```
                    ┌──────────────────────────────────┐
                    │     intellicare-portal           │
                    │     React 19 + Vite 7            │
                    │     porta 3001                   │
                    │                                  │
                    │  /login    /admin    /gestor     │
                    └──────┬─────────┬────────┬────────┘
                           │         │        │
                    Keycloak      8010     8011
                    OIDC/PKCE      │        │
                           │       ▼        ▼
                           │  ┌─────────┐ ┌──────────┐
                           │  │ admin   │ │ gestor   │
                           │  │ FastAPI │ │ FastAPI  │
                           └► │ porta   │ │ porta    │
                              │ 8010    │ │ 8011     │
                              └────┬────┘ └────┬─────┘
                                   │            │
                              ┌────▼────────────▼────┐
                              │     PostgreSQL 15     │
                              │  schema: platform     │
                              │  schema: {tenant_id}  │
                              └──────────────────────┘
```

| Módulo | Porta | Schema DB | Responsabilidade |
|--------|-------|-----------|------------------|
| `intellicare-admin` | 8010 | `platform` | CRUD tenants, planos, módulos, gestores, contratos, auditoria global |
| `intellicare-gestor` | 8011 | `{tenant_id}` | CRUD usuários, unidades, roles, configurações por tenant |
| `intellicare-portal` (frontend) | 3001 | — | React: serve `/admin`, `/gestor`, `/dashboard`, `/login` |
| Keycloak | 8080 | `keycloak` (PG) | OIDC provider: autenticação, roles, JWT |

---

## 🔐 2. Fluxo PKCE — Detalhe Técnico

```
Frontend                          Keycloak                    Backend
   │                                  │                          │
   │ 1. gera code_verifier (64 bytes) │                          │
   │ 2. code_challenge = SHA256(verifier) base64url              │
   │                                  │                          │
   │──── GET /auth?code_challenge=... ►│                          │
   │                                  │                          │
   │◄── redirect com ?code=xxxx ───── │                          │
   │                                  │                          │
   │──── POST /token {code, verifier} ►│                          │
   │◄── {access_token, refresh_token} ─│                          │
   │                                  │                          │
   │ Armazena em memória (Zustand)    │                          │
   │                                  │                          │
   │──── GET /admin/dashboard ─────────────────────────────────► │
   │     Authorization: Bearer {access_token}                    │
   │                                  │  verify JWT (RS256)      │
   │                                  │  check realm_roles       │
   │◄─────────────────────────────────────────── 200 JSON ────── │
```

**Passos numerados:**

1. Frontend gera `code_verifier` (64 bytes random, base64url)
2. `code_challenge = base64url(SHA256(code_verifier))`
3. `GET /realms/intellicare/protocol/openid-connect/auth?client_id=intellicare-portal&response_type=code&scope=openid+profile&code_challenge=...&code_challenge_method=S256`
4. Usuário autentica no Keycloak → retorna `?code=xxxx`
5. `POST /token` com `{ code, redirect_uri, code_verifier, grant_type: authorization_code }`
6. Resposta: `{ access_token, id_token, refresh_token, expires_in }`
7. `access_token` → Zustand store (memória). `refresh_token` → sessionStorage
8. Cada request: `Authorization: Bearer {access_token}`
9. Backend valida JWT (RS256, `iss`, `exp`, `azp`) e extrai `roles` / `tenant_id`

---

## ⚙️ 3. intellicare-admin — Backend

### 3.1 Arquivos: o que existe e o que criar

| Arquivo | Status | Ação |
|---------|--------|------|
| `admin/api/app.py` | ✅ Existe | Adicionar `require_platform_admin` dependency |
| `admin/api/deps.py` | ⚠️ Incompleto | `get_actor_id` tem fallback sem auth — **SUBSTITUIR** |
| `admin/api/tenant_routes.py` | ✅ Existe | Aplicar `require_platform_admin` em todos endpoints |
| `admin/api/plan_routes.py` | ⚠️ Parcial | Expandir `GET /admin/dashboard` |
| `admin/api/gestor_routes.py` | ❌ Criar | Endpoints gestores por tenant |
| `admin/api/contrato_routes.py` | ❌ Criar | Endpoints de contratos |
| `admin/models/tenant_gestor.py` | ❌ Criar | ORM TenantGestor |
| `admin/models/tenant_contrato.py` | ❌ Criar | ORM TenantContrato |
| `migrations/xxx_gestores_contratos.py` | ❌ Criar | Migration Alembic |

---

### 3.2 Dependency: `require_platform_admin`

```python
# admin/api/deps.py
from fastapi.security import OAuth2PasswordBearer
from intellicare_auth.jwt import verify_jwt, IntelliCareJWTError

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

async def require_platform_admin(
    token: str = Depends(oauth2_scheme)
) -> dict:
    if not token:
        raise HTTPException(status_code=401, detail="Token ausente")
    try:
        payload = verify_jwt(token, required_roles=["PLATFORM_ADMIN"])
        return payload
    except IntelliCareJWTError as e:
        raise HTTPException(status_code=403, detail=f"Acesso negado: {e}")

# Aplicar em TODOS os routers:
router = APIRouter(dependencies=[Depends(require_platform_admin)])
```

---

### 3.3 Contratos de API — intellicare-admin

| Método | Endpoint | Descrição | Response |
|--------|----------|-----------|----------|
| `GET` | `/admin/dashboard` | KPIs globais + módulos populares + atividades | `DashboardResponse` |
| `GET` | `/admin/tenants` | Lista paginada (page, size, status, q) | `{ items, total, page }` |
| `POST` | `/admin/tenants` | Cria tenant + provisiona schema + Keycloak realm | `TenantResponse` (201) |
| `GET` | `/admin/tenants/{id}` | Detalhe com módulos habilitados | `TenantDetailResponse` |
| `PATCH` | `/admin/tenants/{id}` | Atualiza dados cadastrais e branding | `TenantResponse` |
| `POST` | `/admin/tenants/{id}/suspend` | Suspende tenant `{ motivo }` | `204` |
| `POST` | `/admin/tenants/{id}/reactivate` | Reativa tenant suspenso | `204` |
| `GET` | `/admin/tenants/{id}/modules` | Lista módulos com status habilitado | `List[ModuleStatus]` |
| `PATCH` | `/admin/tenants/{id}/modules` | Habilita/desabilita módulo `{ module_name, enabled }` | `204` |
| `GET` | `/admin/tenants/{id}/gestores` | Lista gestores do tenant | `List[GestorResponse]` |
| `POST` | `/admin/tenants/{id}/gestores` | Cria gestor (Keycloak + BD) | `GestorResponse` (201) |
| `DELETE` | `/admin/tenants/{id}/gestores/{uid}` | Remove role `TENANT_GESTOR` | `204` |
| `GET` | `/admin/tenants/{id}/contrato` | Contrato vigente + histórico | `ContratoResponse` |
| `POST` | `/admin/tenants/{id}/contrato` | Cria/renova contrato | `ContratoResponse` (201) |
| `PATCH` | `/admin/tenants/{id}/contrato` | Atualiza vigência ou plano | `ContratoResponse` |
| `GET` | `/admin/tenants/{id}/audit` | Log paginado do tenant | `AuditPage` |

---

### 3.4 Schemas Pydantic — Admin

```python
# TenantCreate
class TenantCreate(BaseModel):
    nome_fantasia: str = Field(min_length=3, max_length=100)
    razao_social: str
    cnpj: str  # validado com check_cnpj()
    email_admin: EmailStr
    telefone: str | None = None
    plan_id: UUID
    dominio_customizado: str | None = None  # ex: "hsaolucas"

# TenantGestorCreate
class TenantGestorCreate(BaseModel):
    nome: str
    email: EmailStr
    telefone: str | None = None

# TenantContratoCreate
class TenantContratoCreate(BaseModel):
    plan_id: UUID
    inicio_vigencia: date
    fim_vigencia: date | None = None
    valor_mensal: Decimal
    obs: str | None = None

# DashboardResponse
class DashboardResponse(BaseModel):
    totais: dict  # { tenants, ativos, suspensos, trial }
    modulos_mais_usados: list[dict]  # [{ nome, tenants_ativos }]
    gestores_totais: int
    ultimas_atividades: list[AuditEntry]
```

---

### 3.5 Modelos ORM — tabelas a criar

```python
# platform.tenant_gestores
class TenantGestor(Base):
    __tablename__ = "tenant_gestores"
    __table_args__ = {"schema": "platform"}

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[str] = mapped_column(
        ForeignKey("platform.tenants.tenant_id")
    )
    keycloak_user_id: Mapped[str] = mapped_column(String(255), unique=True)
    nome: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255))
    telefone: Mapped[str | None]
    active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now())

# platform.tenant_contratos
class TenantContrato(Base):
    __tablename__ = "tenant_contratos"
    __table_args__ = {"schema": "platform"}

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[str] = mapped_column(
        ForeignKey("platform.tenants.tenant_id")
    )
    plan_id: Mapped[UUID] = mapped_column(ForeignKey("platform.plans.id"))
    inicio_vigencia: Mapped[date]
    fim_vigencia: Mapped[date | None]
    valor_mensal: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    obs: Mapped[str | None]
    created_at: Mapped[datetime] = mapped_column(default=func.now())
```

---

## ⚙️ 4. intellicare-gestor — Backend

### 4.1 Arquivos: o que existe e o que criar

| Arquivo | Status | Ação |
|---------|--------|------|
| `gestor/api/user_routes.py` | ✅ Existe | Aplicar `require_tenant_gestor` em todos endpoints |
| `gestor/api/sector_routes.py` | ✅ Existe | Aplicar auth + `POST /sectors/{id}/users` |
| `gestor/api/dashboard_routes.py` | ⚠️ Parcial | Expandir: `por_unidade` + alertas |
| `gestor/api/deps.py` | ⚠️ Incompleto | Adicionar `require_tenant_gestor` com isolamento |
| `gestor/api/modulos_routes.py` | ❌ Criar | `GET /gestor/modulos-habilitados` com cache Redis |

---

### 4.2 Dependency: `require_tenant_gestor`

```python
# gestor/api/deps.py
async def require_tenant_gestor(
    token: str = Depends(oauth2_scheme)
) -> TenantContext:
    if not token:
        raise HTTPException(status_code=401, detail="Token ausente")
    try:
        payload = verify_jwt(token, required_roles=["TENANT_GESTOR"])
        tenant_id = payload.get("tenant_id")
        if not tenant_id:
            raise HTTPException(
                status_code=403,
                detail="tenant_id ausente no token"
            )
        return TenantContext(tenant_id=tenant_id, user_id=payload["sub"])
    except IntelliCareJWTError as e:
        raise HTTPException(status_code=403, detail=str(e))
```

---

### 4.3 Contratos de API — intellicare-gestor

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `GET` | `/gestor/dashboard` | KPIs + por_unidade + alertas + atividades |
| `GET` | `/gestor/modulos-habilitados` | Módulos ativos do tenant (cache Redis 5min) |
| `GET` | `/gestor/users` | Lista usuários (filtros: q, sector_id, cargo, active) |
| `POST` | `/gestor/users` | Cria usuário no tenant |
| `PATCH` | `/gestor/users/{id}` | Atualiza dados do usuário |
| `DELETE` | `/gestor/users/{id}` | Soft delete (active=false) |
| `GET` | `/gestor/sectors` | Árvore hierárquica de setores |
| `POST` | `/gestor/sectors` | Cria setor/unidade |
| `PATCH` | `/gestor/sectors/{id}` | Atualiza setor |
| `DELETE` | `/gestor/sectors/{id}` | Soft delete (valida filhos) |
| `POST` | `/gestor/sectors/{id}/users` | Associa `{ user_ids: [uuid] }` ao setor |
| `DELETE` | `/gestor/sectors/{id}/users/{uid}` | Remove usuário do setor |
| `GET` | `/gestor/settings` | Configurações do tenant |
| `PATCH` | `/gestor/settings` | Atualiza configurações |
| `GET` | `/gestor/audit` | Log paginado do tenant |

---

### 4.4 Cache Redis — módulos habilitados

```python
# gestor/api/modulos_routes.py
@router.get("/modulos-habilitados")
async def get_modulos_habilitados(
    ctx: TenantContext = Depends(require_tenant_gestor),
    redis=Depends(get_redis),
):
    cache_key = f"gestor:{ctx.tenant_id}:modulos"
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)

    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"http://intellicare-admin:8010/admin/tenants/{ctx.tenant_id}/modules",
            headers={"X-Internal-Auth": settings.internal_token},
        )
    r.raise_for_status()
    data = r.json()
    await redis.setex(cache_key, 300, json.dumps(data))  # TTL 5 min
    return data
```

---

### 4.5 Dashboard expandido — response schema

```json
{
  "resumo": {
    "total_unidades": 8,
    "total_usuarios": 124,
    "usuarios_ativos": 118,
    "usuarios_sem_unidade": 6
  },
  "por_unidade": [
    {
      "id": "uuid",
      "nome": "UTI Adulto",
      "tipo": "UTI",
      "usuarios_ativos": 15,
      "responsavel": "Dr. João Silva"
    }
  ],
  "ultimas_atividades": [...],
  "alertas": [
    { "tipo": "usuario_sem_unidade", "count": 6 }
  ]
}
```

---

## 💻 5. Portal Frontend

### 5.1 Componentes a criar

| Arquivo (`src/`) | Responsabilidade |
|------------------|------------------|
| `pages/Login/index.tsx` | Tela de login + branding white-label |
| `pages/Login/AuthCallback.tsx` | Handler do redirect Keycloak (`?code=...`) |
| `components/auth/RoleRouter.tsx` | Lê roles e chama `navigate()` para rota correta |
| `components/auth/ProtectedRoute.tsx` | HOC: verifica auth + role mínima |
| `hooks/useAuth.ts` | Expõe: user, token, roles, tenantId, isAuthenticated, logout |
| `services/authService.ts` | `iniciarLogin()`, `handleCallback()`, `refreshToken()`, `logout()` |
| `store/authStore.ts` | Zustand: accessToken, user, roles, tenantId, expiry |
| `pages/Admin/layout/AdminLayout.tsx` | Sidebar + header + Outlet |
| `pages/Admin/Dashboard.tsx` | KPIs + gráfico + alertas + atividades |
| `pages/Admin/Tenants/List.tsx` | Tabela paginada + filtros |
| `pages/Admin/Tenants/Detail.tsx` | 5 abas: Dados / Módulos / Gestores / Contrato / Auditoria |
| `pages/Gestor/layout/GestorLayout.tsx` | Layout com white-label |
| `pages/Gestor/Dashboard.tsx` | KPIs + alertas + mini-tabela |
| `pages/Gestor/Unidades.tsx` | Árvore hierárquica + modais CRUD |
| `pages/Gestor/Usuarios.tsx` | Lista + filtros + highlights + modais |
| `pages/Gestor/Configuracoes.tsx` | Fuso + e-mails alerta + contrato read-only |
| `components/UnidadeTree.tsx` | Componente reutilizável de árvore |

---

### 5.2 authService.ts

```typescript
// Gera PKCE e inicia redirect para Keycloak
export function iniciarLogin(redirectAfter?: string): void {
  const verifier = generateCodeVerifier()  // 64 bytes random base64url
  const challenge = await generateCodeChallenge(verifier)  // SHA-256
  sessionStorage.setItem("pkce_verifier", verifier)
  sessionStorage.setItem("redirect_after", redirectAfter ?? "/")
  const params = new URLSearchParams({
    client_id: KEYCLOAK_CLIENT_ID,
    redirect_uri: `${window.location.origin}/auth/callback`,
    response_type: "code",
    scope: "openid profile email",
    code_challenge: challenge,
    code_challenge_method: "S256",
    state: crypto.randomUUID(),
  })
  window.location.href =
    `${KEYCLOAK_URL}/protocol/openid-connect/auth?${params}`
}

// Troca code por tokens
export async function handleCallback(code: string): Promise<void> {
  const verifier = sessionStorage.getItem("pkce_verifier")!
  const body = new URLSearchParams({
    grant_type: "authorization_code",
    code,
    redirect_uri: `${window.location.origin}/auth/callback`,
    client_id: KEYCLOAK_CLIENT_ID,
    code_verifier: verifier,
  })
  const resp = await fetch(
    `${KEYCLOAK_URL}/protocol/openid-connect/token`,
    { method: "POST", body,
      headers: { "Content-Type": "application/x-www-form-urlencoded" } }
  )
  const data = await resp.json()
  useAuthStore.getState().setTokens(data)  // Zustand (memória)
}
```

---

### 5.3 RoleRouter.tsx

```typescript
export function RoleRouter() {
  const { roles } = useAuth()
  const navigate = useNavigate()

  useEffect(() => {
    if (roles.includes("PLATFORM_ADMIN"))
      navigate("/admin", { replace: true })
    else if (roles.includes("TENANT_GESTOR"))
      navigate("/gestor", { replace: true })
    else if (roles.some(r => ["CLINICO","MEDICO","ENFERMEIRO"].includes(r)))
      navigate("/dashboard", { replace: true })
    else
      navigate("/sem-permissao", { replace: true })
  }, [roles])

  return <div>Redirecionando...</div>
}
```

---

### 5.4 Roteamento React Router v7

```typescript
// routes.tsx
<Routes>
  <Route path="/login" element={<Login />} />
  <Route path="/auth/callback" element={<AuthCallback />} />
  <Route path="/sem-permissao" element={<SemPermissao />} />

  {/* Área Admin */}
  <Route element={<ProtectedRoute requiredRole="PLATFORM_ADMIN" />}>
    <Route path="/admin" element={<AdminLayout />}>
      <Route index element={<AdminDashboard />} />
      <Route path="tenants" element={<TenantList />} />
      <Route path="tenants/:id" element={<TenantDetail />} />
      <Route path="planos" element={<Planos />} />
      <Route path="auditoria" element={<AuditoriaGlobal />} />
    </Route>
  </Route>

  {/* Área Gestor */}
  <Route element={<ProtectedRoute requiredRole="TENANT_GESTOR" />}>
    <Route path="/gestor" element={<GestorLayout />}>
      <Route index element={<GestorDashboard />} />
      <Route path="unidades" element={<Unidades />} />
      <Route path="usuarios" element={<Usuarios />} />
      <Route path="configuracoes" element={<Configuracoes />} />
    </Route>
  </Route>

  <Route path="*" element={<Navigate to="/login" />} />
</Routes>
```

---

### 5.5 store/authStore.ts

```typescript
interface AuthState {
  accessToken: string | null
  refreshToken: string | null
  user: { sub: string; name: string; email: string } | null
  roles: string[]
  tenantId: string | null
  expiry: number | null  // Unix timestamp
  setTokens: (data: TokenResponse) => void
  clear: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  accessToken: null,
  refreshToken: null,
  user: null,
  roles: [],
  tenantId: null,
  expiry: null,
  setTokens: (data) => {
    const payload = parseJwt(data.access_token)
    set({
      accessToken: data.access_token,
      refreshToken: data.refresh_token,
      user: { sub: payload.sub, name: payload.name, email: payload.email },
      roles: payload.realm_roles ?? [],
      tenantId: payload.tenant_id ?? null,
      expiry: Date.now() + data.expires_in * 1000,
    })
    // refresh_token vai para sessionStorage (sobrevive ao F5)
    sessionStorage.setItem("refresh_token", data.refresh_token)
  },
  clear: () => {
    sessionStorage.removeItem("refresh_token")
    set({ accessToken: null, refreshToken: null, user: null,
          roles: [], tenantId: null, expiry: null })
  },
}))
```

---

## 🔑 6. Keycloak — Configuração Completa

### 6.1 Configuração do Client `intellicare-portal`

| Parâmetro | Valor |
|-----------|-------|
| **Client ID** | `intellicare-portal` |
| **Access Type** | `public` (sem client_secret no frontend) |
| **Standard Flow** | `ON` (Authorization Code) |
| **Implicit Flow** | `OFF` (deprecated) |
| **Valid Redirect URIs** | `https://portal.intellicare.ia.br/*` \| `http://localhost:3001/*` |
| **Web Origins** | `https://portal.intellicare.ia.br` \| `http://localhost:3001` |

### 6.2 Mappers obrigatórios no client

| Mapper | Tipo | User Attribute / Source | Token Claim Name | Access Token |
|--------|------|------------------------|------------------|:----------:|
| `realm_roles` | User Realm Role | — | `realm_roles` | ✅ |
| `tenant_id` | User Attribute | `tenant_id` | `tenant_id` | ✅ |

### 6.3 Roles do realm `intellicare`

| Role | Descrição |
|------|-----------|
| `PLATFORM_ADMIN` | Superadmin IntelliCare — acessa `/admin` completo |
| `TENANT_GESTOR` | Admin local do tenant — acessa `/gestor` |
| `CLINICO` | Profissional de saúde genérico |
| `MEDICO` | Médico (herda CLINICO) |
| `ENFERMEIRO` | Enfermeiro (herda CLINICO) |
| `PACIENTE` | Paciente — escopo futuro |

### 6.4 Atributo `tenant_id` no usuário

```
Keycloak Admin → Users → [usuário] → Attributes → Add
Key: tenant_id  |  Value: hospital_sao_lucas
```

> O `ProvisioningService` do `intellicare-admin` já faz isso automaticamente ao provisionar um novo tenant.

---

## 🛡️ 7. CORS e Segurança

### 7.1 CORS nos backends (admin + gestor)

```python
# Aplicar em cada app.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    # White-label: aceita qualquer subdomínio intellicare
    allow_origin_regex=r"https://[a-z0-9-]+\.intellicare\.ia\.br",
    allow_origins=[
        "https://portal.intellicare.ia.br",
        "http://localhost:3001",
    ],
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Tenant-ID"],
    allow_credentials=True,
)
```

### 7.2 Checklist de segurança

| Item | Status | Detalhe |
|------|--------|---------|
| PKCE obrigatório | ✅ | `code_challenge_method=S256` |
| `access_token` não vai para `localStorage` | ✅ | Zustand memória |
| `refresh_token` em `sessionStorage` | ✅ | Sobrevive F5, não a novo tab |
| Implicit Flow desabilitado no Keycloak | ✅ | `implicitFlowEnabled: false` |
| JWT validado com chave pública RS256 | ✅ | Via `intellicare_auth.jwt.verify_jwt` |
| `tenant_id` extraído do JWT (nunca do body) | ✅ | RN-01 |
| HTTP 401 sem token, 403 sem role | ✅ | `require_platform_admin`, `require_tenant_gestor` |
| Logs de auditoria em todas as ações destrutivas | ✅ | `platform.audit_logs` / `LocalAuditLog` |

---

*Documento gerado em: 2026-03-05 | Versão: 2.0.2 | Confidencial — IntelliCare © 2026*
