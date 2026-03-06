# 01 — Especificação Funcional: Keycloak IntelliCare

> **Versão:** 2.0.0 | **Data:** 2026-03-06 | **Status:** ✅ Referência
> **Rastreabilidade:** V2.0.0-KEYCLOAK | **Público-alvo:** PO, Arquitetos, Designers

---

## 🎯 Visão Geral

O Keycloak é o **Identity Provider (IdP) centralizado** do IntelliCare. Toda autenticação e autorização passa por ele — seja um administrador de plataforma, um gestor de hospital, um médico ou uma integração máquina-a-máquina entre módulos.

**Princípios fundamentais:**
- ✅ **Single Sign-On (SSO)** — um login serve todos os módulos e portais
- ✅ **Zero-trust** — cada endpoint valida JWT localmente (sem consultar Keycloak por requisição)
- ✅ **Multi-tenant** — token carrega `tenant_id` que isola dados por schema PostgreSQL
- ✅ **Standards-based** — OIDC 1.0, OAuth 2.1, PKCE, SMART-on-FHIR 2.0

---

## 👥 Atores

### Atores Humanos

| Ator | Role Keycloak | Descrição |
|------|---------------|-----------|
| **Platform Admin** | `PLATFORM_ADMIN` | Eduardo e equipe IntelliCare — acesso total à plataforma |
| **Platform Support** | `PLATFORM_SUPPORT` | Suporte técnico — leitura de logs e dados de tenants |
| **Platform Billing** | `PLATFORM_BILLING` | Financeiro — acesso ao módulo de cobranças |
| **Tenant Gestor** | `TENANT_GESTOR` | Administrador local do hospital/clínica |
| **Médico** | `MEDICO` | Profissional médico com acesso ao módulo clínico |
| **Clínico** | `CLINICO` | Profissional de saúde geral |
| **Enfermeiro** | `ENFERMEIRO` | Profissional de enfermagem |
| **Recepcionista** | `RECEPCIONISTA` | Acesso limitado ao módulo de agendamento |
| **Paciente** | `PACIENTE` | Acesso ao portal do paciente (escopo futuro) |

### Atores de Sistema (Machine-to-Machine)

| Ator | Client Keycloak | Descrição |
|------|-----------------|-----------|
| **Portal React** | `intellicare-portal` | Autenticação via PKCE (public client) |
| **intellicare-wanda** | `intellicare-wanda` | Orquestrador — token exchange e service calls |
| **Módulos clínicos** | `intellicare-florence`, etc. | Validam tokens dos usuários + obtêm tokens próprios |
| **intellicare-admin** | `intellicare-admin` | Painel administrativo (public client) |

---

## 🔄 Fluxos de Autenticação

### Fluxo 1: Login Humano via Portal (Authorization Code + PKCE)

```
Usuário            Portal React         Keycloak              Backend
   │                    │                   │                    │
   │── Acessa /login ──►│                   │                    │
   │                    │── Gera PKCE ──►   │                    │
   │                    │   code_verifier   │                    │
   │                    │   code_challenge  │                    │
   │                    │                   │                    │
   │◄───── Redirect ────│                   │                    │
   │── Login/Senha ────────────────────────►│                    │
   │                    │                   │                    │
   │◄────────────────── Redirect + code ────│                    │
   │                    │                   │                    │
   │── /auth/callback ─►│                   │                    │
   │                    │── POST /token ────►│                   │
   │                    │   code + verifier  │                   │
   │                    │◄─── access_token ──│                   │
   │                    │     refresh_token  │                   │
   │                    │     id_token       │                   │
   │                    │                   │                    │
   │                    │── GET /api/* ─────────────────────────►│
   │                    │   Authorization: Bearer {access_token} │
   │                    │                                        │
   │                    │◄─────────────── 200 OK ───────────────│
```

**Características:**
- `code_challenge_method: S256` (SHA-256)
- `scope: openid profile email`
- Token armazenado em memória (Zustand store) — **nunca em localStorage**
- Refresh automático antes da expiração (5min antes de `exp`)

---

### Fluxo 2: Multi-Tenant Token Exchange

Quando o JWT do Keycloak não contém `tenant_id` ativo (usuário pertence a múltiplos tenants):

```
Portal (TenantContext)          WANDA (/api/v1/token/exchange)
        │                                    │
        │── Token genérico (sem tenant_id) ─►│
        │   + tenant_id desejado             │
        │                                    │── Valida token original
        │                                    │── Gera token tenant-específico
        │                                    │   com tenant_id embedded
        │◄──── Novo access_token ────────────│
        │      (com tenant_id = hospital_abc)│
        │                                    │
        │── Atualiza Zustand store           │
        │── Re-renderiza com tenant ativo    │
```

