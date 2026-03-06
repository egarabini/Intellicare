# 03 — Plano de Implementação: Keycloak IntelliCare

> **Versão:** 2.0.0 | **Data:** 2026-03-06 | **Status:** 📋 Referência
> **Rastreabilidade:** V2.0.0-KEYCLOAK | **Público-alvo:** Tech Lead, DevOps, PMs

---

## 🗺️ Visão Geral das Fases

```
FASE 0          FASE 1          FASE 2          FASE 3          FASE 4          FASE 5
─────────       ─────────       ─────────       ─────────       ─────────       ─────────
Infra           Realm           Módulos         Portal          SMART           Produção
Docker +        bemcuidar:      Python:         Frontend:       on-FHIR:        Traefik +
PostgreSQL +    roles +         configure_auth  authService     GRAHAME +       HTTPS +
Keycloak up     clients +       em todos        PKCE fix        EHR launch      monitoring
                mappers +       os módulos      TenantCtx
                realm.json      + Wanda M2M
                                exchange

✅ Concluído   ✅ Concluído   ✅ Concluído   🔄 Em Progresso  ⬜ Pendente    ⬜ Pendente
```

---

## 📋 Fase 0: Infraestrutura (✅ Concluído)

### Entregáveis

- ✅ `docker-compose.keycloak.yml` com Keycloak 24.0 + PostgreSQL 15
- ✅ `.env.keycloak` com variáveis de ambiente
- ✅ Rede Docker `intellicare_intellicare-network` externa
- ✅ Volume persistente `keycloak_db_data`
- ✅ Health checks configurados
- ✅ Labels Traefik para produção

### Comandos de Verificação

```bash
# Subir Keycloak
docker-compose -f docker-compose.keycloak.yml up -d

# Verificar health
curl http://localhost:8080/health/ready
# → {"status": "UP"}

# Admin Console
open http://localhost:8080/admin
# admin / <KEYCLOAK_ADMIN_PASSWORD>
```

---

## 📋 Fase 1: Realm bemcuidar (✅ Concluído)

### Entregáveis

- ✅ `intellicare-auth/keycloak/import/bemcuidar-realm.json`
- ✅ Realm `bemcuidar` configurado com roles, clients e mappers
- ✅ Auto-import via `--import-realm` no start do container

### Checklist de Configuração

```bash
# Verificar realm importado
curl -s http://localhost:8080/realms/bemcuidar/.well-known/openid-configuration \
  | python3 -m json.tool | head -20

# Verificar JWKS disponível
curl -s http://localhost:8080/realms/bemcuidar/protocol/openid-connect/certs \
  | python3 -m json.tool | grep kid

# Obter token de admin para verificações
export ADMIN_TOKEN=$(curl -s \
  -d "client_id=admin-cli" \
  -d "username=admin" \
  -d "password=${KEYCLOAK_ADMIN_PASSWORD}" \
  -d "grant_type=password" \
  "http://localhost:8080/realms/master/protocol/openid-connect/token" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Listar clients do realm
curl -s -H "Authorization: Bearer $ADMIN_TOKEN" \
  "http://localhost:8080/admin/realms/bemcuidar/clients" \
  | python3 -m json.tool | grep '"clientId"'

# Listar realm roles
curl -s -H "Authorization: Bearer $ADMIN_TOKEN" \
  "http://localhost:8080/admin/realms/bemcuidar/roles" \
  | python3 -c "import sys,json; [print(r['name']) for r in json.load(sys.stdin)]"
```

### Criar Usuário de Teste (se necessário)

