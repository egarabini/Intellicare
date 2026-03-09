# DEM-002 — Correção e Especificação de Admin e Gestor

| Campo | Valor |
|---|---|
| **ID** | DEM-002 |
| **Título** | Corrigir autenticação e especificar intellicare-admin e intellicare-gestor |
| **Módulos** | intellicare-admin (8010), intellicare-gestor (8011), intellicare-auth |
| **Prioridade** | 🔴 CRÍTICO — bloqueador da plataforma |
| **Status** | APROVADO |
| **Dev responsável** | dev1 |
| **Claude** | Spec aprovada + revisão técnica concluída |
| **Eduardo** | ✅ Aprovado em 2026-03-08 |
| **Data abertura** | 2026-03-08 |
| **Branch** | `fix/admin-gestor-auth` |

---

## Contexto

Os módulos `intellicare-admin` e `intellicare-gestor` são a base da plataforma.
Sem eles funcionando, nenhum tenant pode ser criado, nenhum gestor pode ser
configurado, e nenhuma unidade pode ser cadastrada.

Ambos estão bloqueados por uma combinação de:
1. Realm Keycloak incorreto no código (`bemcuidar` onde deveria ser `intellicare`)
2. Dependências Python ausentes no `pyproject.toml` do admin
3. `configure_auth()` não chamado no app.py do admin
4. Middleware de autenticação definido mas nunca aplicado
5. Rotas do gestor sem guards de autenticação

---

## Arquitetura Keycloak (definição canônica)

```
Keycloak
├── master              ← realm interno do Keycloak (não alterar)
└── intellicare         ← realm da plataforma IntelliCare
    ├── Clientes
    │   ├── intellicare-admin    (confidential, backend)
    │   ├── intellicare-gestor   (confidential, backend)
    │   └── intellicare-portal   (public, SPA)
    └── Roles do realm
        ├── PLATFORM_ADMIN       (acessa admin, vê todos os tenants)
        ├── TENANT_GESTOR        (acessa gestor, vê só seu tenant)
        ├── PROFISSIONAL         (acessa portal, módulos clínicos)
        └── PACIENTE             (acessa portal, área do paciente)
```

**Regra:** todo módulo autentica contra o realm `intellicare`.
O realm `bemcuidar` era nome incorreto — deve ser criado como `intellicare`.

---

## Escopo aprovado

### FASE 1 — Keycloak (pré-requisito para tudo)

- [x] Criar realm `intellicare` no Keycloak em `auth.intellicare.ia.br`
- [x] Criar cliente `intellicare-admin` (confidential)
- [x] Criar cliente `intellicare-gestor` (confidential)
- [x] Criar roles: `PLATFORM_ADMIN`, `TENANT_GESTOR`
- [x] Criar usuário de teste `platform_admin@intellicare.ia.br` com role `PLATFORM_ADMIN`
- [x] Gerar `keycloak_client_secrets.json` para admin e gestor
- [x] Validar: token obtido com credenciais do usuário de teste é válido

### FASE 2 — Corrigir intellicare-admin

- [x] Adicionar `intellicare-core` e `intellicare-auth` ao `pyproject.toml`
- [x] Substituir `python-keycloak` direto por `intellicare-auth`
- [x] Chamar `configure_auth(app, ...)` no `app.py`
- [x] Aplicar middleware de autenticação: `app.add_middleware(AuthMiddleware)`
- [x] Corrigir `dashboard.html`: `realm: 'bemcuidar'` → `realm: 'intellicare'`
- [x] Corrigir `dashboard.html`: URL do auth.intellicare.ia.br
- [x] Usar `TenantAwareSessionFactory` no lugar do engine direto
- [x] Chamar `init_tenant_resolver()` no lifespan
- [x] Testar: acessar `admin.intellicare.ia.br` → redireciona para login Keycloak → após login mostra dashboard

### FASE 3 — Corrigir intellicare-gestor

- [x] Adicionar `intellicare-auth` ao `pyproject.toml` (explícito, não try/except)
- [x] Adicionar `Depends(require_tenant_gestor)` nas rotas: users, roles, sectors, settings, patients, bots
- [x] Criar `require_tenant_gestor` em `deps.py` (valida role `TENANT_GESTOR` no token)
- [x] Criar dashboard React do gestor — **entregue via DEM-003** (intellicare-gestor-frontend, porta 3002)
- [x] Testar: chamada sem token → 403; com token de `PLATFORM_ADMIN` → 403; com token de `TENANT_GESTOR` → 200

### FASE 4 — Smoke test integrado

- [x] Admin cria um tenant via `/api/v1/admin/tenants` → 201 ✅
- [x] Admin atribui um usuário como gestor desse tenant → 201 ✅
- [x] Gestor loga com suas credenciais → acessa `/api/v1/gestor/users` → vê apenas usuários do seu tenant → 200 ✅
- [x] Smoke test: `GET /api/v1/health` admin → 200 ✅ | `GET /api/v1/gestor/health` gestor → 200 ✅

---

## Log de execução

