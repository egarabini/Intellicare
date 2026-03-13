---
dem: DEM-005
titulo: Admin Backend — Módulo de Gestão de Plataforma
tipo: FUNCIONAL
status: aprovado
criado: 2026-03-13
dependencias: [DEM-002, DEM-003, DEM-004]
---

# DEM-005 · 01 — Especificação Funcional

## Contexto e Motivação

Com infraestrutura (DEM-002), core (DEM-003) e autenticação (DEM-004) estabelecidos, o próximo
passo é o **módulo Admin**: a camada de backend que permite ao `PLATFORM_ADMIN` gerenciar
tenants, usuários e contratos da plataforma IntelliCare V3.

O Admin Backend expõe uma API REST protegida, consumida inicialmente por scripts e futuramente
pelo Admin Frontend (DEM-006). Toda operação cria rastro de auditoria.

## Escopo

### Incluído

- **CRUD de Tenants**: criar, listar, detalhar, suspender, reativar unidades de saúde
- **Provisionamento de schema**: ao criar tenant → `CREATE SCHEMA tenant_{slug}` + tabelas base
- **Gestão de usuários por tenant**: listar, convidar (via Keycloak), remover
- **Auditoria**: tabela `platform_audit_log` no schema `public`, registra quem fez o quê e quando
- **Health check do módulo**: endpoint `/admin/health` compatível com o contrato `BaseModule`

### Excluído (outras DEMs)

- Interface gráfica → DEM-006
- Financeiro / contratos → DEM-007
- Módulos clínicos → DEM-009+

## Atores

| Ator | Ação permitida |
|---|---|
| `PLATFORM_ADMIN` | Todas as operações do módulo |
| `TENANT_GESTOR` | Nenhuma (módulo restrito) |
| `CLINICO` / `PACIENTE` | Nenhuma |

## Casos de Uso Principais

### UC-1: Criar Tenant

**Trigger**: POST `/admin/tenants`  
**Ator**: PLATFORM_ADMIN  
**Fluxo**:
1. Validar payload (nome, slug, email do gestor)
2. Verificar que `slug` não existe
3. `CREATE SCHEMA tenant_{slug}` no PostgreSQL
4. Executar migrations iniciais do tenant (tabelas base: `users`, `knowledge_base`)
5. Criar grupo no Keycloak com `tenant_id = slug`
6. Registrar em `public.tenants`
7. Registrar em `public.platform_audit_log`
8. Retornar representação do tenant criado

**Invariantes**:
- `slug` é imutável após criação
- Operação é **transacional**: se qualquer passo falhar, rollback total
- Slug: `[a-z0-9_]{3,30}`

### UC-2: Listar Tenants

**Trigger**: GET `/admin/tenants`  
**Retorno**: lista paginada com `id, slug, name, status, created_at, user_count`

### UC-3: Detalhar Tenant

**Trigger**: GET `/admin/tenants/{slug}`  
**Retorno**: tenant + usuários vinculados + uso de storage

### UC-4: Suspender / Reativar Tenant

**Trigger**: PATCH `/admin/tenants/{slug}/status`  
**Corpo**: `{ "status": "suspended" | "active" }`  
**Efeito**: atualiza `public.tenants.status`; acesso clínico bloqueado via middleware

### UC-5: Listar Usuários de um Tenant

**Trigger**: GET `/admin/tenants/{slug}/users`  
**Fonte**: Keycloak Admin API (grupo do tenant)

## Modelo de Dados

### `public.tenants` (global, fora de qualquer schema de tenant)

```sql
CREATE TABLE IF NOT EXISTS public.tenants (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug        TEXT NOT NULL UNIQUE CHECK (slug ~ '^[a-z0-9_]{3,30}$'),
    name        TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active','suspended','terminated')),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### `public.platform_audit_log`

```sql
CREATE TABLE IF NOT EXISTS public.platform_audit_log (
    id          BIGSERIAL PRIMARY KEY,
    actor_id    TEXT NOT NULL,      -- user_id do PLATFORM_ADMIN
    actor_email TEXT,
    action      TEXT NOT NULL,      -- e.g. "tenant.create", "tenant.suspend"
    target_type TEXT,               -- e.g. "tenant"
    target_id   TEXT,               -- e.g. slug
    payload     JSONB,              -- dados relevantes da operação
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

## Critérios de Aceite

| # | Critério |
|---|---|
| AC-1 | POST `/admin/tenants` cria schema PostgreSQL + registro em `public.tenants` |
| AC-2 | Slug duplicado → 409 Conflict com mensagem clara |
| AC-3 | Slug inválido → 422 Unprocessable Entity |
| AC-4 | Toda operação bem-sucedida gera registro em `platform_audit_log` |
| AC-5 | Endpoints retornam 403 se token não tem role `PLATFORM_ADMIN` |
| AC-6 | GET `/admin/tenants` retorna lista paginada (`page`, `size`, `total`) |
| AC-7 | PATCH status com valor inválido → 422 |
| AC-8 | `/admin/health` retorna `{"status": "healthy", "module": "admin", "version": "..."}` |
| AC-9 | Falha em qualquer passo do UC-1 → rollback (schema não criado, tenant não registrado) |
| AC-10 | Testes unitários cobrem: validação de slug, lógica de provisionamento, auditoria |

## Não-Funcionais

- Latência p95 < 500ms para operações de leitura
- Operação de criação de tenant (com schema) < 2s
- Logs estruturados em JSON para todas as operações
- Sem segredos no código — usar variáveis de ambiente

## Dependências Técnicas

| Componente | Versão mínima |
|---|---|
| PostgreSQL | 15 (com pgvector) |
| Keycloak | 24 |
| Python | 3.11 |
| FastAPI | 0.111 |
| SQLAlchemy (async) | 2.0 |
| httpx | 0.27 (para Keycloak Admin API) |