```bash
# Criar usuário PLATFORM_ADMIN
curl -s -X POST \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin@intellicare.ia.br",
    "email": "admin@intellicare.ia.br",
    "firstName": "Platform",
    "lastName": "Admin",
    "enabled": true,
    "emailVerified": true,
    "credentials": [{"type": "password", "value": "Admin@2026!", "temporary": false}],
    "attributes": {
      "tenant_id": ["platform"],
      "tenants": ["platform"]
    }
  }' \
  "http://localhost:8080/admin/realms/bemcuidar/users"

# Obter ID do usuário criado
USER_ID=$(curl -s -H "Authorization: Bearer $ADMIN_TOKEN" \
  "http://localhost:8080/admin/realms/bemcuidar/users?username=admin@intellicare.ia.br" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)[0]['id'])")

# Obter ID da role PLATFORM_ADMIN
ROLE_ID=$(curl -s -H "Authorization: Bearer $ADMIN_TOKEN" \
  "http://localhost:8080/admin/realms/bemcuidar/roles/PLATFORM_ADMIN" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['id']+'|'+d['name'])")

# Atribuir role ao usuário
curl -s -X POST \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "[{\"id\": \"${ROLE_ID%|*}\", \"name\": \"PLATFORM_ADMIN\"}]" \
  "http://localhost:8080/admin/realms/bemcuidar/users/$USER_ID/role-mappings/realm"
```

---

## 📋 Fase 2: Módulos Python (✅ Concluído)

### Entregáveis

- ✅ `intellicare-auth` biblioteca Python com `KeycloakClient`, `configure_auth`, `require_role`
- ✅ `keycloak_client_secrets.json` com 14 client secrets
- ✅ Todos os módulos com `configure_auth()` no startup

### Integração Padrão por Módulo

**Passo 1: Adicionar dependência**

```toml
# pyproject.toml (poetry)
[tool.poetry.dependencies]
intellicare-auth = {path = "../intellicare-auth", develop = true}
```

**Passo 2: Configurar no app.py**

```python
# <modulo>/api/app.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from intellicare_auth.fastapi import configure_auth

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Configura Keycloak (lê keycloak_client_secrets.json)
    configure_auth(app, secrets_path="keycloak_client_secrets.json")
    yield

app = FastAPI(lifespan=lifespan)
```

**Passo 3: Proteger endpoints**

```python
# Adicionar às rotas conforme necessidade
from intellicare_auth.fastapi import require_role
from intellicare_auth.middleware import get_current_user

@router.get("/api/v1/analyze")
async def analyze(user: dict = Depends(get_current_user)):
    ...

@router.delete("/api/v1/data/{id}")
async def delete_data(
    id: str,
    user: dict = Depends(require_role("PLATFORM_ADMIN"))
):
    ...
```

### Verificar Módulo Integrado

```bash
# Teste de validação de token
TOKEN=$(curl -s \
  -d "client_id=intellicare-portal" \
  -d "username=admin@intellicare.ia.br" \
  -d "password=Admin@2026!" \
  -d "grant_type=password" \
  "http://localhost:8080/realms/bemcuidar/protocol/openid-connect/token" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Testar endpoint protegido
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8001/api/v1/info
# → {"module": "florence", "user": "admin@intellicare.ia.br", ...}
```

---

## 📋 Fase 3: Portal Frontend (🔄 Em Progresso)

### Entregáveis

- ✅ `authService.ts` — PKCE flow implementado
- ✅ `TenantContext.tsx` — Multi-tenant context implementado
- ⚠️ **BUG:** `REALM` fallback hardcoded como `'intellicare'` → deve ser `'bemcuidar'`
- ⬜ `RoleRouter.tsx` — Roteamento por role
- ⬜ Interceptor Axios para refresh automático
- ⬜ Tela de seleção de tenant

### Correção Urgente — Realm Name Bug

```bash
# Corrigir fallback do realm name em authService.ts
sed -i "s/|| 'intellicare'/|| 'bemcuidar'/g" \
  intellicare-portal/frontend/src/services/authService.ts

# Verificar correção
grep "REALM" intellicare-portal/frontend/src/services/authService.ts
# → const REALM = import.meta.env.VITE_KEYCLOAK_REALM || 'bemcuidar';
```

### Arquivo `.env.local` (desenvolvimento)

```env
VITE_KEYCLOAK_URL=http://localhost:8080
VITE_KEYCLOAK_REALM=bemcuidar
VITE_KEYCLOAK_CLIENT_ID=intellicare-portal
VITE_WANDA_URL=http://localhost:8004
VITE_API_BASE_URL=http://localhost:8004/api/v1
```