**Cenários possíveis:**
- ✅ `tenant_id` presente no JWT → carrega direto
- ✅ Apenas 1 tenant em `tenants[]` → exchange automático
- ✅ Múltiplos tenants → exibe seletor ao usuário
- ❌ Nenhum tenant → erro "Nenhuma organização configurada"

---

### Fluxo 3: Machine-to-Machine (Client Credentials)

Para comunicação entre módulos backend:

```
intellicare-wanda              Keycloak              intellicare-florence
        │                          │                         │
        │── POST /token ──────────►│                         │
        │   grant_type=client_credentials                    │
        │   client_id=intellicare-wanda                      │
        │   client_secret=WVmIK...                           │
        │◄── access_token ─────────│                         │
        │                          │                         │
        │── POST /api/v1/analyze ────────────────────────────►│
        │   Authorization: Bearer {access_token}              │
        │◄────────────────────────────────────────────────────│
```

---

### Fluxo 4: SMART-on-FHIR EHR Launch

Para apps clínicos integrados via GRAHAME:

```
EHR System            Portal SMART         Keycloak             GRAHAME
    │                      │                   │                    │
    │── launch=token ──────►│                  │                    │
    │── iss=server_url      │                  │                    │
    │                       │── Auth request ──►│                   │
    │                       │   scope: launch/patient               │
    │                       │          patient/*.read               │
    │                       │◄─── Consent screen ──│               │
    │                       │── Approve ────────────►│             │
    │                       │◄─── code ─────────────│             │
    │                       │── /token + launch ────►│             │
    │                       │◄─── SMART token ───────│             │
    │                       │   patient: P123        │             │
    │                       │   encounter: E456      │             │
    │                       │                        │             │
    │                       │── FHIR request ──────────────────────►│
    │                       │   Authorization: Bearer {smart_token} │
```

---

## 📋 Casos de Uso

### CU-K01: Login Unificado

**Ator:** Qualquer usuário humano
**Pré-condição:** Usuário cadastrado no Keycloak com role atribuída
**Fluxo:**
1. Usuário acessa `https://app.intellicare.ia.br`
2. Portal detecta ausência de token → redireciona para `/login`
3. Portal inicia fluxo PKCE e redireciona para Keycloak
4. Usuário autentica (user/senha ou MFA)
5. Keycloak emite JWT com roles e tenant claims
6. Portal processa callback, armazena tokens, executa `RoleRouter`
7. `RoleRouter` redireciona conforme role: `/admin`, `/gestor`, `/dashboard`

**Pós-condição:** Usuário autenticado e na área correta da plataforma

---

### CU-K02: Refresh de Token

**Ator:** Portal React (automático)
**Pré-condição:** `refresh_token` válido em sessionStorage
**Fluxo:**
1. Interceptor Axios detecta token com menos de 5min de validade
2. Chama `refreshToken()` com `grant_type=refresh_token`
3. Atualiza Zustand store com novos tokens
4. Requisição original é refeita com novo access_token

**Exceção:** refresh_token expirado → logout automático e redirect para `/login`

---

### CU-K03: Seleção de Tenant

**Ator:** Usuário com múltiplos tenants
**Pré-condição:** JWT sem `tenant_id` ativo, `tenants[]` com 2+ entradas
**Fluxo:**
1. `TenantContext` detecta múltiplos tenants sem seleção ativa
2. Exibe modal "Selecione sua organização"
3. Usuário seleciona tenant
4. Frontend chama Wanda `/api/v1/token/exchange`
5. Wanda retorna token com `tenant_id` embutido
6. App reinicializa contexto com tenant selecionado

---

### CU-K04: Logout

**Ator:** Qualquer usuário autenticado
**Fluxo:**
1. Usuário clica "Sair"
2. Portal limpa Zustand store (tokens em memória)
3. Redirect para Keycloak `/logout?post_logout_redirect_uri=.../login`
4. Keycloak invalida sessão SSO
5. Usuário é redirecionado para tela de login

---

### CU-K05: Acesso Negado

**Ator:** Usuário com role insuficiente
**Fluxo:**
1. Usuário tenta acessar endpoint com role insuficiente
2. Backend extrai roles do JWT: `realm_access.roles` + `resource_access.{client}.roles`
3. `require_role("PLATFORM_ADMIN")` verifica lista de roles
4. HTTP 403 retornado: `{"detail": "Role 'PLATFORM_ADMIN' required. You have: CLINICO"}`
5. Frontend exibe tela "Acesso não autorizado"