### 2026-03-08 11:10 (America/Sao_Paulo) — FASE 1 concluída
- Subido Keycloak local (`keycloak-db` e `keycloak-intellicare`) e validada disponibilidade em `http://localhost:8080`.
- Criado realm `intellicare`.
- Criados clients confidenciais `intellicare-admin` e `intellicare-gestor` com redirect URIs e web origins.
- Criadas realm roles `PLATFORM_ADMIN` e `TENANT_GESTOR`.
- Criado usuário `platform_admin@intellicare.ia.br` com role `PLATFORM_ADMIN`.
- Gerados arquivos:
  - `intellicare-admin/keycloak_client_secrets.json`
  - `intellicare-gestor/keycloak_client_secrets.json`
- Validação: token obtido com sucesso no endpoint `/realms/intellicare/protocol/openid-connect/token`.

### 2026-03-08 11:18 (America/Sao_Paulo) — FASE 2 (código admin) aplicada
- `intellicare-admin/pyproject.toml`: removido `python-keycloak`; adicionados `intellicare-core` e `intellicare-auth`.
- `admin/api/app.py`: adicionado `configure_auth(...)`, `app.add_middleware(AuthMiddleware)` e `init_tenant_resolver()` no lifespan.
- `admin/db/session.py`: migração para `TenantAwareSessionFactory` com session de plataforma.
- `admin/api/deps.py`: substituído cliente direto por `require_role("PLATFORM_ADMIN")`.
- `admin/templates/dashboard.html`: realm alterado para `intellicare`.

### 2026-03-08 11:24 (America/Sao_Paulo) — FASE 3 (código gestor) aplicada
- `intellicare-gestor/pyproject.toml`: adicionada dependência explícita `intellicare-auth`.
- `gestor/api/app.py`: removido `try/except` de auth e `configure_auth(...)` ficou incondicional.
- `gestor/api/deps.py`: criado `require_tenant_gestor` com validação da role `TENANT_GESTOR` e injeção do `tenant_context`.
- Guards adicionados (`Depends(require_tenant_gestor)`) nas rotas: users, roles, sectors, settings, patients, bots.
- `gestor/config.py`: default de realm alterado para `intellicare`.

### 2026-03-08 11:33 (America/Sao_Paulo) — Hardening pós-revisão técnica
- Corrigida rota sensível `GET /audit` em `gestor/api/audit_routes.py` com `Depends(require_tenant_gestor)`.
- Corrigida rota sensível `GET /dashboard` em `gestor/api/dashboard_routes.py` com `Depends(require_tenant_gestor)`.
- Resultado: todas as rotas de leitura sensível do gestor agora exigem autenticação/autorização `TENANT_GESTOR`.

### 2026-03-08 (America/Sao_Paulo) — FASE 4 concluída por dev1

Smoke test integrado executado com todos os resultados validados:

| Teste | Resultado | Status |
|---|---|---|
| `GET /api/v1/gestor/users` sem token | 403 | ✅ |
| `GET /api/v1/gestor/users` com token `PLATFORM_ADMIN` | 403 | ✅ |
| `GET /api/v1/gestor/users` com token `TENANT_GESTOR` | 200 | ✅ |
| `POST /api/v1/admin/tenants` (criar tenant) | 201 | ✅ |
| `POST /api/v1/admin/tenants/{id}/gestores` (atribuir gestor) | 201 | ✅ |
| `GET /api/v1/health` (admin) | 200 | ✅ |
| `GET /api/v1/gestor/health` (gestor) | 200 | ✅ |

> **Nota para revisão:** sem token retornou `403` (semântica HTTP ideal: `401` para ausência/invalidade de credencial).
> Hoje o middleware colapsa cenários de autenticação/autorização em `403`.
> Melhoria sugerida (não bloqueante): retornar `401` para "sem token/token inválido" e `403` apenas para "token válido sem role/permissão".

### 2026-03-08 (America/Sao_Paulo) — Finalização da revisão por dev1

dev1 concordou com a observação e registrou como melhoria não bloqueante com a seguinte definição canônica:

| Código | Semântica | Quando usar |
|---|---|---|
| `401 Unauthorized` | Falha de **identidade** | Ausência de token ou token inválido/expirado |
| `403 Forbidden` | Falha de **autorização** | Token válido mas sem role/permissão suficiente |

**Estado atual:** middleware retorna `403` para ambos os casos.
**Melhoria futura (não bloqueante):** diferenciar os dois cenários no middleware de autenticação do `intellicare-auth`.

---

## Revisão

**Resultado:** ✅ APROVADO

**Eduardo:** Aprovado. Observação 401 vs 403 concordada — registrada como melhoria não bloqueante para versão futura do middleware.
dev1 finalizou e documentou corretamente o comportamento atual vs. desejado.

---

## Aprendizados

- Realm Keycloak definido como `intellicare` (não `bemcuidar`, não `master`)
- Todo módulo deve declarar `intellicare-auth` explicitamente no pyproject.toml
- Middleware de auth deve ser aplicado via `app.add_middleware()`, não só via `Depends()`
- `dashboard.html` e qualquer frontend embed precisam usar a variável de ambiente, não hardcode