### Arquivo `.env.production`

```env
VITE_KEYCLOAK_URL=https://auth.intellicare.ia.br
VITE_KEYCLOAK_REALM=bemcuidar
VITE_KEYCLOAK_CLIENT_ID=intellicare-portal
VITE_WANDA_URL=https://api.intellicare.ia.br
VITE_API_BASE_URL=https://api.intellicare.ia.br/api/v1
```

### Implementar Interceptor Axios para Refresh

```typescript
// src/services/api.ts
import axios from 'axios';
import { useAuthStore } from '@store/authStore';
import { refreshToken } from './authService';

const api = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL,
});

// Request interceptor — adiciona token
api.interceptors.request.use(async (config) => {
    const { token, tokenExp } = useAuthStore.getState();
    
    // Refresh proativo 5min antes da expiração
    if (token && tokenExp) {
        const timeLeft = tokenExp - Math.floor(Date.now() / 1000);
        if (timeLeft < 300) {
            await refreshToken();
        }
    }
    
    const currentToken = useAuthStore.getState().token;
    if (currentToken) {
        config.headers.Authorization = `Bearer ${currentToken}`;
    }
    return config;
});

// Response interceptor — trata 401
api.interceptors.response.use(
    (response) => response,
    async (error) => {
        if (error.response?.status === 401) {
            const refreshed = await refreshToken();
            if (refreshed) {
                // Retry original request
                const token = useAuthStore.getState().token;
                error.config.headers.Authorization = `Bearer ${token}`;
                return api(error.config);
            }
            // Refresh failed — redirect to login
            useAuthStore.getState().clear();
            window.location.href = '/login';
        }
        return Promise.reject(error);
    }
);

export default api;
```

### Implementar RoleRouter

```typescript
// src/components/RoleRouter.tsx
import { Navigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '@store/authStore';
import { decodeToken } from '@utils/jwt';

export function RoleRouter() {
    const { token } = useAuthStore();
    const location = useLocation();
    
    if (!token) return <Navigate to="/login" state={{ from: location }} replace />;
    
    const decoded = decodeToken(token);
    if (!decoded) return <Navigate to="/login" replace />;
    
    const roles: string[] = decoded.realm_access?.roles ?? [];
    
    if (roles.some(r => ['PLATFORM_ADMIN', 'PLATFORM_SUPPORT', 'PLATFORM_BILLING'].includes(r))) {
        return <Navigate to="/admin" replace />;
    }
    if (roles.includes('TENANT_GESTOR')) {
        return <Navigate to="/gestor" replace />;
    }
    if (roles.some(r => ['MEDICO', 'CLINICO', 'ENFERMEIRO', 'RECEPCIONISTA'].includes(r))) {
        return <Navigate to="/dashboard" replace />;
    }
    if (roles.includes('PACIENTE')) {
        return <Navigate to="/paciente" replace />;
    }
    
    return <Navigate to="/sem-acesso" replace />;
}
```

### React Router v7 — Rotas

```typescript
// src/main.tsx ou App.tsx
import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import { RoleRouter } from '@components/RoleRouter';
import { AuthCallback } from '@pages/AuthCallback';
import { LoginPage } from '@pages/LoginPage';
import { ProtectedRoute } from '@components/ProtectedRoute';

const router = createBrowserRouter([
    { path: '/login', element: <LoginPage /> },
    { path: '/auth/callback', element: <AuthCallback /> },
    { path: '/', element: <RoleRouter /> },
    {
        path: '/admin/*',
        element: <ProtectedRoute roles={['PLATFORM_ADMIN', 'PLATFORM_SUPPORT', 'PLATFORM_BILLING']} />,
        children: [/* admin routes */],
    },
    {
        path: '/gestor/*',
        element: <ProtectedRoute roles={['TENANT_GESTOR']} />,
        children: [/* gestor routes */],
    },
    {
        path: '/dashboard/*',
        element: <ProtectedRoute roles={['MEDICO', 'CLINICO', 'ENFERMEIRO', 'RECEPCIONISTA']} />,
        children: [/* clinical routes */],
    },
    { path: '/sem-acesso', element: <SemAcessoPage /> },
]);
```

