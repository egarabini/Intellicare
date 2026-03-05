# PLANO DE IMPLEMENTAÇÃO — Admin + Gestor + Portal Auth

**Data**: 2026-03-05
**Status**: 🟡 Em Planejamento
**Prioridade**: 🚀 P0 — Crítica
**Versão**: 2.0.2
**Estimativa**: ~15 dias-dev (ou ~11 dias com 2 devs em paralelo)
**Rastreabilidade**: 02_ESPECIFICACAO_TECNICA.md

---

## 📋 Índice

1. [Visão Geral do Plano](#1-visão-geral-do-plano)
2. [Sprint 1 — Keycloak](#2-sprint-1--keycloak-1-dia)
3. [Sprint 2 — Portal: Login e Auth](#3-sprint-2--portal-login-e-auth-2-dias)
4. [Sprint 3 — Admin Backend](#4-sprint-3--admin-backend-2-dias)
5. [Sprint 4 — Admin Frontend](#5-sprint-4--admin-frontend-4-dias)
6. [Sprint 5 — Gestor Backend](#6-sprint-5--gestor-backend-15-dias)
7. [Sprint 6 — Gestor Frontend](#7-sprint-6--gestor-frontend-35-dias)
8. [Sprint 7 — QA e Deploy](#8-sprint-7--qa-e-deploy-1-dia)
9. [Configuração de Deploy](#9-configuração-de-deploy)
10. [Variáveis de Ambiente](#10-variáveis-de-ambiente)
11. [Migrações Alembic](#11-migrações-alembic)
12. [Build e Deploy do Portal](#12-build-e-deploy-do-portal)
13. [Smoke Tests pós-Deploy](#13-smoke-tests-pós-deploy)
14. [Critérios de Aceite Consolidados](#14-critérios-de-aceite-consolidados)

---

## 📊 1. Visão Geral do Plano

```
SEMANA 1                          SEMANA 2                      SEMANA 3
│                                 │                             │
├─ Sprint 1: Keycloak (1d)        │                             │
├─ Sprint 2: Portal Auth (2d)     │                             │
├─ Sprint 3: Admin Backend (2d)   │                             │
│                                 ├─ Sprint 4: Admin FE (4d)   │
│                                 ├─ Sprint 5: Gestor BE (1.5d) │
│                                 │                             ├─ Sprint 6: Gestor FE (3.5d)
│                                 │                             ├─ Sprint 7: QA+Deploy (1d)
```

> **Paralelização possível**: Sprint 4 (Admin FE) e Sprint 5 (Gestor BE) podem rodar em paralelo com 2 devs.

| Sprint | Entregável | Duração | Pré-requisito |
|--------|------------|---------|---------------|
| 1 | Keycloak configurado | 1 dia | — |
| 2 | Portal: Login + auth flow | 2 dias | Sprint 1 |
| 3 | Admin Backend (gaps preenchidos) | 2 dias | Sprint 1 |
| 4 | Admin Frontend (5 abas) | 4 dias | Sprint 2 + 3 |
| 5 | Gestor Backend (auth + módulos) | 1,5 dias | Sprint 1 + 3 |
| 6 | Gestor Frontend | 3,5 dias | Sprint 2 + 5 |
| 7 | QA + Deploy | 1 dia | Sprint 4 + 6 |
| **Total** | | **~15 dias** | |

---

## 🔑 2. Sprint 1 — Keycloak (1 dia)

> **Objetivo**: Configurar autenticação antes de qualquer código de produto.

### Checklist

```
□ Keycloak rodando: docker compose up -d keycloak
□ Criar realm: intellicare
□ Criar client: intellicare-portal
   □ Access Type: public
   □ Standard Flow: ON
   □ Implicit Flow: OFF
   □ Valid Redirect URIs: http://localhost:3001/* | https://portal.intellicare.ia.br/*
   □ Web Origins: http://localhost:3001 | https://portal.intellicare.ia.br
□ Criar roles realm: PLATFORM_ADMIN, TENANT_GESTOR, CLINICO, MEDICO, ENFERMEIRO, PACIENTE
□ Adicionar mapper realm_roles → Token Claim Name: realm_roles → add to access token: ON
□ Adicionar mapper tenant_id → User Attribute → Token Claim Name: tenant_id → ON
□ Criar usuário: admin@intellicare.ia.br → role: PLATFORM_ADMIN
□ Criar usuário: gestor@hsaolucas.com.br → role: TENANT_GESTOR, attr: tenant_id=hospital_sao_lucas
□ Testar geração de token via Postman
□ Validar claims em jwt.io: realm_roles e tenant_id presentes
```

---

## 🌐 3. Sprint 2 — Portal: Login e Auth (2 dias)

### Dia 1

| Arquivo | Tarefa |
|---------|--------|
| `store/authStore.ts` | Zustand: accessToken, user, roles, tenantId, expiry, `setTokens()`, `clear()` |
| `services/authService.ts` | `iniciarLogin()` + `handleCallback()` + `refreshToken()` + `logout()` |
| `hooks/useAuth.ts` | Hook que expõe dados do authStore + helper `isRole()` |

### Dia 2

| Arquivo | Tarefa |
|---------|--------|
| `pages/Login/index.tsx` | Tela visual: logo + botão "Entrar" + tratamento de erro |
| `pages/Login/AuthCallback.tsx` | Extrai `?code=` da URL → `handleCallback()` → navega para `RoleRouter` |
| `components/auth/RoleRouter.tsx` | Redireciona por role (prioridade: PLATFORM_ADMIN > TENANT_GESTOR > CLINICO) |
| `components/auth/ProtectedRoute.tsx` | HOC: verifica auth + role; redirect para `/login` se não autorizado |
| `routes.tsx` | Estrutura de rotas com ProtectedRoute por área |

**Teste de aceite do sprint:**
- ✅ Login com PLATFORM_ADMIN → `/admin` (apenas layout placeholder)
- ✅ Login com TENANT_GESTOR → `/gestor` (apenas layout placeholder)
- ✅ Acesso direto a `/admin` sem token → redirect `/login`

---

## ⚙️ 4. Sprint 3 — Admin Backend (2 dias)

### Dia 1

| Arquivo | Tarefa |
|---------|--------|
| `admin/api/deps.py` | Implementar `require_platform_admin` com `verify_jwt` real (remover fallback) |
| `admin/models/tenant_gestor.py` | Modelo ORM `TenantGestor` |
| `admin/models/tenant_contrato.py` | Modelo ORM `TenantContrato` |
| `migrations/` | `alembic revision --autogenerate -m "add_tenant_gestores_and_contratos"` |
| `migrations/` | `alembic upgrade head` |

### Dia 2

| Arquivo | Tarefa |
|---------|--------|
| `admin/api/gestor_routes.py` | `GET` + `POST /admin/tenants/{id}/gestores` + `DELETE /{uid}` |
| `admin/api/contrato_routes.py` | `GET` + `POST` + `PATCH /admin/tenants/{id}/contrato` |
| `admin/api/plan_routes.py` | Expandir `GET /admin/dashboard` (módulos populares + últimas atividades) |
| `tests/test_admin_auth.py` | 401 sem token, 403 sem role, 200 com PLATFORM_ADMIN |

**Teste de aceite do sprint:**
- ✅ `GET /admin/dashboard` com token PLATFORM_ADMIN → 200
- ✅ `GET /admin/dashboard` sem token → 401
- ✅ `GET /admin/dashboard` com token TENANT_GESTOR → 403
- ✅ `alembic upgrade head` sem erros; tabelas `tenant_gestores` e `tenant_contratos` existem

---

## 🖥️ 5. Sprint 4 — Admin Frontend (4 dias)

### Dia 1

| Arquivo | Tarefa |
|---------|--------|
| `pages/Admin/layout/AdminLayout.tsx` | Sidebar + header + Outlet |
| `pages/Admin/layout/AdminSidebar.tsx` | Menu: Dashboard, Tenants, Planos, Auditoria, Config |
| `pages/Admin/layout/AdminHeader.tsx` | Nome admin + avatar + botão Sair |
| `services/adminApi.ts` | Cliente HTTP `/admin/*` com interceptor de token + retry no 401 |

### Dia 2

| Arquivo | Tarefa |
|---------|--------|
| `pages/Admin/Dashboard.tsx` | 4 KPI cards + gráfico barras (top 5 módulos) + tabela atividades |
| `pages/Admin/Tenants/List.tsx` | Tabela paginada + filtros status/busca + modal criação |

### Dia 3

| Arquivo | Tarefa |
|---------|--------|
| `pages/Admin/Tenants/Detail.tsx` | Estrutura de 5 abas + header com status + ações Suspender/Reativar |
| `pages/Admin/Tenants/tabs/DadosTab.tsx` | Form editável: nome, e-mail, telefone, branding |
| `pages/Admin/Tenants/tabs/ModulosTab.tsx` | Grid de cards com toggle ON/OFF por módulo |

### Dia 4

| Arquivo | Tarefa |
|---------|--------|
| `pages/Admin/Tenants/tabs/GestoresTab.tsx` | Lista gestores + modal adicionar + ação remover |
| `pages/Admin/Tenants/tabs/ContratoTab.tsx` | Contrato vigente + histórico + modal alterar plano |
| `pages/Admin/Tenants/tabs/AuditoriaTab.tsx` | Log paginado + filtro período + tipo de ação |

**Teste de aceite do sprint:**
- ✅ Dashboard carrega em < 2s com dados reais
- ✅ Toggle de módulo: toast "Módulo habilitado" + estado atualizado sem reload
- ✅ Modal criação tenant: CNPJ inválido exibe erro inline sem submeter

---

## ⚙️ 6. Sprint 5 — Gestor Backend (1,5 dias)

### Dia 1

| Arquivo | Tarefa |
|---------|--------|
| `gestor/api/deps.py` | Implementar `require_tenant_gestor` com validação de `tenant_id` |
| `gestor/api/user_routes.py` | Aplicar `require_tenant_gestor` em todos os endpoints existentes |
| `gestor/api/sector_routes.py` | Aplicar auth + adicionar `POST /sectors/{id}/users` |
| `gestor/api/modulos_routes.py` | `GET /gestor/modulos-habilitados` com cache Redis 5min |

### Dia 2 (manhã)

| Arquivo | Tarefa |
|---------|--------|
| `gestor/api/dashboard_routes.py` | Expandir: `por_unidade` + `usuarios_sem_unidade` + alertas |
| `tests/test_gestor_isolation.py` | Token tenant_A NÃO acessa dados tenant_B → HTTP 403 |

**Teste de aceite do sprint:**
- ✅ `GET /gestor/users` com token tenant_A → apenas usuários do tenant A
- ✅ Segunda chamada a `/gestor/modulos-habilitados` (< 100ms) = cache hit
- ✅ Token de outro tenant → HTTP 403

---

## 🖥️ 7. Sprint 6 — Gestor Frontend (3,5 dias)

### Dia 1

| Arquivo | Tarefa |
|---------|--------|
| `pages/Gestor/layout/GestorLayout.tsx` | Layout com white-label (logo via `GET /gestor/settings`) |
| `pages/Gestor/layout/GestorSidebar.tsx` | Menu: Dashboard, Unidades, Usuários, Config |
| `pages/Gestor/layout/GestorHeader.tsx` | Logo tenant + nome gestor + botão Sair |
| `services/gestorApi.ts` | Cliente HTTP `/gestor/*` com token |

### Dia 2

| Arquivo | Tarefa |
|---------|--------|
| `pages/Gestor/Dashboard.tsx` | KPIs + badge vermelho sem-unidade + mini-tabela + atividades |
| `pages/Gestor/Unidades.tsx` | Árvore hierárquica com expand/collapse + modais CRUD |
| `components/UnidadeTree.tsx` | Componente reutilizável de árvore (recursivo) |

### Dia 3

| Arquivo | Tarefa |
|---------|--------|
| `pages/Gestor/Usuarios.tsx` | Filtros + tabela com linha amarela (sem unidade) + modal CRUD |

### Dia 4 (manhã)

| Arquivo | Tarefa |
|---------|--------|
| `pages/Gestor/Configuracoes.tsx` | Fuso + e-mails alerta + contrato read-only |

**Teste de aceite do sprint:**
- ✅ Dashboard: badge vermelho visível quando há usuários sem unidade
- ✅ Árvore de unidades: expand/collapse + subunidades indentadas
- ✅ Lista usuários: linha amarela para sem-unidade
- ✅ Configurações: salvar fuso → recarregar → fuso mantido

---

## 🧪 8. Sprint 7 — QA e Deploy (1 dia)

### Checklist

```
□ Atualizar 01-backend-health.spec.js: adicionar admin (8010) e gestor (8011)
□ Criar 03-admin-gestor.spec.js: testes E2E de auth flow
□ Testar isolamento multi-tenant
□ Validar todos os critérios de aceite (seção 14)
□ Fix GRAHAME migration: cd intellicare-grahame && alembic upgrade head
□ Executar run-smoke.bat → 53+ testes passando
□ Tag de release: git tag v2.0.2
```

---

## 🐳 9. Configuração de Deploy

### 9.1 Docker Compose — intellicare-admin

Adicionar ao `docker-compose.full.yml`:

```yaml
  intellicare-admin:
    build:
      context: ./intellicare-admin
      dockerfile: Dockerfile
    container_name: intellicare-admin
    restart: unless-stopped
    ports:
      - "8010:8010"
    environment:
      - APP_ENV=${APP_ENV:-development}
      - DATABASE_URL=postgresql+asyncpg://${DB_USER}:${DB_PASS}@postgres:5432/${DB_NAME}
      - REDIS_URL=redis://redis:6379/3
      - KEYCLOAK_URL=${KEYCLOAK_URL}
      - KEYCLOAK_REALM=${KEYCLOAK_REALM:-intellicare}
      - KEYCLOAK_CLIENT_ID=intellicare-admin-backend
      - INTERNAL_AUTH_TOKEN=${INTERNAL_AUTH_TOKEN}
    depends_on:
      - postgres
      - redis
      - keycloak
    networks:
      - intellicare-net
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8010/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

---

### 9.2 Docker Compose — intellicare-gestor

```yaml
  intellicare-gestor:
    build:
      context: ./intellicare-gestor
      dockerfile: Dockerfile
    container_name: intellicare-gestor
    restart: unless-stopped
    ports:
      - "8011:8011"
    environment:
      - APP_ENV=${APP_ENV:-development}
      - DATABASE_URL=postgresql+asyncpg://${DB_USER}:${DB_PASS}@postgres:5432/${DB_NAME}
      - REDIS_URL=redis://redis:6379/4
      - KEYCLOAK_URL=${KEYCLOAK_URL}
      - KEYCLOAK_REALM=${KEYCLOAK_REALM:-intellicare}
      - ADMIN_INTERNAL_URL=http://intellicare-admin:8010
      - INTERNAL_AUTH_TOKEN=${INTERNAL_AUTH_TOKEN}
    depends_on:
      - postgres
      - redis
      - intellicare-admin
    networks:
      - intellicare-net
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8011/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

---

### 9.3 Docker Compose — Keycloak

```yaml
  keycloak:
    image: quay.io/keycloak/keycloak:24.0
    container_name: keycloak
    command: start-dev
    restart: unless-stopped
    ports:
      - "8080:8080"
    environment:
      - KEYCLOAK_ADMIN=${KEYCLOAK_ADMIN_USER:-admin}
      - KEYCLOAK_ADMIN_PASSWORD=${KEYCLOAK_ADMIN_PASS}
      - KC_DB=postgres
      - KC_DB_URL=jdbc:postgresql://postgres:5432/${DB_NAME}
      - KC_DB_USERNAME=${DB_USER}
      - KC_DB_PASSWORD=${DB_PASS}
      - KC_HOSTNAME=${KEYCLOAK_HOSTNAME:-localhost}
    depends_on:
      - postgres
    networks:
      - intellicare-net
```

---

### 9.4 Traefik — Roteamento por subdomínio (produção)

Adicionar labels em `docker-compose.traefik.yml`:

```yaml
  intellicare-admin:
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.admin-api.rule=Host(`admin-api.intellicare.ia.br`)"
      - "traefik.http.routers.admin-api.tls.certresolver=letsencrypt"
      - "traefik.http.routers.admin-api.entrypoints=websecure"
      - "traefik.http.services.admin-api.loadbalancer.server.port=8010"

  intellicare-gestor:
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.gestor-api.rule=Host(`gestor-api.intellicare.ia.br`)"
      - "traefik.http.routers.gestor-api.tls.certresolver=letsencrypt"
      - "traefik.http.routers.gestor-api.entrypoints=websecure"
      - "traefik.http.services.gestor-api.loadbalancer.server.port=8011"

  intellicare-portal:
    labels:
      - "traefik.enable=true"
      # Portal principal
      - "traefik.http.routers.portal.rule=Host(`portal.intellicare.ia.br`)"
      # White-label: qualquer subdomínio *.intellicare.ia.br
      - "traefik.http.routers.portal-wl.rule=HostRegexp(`{tenant:[a-z0-9-]+}.intellicare.ia.br`)"
      - "traefik.http.routers.portal-wl.tls.certresolver=letsencrypt"
      - "traefik.http.routers.portal-wl.entrypoints=websecure"
```

---

## 🔒 10. Variáveis de Ambiente

### `.env` (raiz do projeto)

```bash
# ── Banco de Dados ─────────────────────────────────────────────
DB_USER=intellicare
DB_PASS=SUBSTITUA_POR_SENHA_FORTE
DB_NAME=intellicare

# ── Keycloak ───────────────────────────────────────────────────
KEYCLOAK_URL=https://auth.intellicare.ia.br
KEYCLOAK_REALM=intellicare
KEYCLOAK_HOSTNAME=auth.intellicare.ia.br
KEYCLOAK_ADMIN_USER=admin
KEYCLOAK_ADMIN_PASS=SUBSTITUA_POR_SENHA_FORTE

# ── Segurança interna (comunicação inter-serviço) ──────────────
# Gerar com: python -c "import secrets; print(secrets.token_hex(32))"
INTERNAL_AUTH_TOKEN=SUBSTITUA_POR_TOKEN_64_CHARS

# ── Serviços ───────────────────────────────────────────────────
REDIS_URL=redis://redis:6379
APP_ENV=production

# ── E-mail (notificações e convites) ──────────────────────────
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASS=SUA_API_KEY_SENDGRID
EMAIL_FROM=noreply@intellicare.ia.br
```

### `.env.production` (Vite build do portal)

```bash
VITE_KEYCLOAK_URL=https://auth.intellicare.ia.br
VITE_KEYCLOAK_REALM=intellicare
VITE_KEYCLOAK_CLIENT_ID=intellicare-portal
VITE_ADMIN_API_URL=https://admin-api.intellicare.ia.br
VITE_GESTOR_API_URL=https://gestor-api.intellicare.ia.br
VITE_PORTAL_VERSION=2.0.2
```

---

## 🗄️ 11. Migrações Alembic

> ⚠️ **Atenção**: executar nesta ordem. O schema `platform` deve existir antes das migrações de gestor.

### Passo 1 — intellicare-admin

```bash
cd intellicare-admin

# Aplicar migrações já existentes
alembic upgrade head

# Gerar nova migration (gestores + contratos)
alembic revision --autogenerate -m "add_tenant_gestores_and_contratos"

# Aplicar
alembic upgrade head

# Verificar tabelas
psql -U intellicare -c "\dt platform.*"
# Esperado: tenants, plans, billing_records, audit_logs,
#           tenant_modules, tenant_gestores, tenant_contratos
```

### Passo 2 — intellicare-gestor

```bash
cd intellicare-gestor
alembic upgrade head
# Schemas de tenant são criados dinamicamente pelo ProvisioningService
# ao chamar POST /admin/tenants
```

### Passo 3 — intellicare-grahame (pendência conhecida 🐛)

```bash
cd intellicare-grahame
alembic upgrade head
# Cria coluna fhir_resources.fhir_id ausente
# (causa HTTP 500 em TODOS os endpoints FHIR — prioridade alta)
```

### Verificação final

```bash
# Verificar status de todas as migrações
for module in intellicare-admin intellicare-gestor intellicare-grahame; do
  echo "=== $module ==="
  cd $module
  alembic current
  cd ..
done
```

---

## 🚀 12. Build e Deploy do Portal

### Build de produção

```bash
cd intellicare-portal/frontend

# Copiar e editar variáveis de produção
cp .env.example .env.production
# Editar: VITE_KEYCLOAK_URL, VITE_ADMIN_API_URL, VITE_GESTOR_API_URL

npm ci                  # Dependências (CI-safe, sem atualizar lock)
npm run lint            # Verificar erros ESLint
npm run test            # Vitest — todos os testes devem passar
npm run build           # Gera dist/ (TypeScript + Vite)
```

### Dockerfile do portal

```dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
ARG VITE_KEYCLOAK_URL VITE_KEYCLOAK_REALM VITE_KEYCLOAK_CLIENT_ID
ARG VITE_ADMIN_API_URL VITE_GESTOR_API_URL
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### nginx.conf (SPA — client-side routing)

```nginx
server {
    listen 80;
    root /usr/share/nginx/html;
    index index.html;

    # Redireciona todas as rotas para index.html (React Router)
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Cache de assets estáticos (Vite gera hashes únicos)
    location ~* \.(js|css|png|jpg|svg|ico|woff2)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

---

## 🧪 13. Smoke Tests pós-Deploy

### Script de verificação rápida

```bash
#!/bin/bash
set -e

echo "=== Smoke Test V2.0.2 ==="

# 1. Health checks
curl -sf http://localhost:8010/api/v1/health && echo "✅ admin: OK" || echo "❌ admin: FAIL"
curl -sf http://localhost:8011/api/v1/health && echo "✅ gestor: OK" || echo "❌ gestor: FAIL"

# 2. Endpoints sem token devem retornar 401
STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8010/admin/dashboard)
[ "$STATUS" = "401" ] && echo "✅ admin sem auth: 401 OK" || echo "❌ admin sem auth: $STATUS"

# 3. Obter token PLATFORM_ADMIN (apenas para teste)
TOKEN=$(curl -s -X POST \
  http://localhost:8080/realms/intellicare/protocol/openid-connect/token \
  -d "client_id=intellicare-portal&grant_type=password" \
  -d "username=admin@intellicare.ia.br&password=SENHA_ADMIN" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# 4. Endpoint com token PLATFORM_ADMIN deve retornar 200
STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $TOKEN" \
  http://localhost:8010/admin/dashboard)
[ "$STATUS" = "200" ] && echo "✅ admin com auth: 200 OK" || echo "❌ admin com auth: $STATUS"

# 5. Smoke tests Playwright completos
echo "=== Playwright Smoke Tests ==="
cd scripts/smoke-playwright && run-smoke.bat
```

---

## ✅ 14. Critérios de Aceite Consolidados

### CA-01 — Autenticação

| Cenário | Resultado esperado |
|---------|--------------------|
| Login PLATFORM_ADMIN | `/admin/dashboard` em < 3s |
| Login TENANT_GESTOR | `/gestor/dashboard` em < 3s |
| Acesso `/admin` com TENANT_GESTOR | HTTP 403 + página "Sem Permissão" |
| Token expirado (1h) | Refresh automático; sem logout involuntário |
| Refresh expirado (8h) | Logout + redirect `/login` com "Sessão expirada" |
| Logout | Store limpo + redirect `/login` |

---

### CA-02 — intellicare-admin Backend

- ✅ `GET /admin/dashboard` retorna totais corretos de tenants por status
- ✅ `POST /admin/tenants` cria tenant + provisiona schema PostgreSQL + cria realm Keycloak
- ✅ `POST /admin/tenants` com CNPJ inválido → HTTP 422 com campo identificado
- ✅ `PATCH /admin/tenants/{id}/modules` salva e reflete em GET imediato (sem reload)
- ✅ `POST /admin/tenants/{id}/gestores` → usuário aparece no Keycloak com role `TENANT_GESTOR`
- ✅ Todos endpoints: 401 sem token, 403 com token sem `PLATFORM_ADMIN`
- ✅ `alembic upgrade head` sem erros; tabelas `tenant_gestores` e `tenant_contratos` criadas

---

### CA-03 — intellicare-admin Frontend

- ✅ Dashboard carrega em < 2s com dados reais
- ✅ Lista tenants pagina: page=2 mostra próximos 20 registros
- ✅ Filtro `status=Suspenso` mostra apenas tenants suspensos
- ✅ Modal criação: CNPJ inválido exibe erro inline, não submete
- ✅ Toggle de módulo: toast "Habilitado/Desabilitado" + estado atualizado visualmente
- ✅ Aba Gestores: gestor adicionado aparece na lista imediatamente após POST

---

### CA-04 — intellicare-gestor Backend (isolamento)

- ✅ `GET /gestor/users` com token tenant_A → APENAS usuários do tenant A
- ✅ `tenant_id` passado no header é ignorado; usa sempre o do JWT
- ✅ `GET /gestor/modulos-habilitados`: segunda chamada < 100ms (cache Redis)
- ✅ `POST /gestor/sectors/{id}/users` com `user_ids` de outro tenant → HTTP 404
- ✅ Token de tenant diferente tentando acessar → HTTP 403

---

### CA-05 — intellicare-gestor Frontend

- ✅ Dashboard: badge vermelho visível quando há usuários sem unidade
- ✅ Árvore de unidades: expand/collapse funcional; subunidades indentadas
- ✅ Lista usuários: linha com fundo amarelo para usuários sem unidade
- ✅ Modal usuário: e-mail duplicado no tenant → erro inline
- ✅ Configurações: salvar fuso horário → recarregar → fuso mantido

---

## 📈 Estimativa Consolidada

| Sprint | Entregável | Dev 1 | Dev 2 | Dias corridos |
|--------|------------|-------|-------|---------------|
| 1 | Keycloak | 1d | — | 1 |
| 2 | Portal Auth | 2d | — | 3 |
| 3 | Admin Backend | 2d | — | 5 |
| 4 | Admin Frontend | 4d | *(paralelo Sprint 5)* | 7 |
| 5 | Gestor Backend | — | 1,5d | 7 |
| 6 | Gestor Frontend | — | 3,5d | 10 |
| 7 | QA + Deploy | 1d | 1d | 11 |
| **Total** | | **10d** | **6d** | **~11 dias corridos** |

> **1 dev sozinho:** ~15 dias | **2 devs em paralelo (Sprint 4+5):** ~11 dias corridos

---

*Documento gerado em: 2026-03-05 | Versão: 2.0.2 | Confidencial — IntelliCare © 2026*