---

## 📐 Regras de Negócio

| RN | Regra |
|----|-------|
| **RN-K01** | Todo acesso a endpoints protegidos requer JWT Bearer no header `Authorization` |
| **RN-K02** | Validação JWT ocorre **localmente** via JWKS cacheado (5min TTL) — sem chamada ao Keycloak por request |
| **RN-K03** | `tenant_id` no JWT determina o schema PostgreSQL usado — sem `tenant_id`, operação rejeitada com HTTP 428 |
| **RN-K04** | Tokens de acesso NÃO são armazenados em localStorage ou cookies — apenas Zustand (memória) + sessionStorage para PKCE verifier |
| **RN-K05** | Usuários com múltiplos tenants DEVEM selecionar o tenant ativo antes de acessar dados clínicos |
| **RN-K06** | Refresh token tem validade de 30 dias; access token tem validade de 5 minutos |
| **RN-K07** | SMART-on-FHIR scopes não podem ser mais amplos que as roles do usuário autenticado |
| **RN-K08** | Client secrets dos módulos NUNCA são expostos no frontend — apenas confidential clients backend usam secrets |
| **RN-K09** | MFA é opcional no realm `bemcuidar` mas obrigatório para roles `PLATFORM_ADMIN` e `PLATFORM_BILLING` |
| **RN-K10** | Expiração do token é verificada 5 minutos antes do `exp` para refresh proativo |

---

## 🎨 Telas e Fluxos UX

### Tela T-K01: Página de Login (`/login`)

```
┌──────────────────────────────────────┐
│           IntelliCare                │
│         [Logo do tenant]             │
│                                      │
│  Email: [________________________]   │
│  Senha: [________________________]   │
│                                      │
│         [ Entrar com SSO ]           │
│                                      │
│  ────── ou continue com ──────       │
│  [ Google ] [ Microsoft ]            │
│                                      │
│  Esqueci minha senha                 │
└──────────────────────────────────────┘
```

> Nota: A tela de login é renderizada pelo Keycloak (tema customizável).
> O Portal React apenas redireciona para o Keycloak.

### Tela T-K02: Seleção de Tenant

```
┌────────────────────────────────────────────┐
│  Selecione sua organização                 │
│                                            │
│  ┌──────────────────────────────────────┐  │
│  │  🏥 Hospital São João               │  │
│  │     São Paulo - SP                  │  │
│  └──────────────────────────────────────┘  │
│                                            │
│  ┌──────────────────────────────────────┐  │
│  │  🏥 Clínica Bem Cuidar              │  │
│  │     Rio de Janeiro - RJ             │  │
│  └──────────────────────────────────────┘  │
│                                            │
│  [ Confirmar ]    [ Cancelar ]             │
└────────────────────────────────────────────┘
```

### Tela T-K03: RoleRouter (invisível ao usuário)

Componente React que analisa as roles do JWT e redireciona:

```
JWT decoded → roles[]
  │
  ├── PLATFORM_ADMIN / PLATFORM_SUPPORT / PLATFORM_BILLING
  │       └── redirect('/admin')
  │
  ├── TENANT_GESTOR
  │       └── redirect('/gestor')
  │
  ├── MEDICO / CLINICO / ENFERMEIRO / RECEPCIONISTA
  │       └── redirect('/dashboard')
  │
  └── PACIENTE
          └── redirect('/paciente')
```

---

## ✅ Critérios de Aceite

| CA | Critério | Como Verificar |
|----|----------|----------------|
| CA-K01 | Login via PKCE funciona sem exposição do client_secret | DevTools → Network — verificar ausência de secret |
| CA-K02 | JWT expirado retorna HTTP 401 | Testar com token expirado manualmente |
| CA-K03 | Role insuficiente retorna HTTP 403 com mensagem descritiva | Testar com role errada |
| CA-K04 | Refresh automático mantém sessão sem re-login | Aguardar 5min e verificar que sessão continua |
| CA-K05 | Multi-tenant exchange funciona corretamente | Criar usuário com 2 tenants e verificar seleção |
| CA-K06 | Logout invalida sessão SSO | Logout e tentar acessar outro client do mesmo realm |
| CA-K07 | JWKS é cacheado (sem chamada por request) | Prometheus `keycloak_jwks_cache_hits` |
| CA-K08 | Token não aparece em localStorage | DevTools → Application → LocalStorage vazio |

---

*Gerado em: 2026-03-06 | Responsável: Eduardo Garabini*