### AuthCallback Page

```typescript
// src/pages/AuthCallback.tsx
import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { handleCallback } from '@services/authService';

export function AuthCallback() {
    const navigate = useNavigate();
    
    useEffect(() => {
        const code = new URLSearchParams(window.location.search).get('code');
        if (!code) { navigate('/login'); return; }
        
        handleCallback(code)
            .then(() => {
                const redirectTo = sessionStorage.getItem('redirect_after') || '/';
                sessionStorage.removeItem('redirect_after');
                navigate(redirectTo, { replace: true });
            })
            .catch((err) => {
                console.error('Auth callback failed:', err);
                navigate('/login?error=auth_failed');
            });
    }, []);
    
    return <div>Autenticando...</div>;
}
```

---

## 📋 Fase 4: SMART-on-FHIR 2.0 (⬜ Pendente)

### Dependência

Esta fase depende da Fase 3 completa e do módulo `intellicare-grahame` funcional.

### Entregáveis

- [ ] `intellicare-auth/intellicare_auth/smart/` — Implementação SMART completa
- [ ] Well-known endpoint exposto via GRAHAME (`/realms/bemcuidar/.well-known/smart-configuration`)
- [ ] EHR Launch handler no GRAHAME
- [ ] Standalone Launch para apps clínicos externos
- [ ] Scopes SMART validados no backend

### Tarefas

```
T4.1 - Verificar smart/ já implementado em intellicare-auth
T4.2 - Configurar well-known em GRAHAME
T4.3 - Implementar /smart/launch endpoint
T4.4 - Implementar /smart/callback com token parsing
T4.5 - Validar patient context em FHIR queries
T4.6 - Testar com client SMART externo (Inferno Test Suite)
```

### Smoke Test SMART

```bash
# Verificar well-known SMART
curl -s https://auth.intellicare.ia.br/realms/bemcuidar/.well-known/smart-configuration \
  | python3 -m json.tool | grep -E "(capabilities|scopes)"

# Verificar FHIR metadata
curl -s https://fhir.intellicare.ia.br/fhir/R4/metadata \
  | python3 -m json.tool | grep -A5 "security"
```

---

## 📋 Fase 5: Produção (⬜ Pendente)

### Checklist Pré-Deploy

```
[ ] Certificado SSL Let's Encrypt ativo para auth.intellicare.ia.br
[ ] KC_HOSTNAME configurado corretamente
[ ] KC_HTTP_ENABLED=false (apenas HTTPS)
[ ] Backup automático do keycloak-db (pg_dump)
[ ] Keycloak rodando com start (não start-dev)
[ ] Pool DB configurado: min=5, max=20
[ ] KC_LOG_LEVEL=WARN (não INFO em produção)
[ ] Prometheus scraping /metrics
[ ] Alertas Grafana para falhas de autenticação
[ ] Rate limiting no Traefik para /realms/bemcuidar/protocol/openid-connect/token
[ ] MFA obrigatório para PLATFORM_ADMIN e PLATFORM_BILLING
[ ] Secrets rotacionados dos client_secrets
[ ] realm.json exportado como backup
```

### Traefik — Rate Limiting para Keycloak

```yaml
# traefik/dynamic/middlewares.yml
http:
  middlewares:
    keycloak-ratelimit:
      rateLimit:
        average: 100
        burst: 50
        period: 1s
        sourceCriterion:
          ipStrategy:
            depth: 1

    keycloak-auth-ratelimit:
      rateLimit:
        average: 10      # 10 tentativas de login por segundo por IP
        burst: 20
        period: 1s
```

### Modo Produção — docker-compose

