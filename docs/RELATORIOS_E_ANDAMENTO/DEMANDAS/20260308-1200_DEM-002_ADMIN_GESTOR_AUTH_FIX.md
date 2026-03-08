# DEM-002 — Correção e Especificação de Admin e Gestor

| Campo | Valor |
|---|---|
| **ID** | DEM-002 |
| **Título** | Corrigir autenticação e especificar intellicare-admin e intellicare-gestor |
| **Módulos** | intellicare-admin (8010), intellicare-gestor (8011), intellicare-auth |
| **Prioridade** | 🔴 CRÍTICO — bloqueador da plataforma |
| **Status** | EM_DEV |
| **Dev responsável** | A definir |
| **Claude** | Spec criada |
| **Eduardo** | Pendente aprovação |
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

- [ ] Criar realm `intellicare` no Keycloak em `auth.intellicare.ia.br`
- [ ] Criar cliente `intellicare-admin` (confidential)
- [ ] Criar cliente `intellicare-gestor` (confidential)
- [ ] Criar roles: `PLATFORM_ADMIN`, `TENANT_GESTOR`
- [ ] Criar usuário de teste `platform_admin@intellicare.ia.br` com role `PLATFORM_ADMIN`
- [ ] Gerar `keycloak_client_secrets.json` para admin e gestor
- [ ] Validar: token obtido com credenciais do usuário de teste é válido

### FASE 2 — Corrigir intellicare-admin

- [ ] Adicionar `intellicare-core` e `intellicare-auth` ao `pyproject.toml`
- [ ] Substituir `python-keycloak` direto por `intellicare-auth`
- [ ] Chamar `configure_auth(app, ...)` no `app.py`
- [ ] Aplicar middleware de autenticação: `app.add_middleware(AuthMiddleware)`
- [ ] Corrigir `dashboard.html`: `realm: 'bemcuidar'` → `realm: 'intellicare'`
- [ ] Corrigir `dashboard.html`: URL do auth.intellicare.ia.br
- [ ] Usar `TenantAwareSessionFactory` no lugar do engine direto
- [ ] Chamar `init_tenant_resolver()` no lifespan
- [ ] Testar: acessar `admin.intellicare.ia.br` → redireciona para login Keycloak → após login mostra dashboard

### FASE 3 — Corrigir intellicare-gestor

- [ ] Adicionar `intellicare-auth` ao `pyproject.toml` (explícito, não try/except)
- [ ] Adicionar `Depends(require_tenant_gestor)` nas rotas: users, roles, sectors, settings, patients, bots
- [ ] Criar `require_tenant_gestor` em `deps.py` (valida role `TENANT_GESTOR` no token)
- [ ] Criar dashboard HTML básico (ou confirmar que virá do portal React)
- [ ] Testar: chamada sem token → 401; com token de `PLATFORM_ADMIN` → 403; com token de `TENANT_GESTOR` → 200

### FASE 4 — Smoke test integrado

- [ ] Admin cria um tenant via `/api/v1/admin/tenants`
- [ ] Admin atribui um usuário como gestor desse tenant
- [ ] Gestor loga com suas credenciais → acessa `/api/v1/gestor/users` → vê apenas usuários do seu tenant
- [ ] Smoke test `scripts/smoke_test.sh` passa sem erros para admin e gestor

---

## Log de execução

> *Preenchido pelo dev durante a implementação*

---

## Revisão

> *Preenchido por Claude + Eduardo após entrega*

---

## Aprendizados

- Realm Keycloak definido como `intellicare` (não `bemcuidar`, não `master`)
- Todo módulo deve declarar `intellicare-auth` explicitamente no pyproject.toml
- Middleware de auth deve ser aplicado via `app.add_middleware()`, não só via `Depends()`
- `dashboard.html` e qualquer frontend embed precisam usar a variável de ambiente, não hardcode