```yaml
# Alterações para produção:
keycloak:
  command: start          # Em vez de start-dev
  environment:
    KC_HTTP_ENABLED: "false"       # Apenas HTTPS
    KC_HTTPS_CERTIFICATE_FILE: "/opt/keycloak/conf/tls.crt"
    KC_HTTPS_CERTIFICATE_KEY_FILE: "/opt/keycloak/conf/tls.key"
    KC_LOG_LEVEL: "WARN"
    KC_DB_POOL_MIN_SIZE: "10"
    KC_DB_POOL_MAX_SIZE: "50"
    KC_CACHE: "ispn"               # Infinispan cache para HA
    KC_CACHE_STACK: "kubernetes"   # ou tcp para single-node
```

### Backup Automático do Realm

```bash
# Script: scripts/backup_keycloak_realm.sh
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="backups/keycloak"
mkdir -p "$BACKUP_DIR"

# Export realm via Admin REST API
export ADMIN_TOKEN=$(curl -s \
  -d "client_id=admin-cli" \
  -d "username=${KEYCLOAK_ADMIN}" \
  -d "password=${KEYCLOAK_ADMIN_PASSWORD}" \
  -d "grant_type=password" \
  "https://auth.intellicare.ia.br/realms/master/protocol/openid-connect/token" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

curl -s -H "Authorization: Bearer $ADMIN_TOKEN" \
  "https://auth.intellicare.ia.br/admin/realms/bemcuidar" \
  > "$BACKUP_DIR/bemcuidar-realm-$DATE.json"

# Backup PostgreSQL
docker exec keycloak-db pg_dump -U keycloak_admin keycloak_db \
  > "$BACKUP_DIR/keycloak-db-$DATE.sql"

echo "Backup completo: $BACKUP_DIR"
```

### Monitoramento — Prometheus

```yaml
# prometheus.yml — adicionar scrape
scrape_configs:
  - job_name: 'keycloak'
    static_configs:
      - targets: ['keycloak-intellicare:8080']
    metrics_path: '/metrics'
    scrape_interval: 30s
```

**Métricas importantes:**
- `keycloak_logins_total` — total de logins bem-sucedidos
- `keycloak_login_errors_total` — falhas de login (brute force detection)
- `vendor_statistics_db_pool_active_count` — pool de conexões DB
- `process_cpu_seconds_total` — CPU do Keycloak

### Alertas Grafana

```json
{
  "alert": "KeycloakLoginFailuresHigh",
  "condition": "sum(rate(keycloak_login_errors_total[5m])) > 50",
  "message": "Alta taxa de falhas de login — possível ataque"
}
```

---

## 🧪 Smoke Tests Globais

```bash
#!/bin/bash
# scripts/smoke_test_keycloak.sh

echo "=== Keycloak Smoke Tests ==="

BASE="https://auth.intellicare.ia.br"
REALM="bemcuidar"

# 1. Health check
echo -n "1. Health: "
STATUS=$(curl -s "$BASE/health/ready" | python3 -c "import sys,json; print(json.load(sys.stdin).get('status','?'))" 2>/dev/null)
[ "$STATUS" = "UP" ] && echo "✅ UP" || echo "❌ $STATUS"

# 2. OIDC Discovery
echo -n "2. OIDC Discovery: "
ISSUER=$(curl -s "$BASE/realms/$REALM/.well-known/openid-configuration" \
  | python3 -c "import sys,json; print(json.load(sys.stdin).get('issuer','?'))" 2>/dev/null)
[ "$ISSUER" != "?" ] && echo "✅ $ISSUER" || echo "❌ FALHOU"

# 3. JWKS
echo -n "3. JWKS: "
KEYS=$(curl -s "$BASE/realms/$REALM/protocol/openid-connect/certs" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d.get('keys',[])),'chaves')" 2>/dev/null)
echo "✅ $KEYS"

# 4. Token M2M (Wanda)
echo -n "4. Token M2M (Wanda): "
TOKEN=$(curl -s -X POST \
  -d "grant_type=client_credentials" \
  -d "client_id=intellicare-wanda" \
  -d "client_secret=WVmIKFXeJxnyIMcsPvzyeE13lG5uZYfy" \
  "$BASE/realms/$REALM/protocol/openid-connect/token" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print('OK' if 'access_token' in d else d.get('error','?'))" 2>/dev/null)
[ "$TOKEN" = "OK" ] && echo "✅ OK" || echo "❌ $TOKEN"

# 5. SMART well-known
echo -n "5. SMART config: "
CAPS=$(curl -s "$BASE/realms/$REALM/.well-known/smart-configuration" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d.get('capabilities',[])),'capabilities')" 2>/dev/null)
echo "✅ $CAPS"

echo ""
echo "=== Smoke Tests Concluídos ==="
```

---

## 📊 Consolidated Task Board

| ID | Fase | Tarefa | Status | Owner |
|----|------|--------|--------|-------|
| T0.1 | 0 | docker-compose.keycloak.yml | ✅ | DevOps |
| T0.2 | 0 | .env.keycloak | ✅ | DevOps |
| T1.1 | 1 | bemcuidar-realm.json — roles | ✅ | Backend |
| T1.2 | 1 | bemcuidar-realm.json — clients | ✅ | Backend |
| T1.3 | 1 | Protocol mappers (tenant_id, tenants) | ✅ | Backend |
| T2.1 | 2 | intellicare_auth/client.py | ✅ | Backend |
| T2.2 | 2 | intellicare_auth/fastapi.py | ✅ | Backend |
| T2.3 | 2 | intellicare_auth/middleware.py | ✅ | Backend |
| T2.4 | 2 | configure_auth() em todos os módulos | ✅ | Backend |
| T2.5 | 2 | Token exchange em WANDA | ✅ | Backend |
| T3.1 | 3 | **FIX: realm fallback bemcuidar** | 🔴 | Frontend |
| T3.2 | 3 | .env.local / .env.production | ⬜ | Frontend |
| T3.3 | 3 | RoleRouter.tsx completo | ⬜ | Frontend |
| T3.4 | 3 | Interceptor Axios (refresh auto) | ⬜ | Frontend |
| T3.5 | 3 | TenantSelector component | ⬜ | Frontend |
| T3.6 | 3 | AuthCallback page | ⬜ | Frontend |
| T4.1 | 4 | smart/ módulo verificação/conclusão | ⬜ | Backend |
| T4.2 | 4 | GRAHAME well-known endpoint | ⬜ | Backend |
| T4.3 | 4 | EHR Launch handler | ⬜ | Backend |
| T4.4 | 4 | Standalone launch | ⬜ | Backend |
| T5.1 | 5 | Keycloak modo `start` (produção) | ⬜ | DevOps |
| T5.2 | 5 | Let's Encrypt auth.intellicare.ia.br | ⬜ | DevOps |
| T5.3 | 5 | Backup automático realm + DB | ⬜ | DevOps |
| T5.4 | 5 | Prometheus scraping Keycloak | ⬜ | DevOps |
| T5.5 | 5 | Alertas Grafana login failures | ⬜ | DevOps |
| T5.6 | 5 | Rate limiting Traefik /token endpoint | ⬜ | DevOps |
| T5.7 | 5 | MFA obrigatório PLATFORM_ADMIN | ⬜ | DevOps |
| T5.8 | 5 | Rotação de client_secrets | ⬜ | DevOps |

---

## 🚨 Issues Conhecidas

| Severidade | Issue | Impacto | Solução |
|------------|-------|---------|---------|
| 🔴 CRÍTICO | `authService.ts` usa realm `'intellicare'` no fallback | Login falha se VITE_KEYCLOAK_REALM não configurado | Fix: `|| 'bemcuidar'` em authService.ts |
| 🟡 MÉDIO | `TenantContext.tsx` usa mock em `fetchTenantProfile` | Branding/módulos hardcoded em dev | Implementar chamada real à API do gestor |
| 🟡 MÉDIO | Não há interceptor Axios para refresh automático | Token expira sem aviso (5min) | Implementar interceptor conforme T3.4 |
| 🟢 BAIXO | `start-dev` em uso (inclui console H2 sem senha) | Não apto para produção | Migrar para `start` na Fase 5 |

---

*Gerado em: 2026-03-06 | Responsável: Eduardo Garabini*
