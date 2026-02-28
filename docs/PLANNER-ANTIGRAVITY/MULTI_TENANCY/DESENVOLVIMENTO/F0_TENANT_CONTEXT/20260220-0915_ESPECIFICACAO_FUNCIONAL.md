# F0 — Especificação Funcional: TenantContext + Infraestrutura

> **Fase:** 0 (Fundação) | **Prioridade:** P0 — Bloqueante para todas as fases  
> **Depende de:** Nenhuma | **Estimativa:** 5 dias  
> **Módulos afetados:** `intellicare-core`, `intellicare-auth`, PostgreSQL, Redis, Keycloak

---

## 1. Objetivo

Criar a infraestrutura base de multi-tenancy que será usada por **todos** os módulos IntelliCare. Ao fim desta fase, qualquer módulo poderá identificar "a qual empresa pertence esta requisição" e acessar o schema correto do banco de dados.

---

## 2. Requisitos Funcionais

### RF-F0-001: Identificação do Tenant na Requisição

**Descrição:** Toda requisição HTTP autenticada deve conter a informação de qual tenant o usuário pertence.

**Regras:**
1. O `tenant_id` deve vir como claim no token JWT do Keycloak
2. O claim deve se chamar `tenant_id` (tipo: string)
3. Adicionalmente, o JWT contém `tenants` (tipo: array de strings) com **todos** os tenants que o usuário tem acesso
4. Se o token não contiver `tenant_id` E não contiver `tenants`, a requisição deve ser rejeitada com HTTP 403
5. Se o token contiver `tenants` mas não `tenant_id`, o backend retorna HTTP 428 "Tenant não selecionado" (indica que o Portal deve exibir a tela de seleção)
6. Exceção: endpoints de plataforma (`/admin/*`, `/health`) não exigem `tenant_id`
7. O `tenant_id` deve ser um slug alfanumérico (ex: `hospital_einstein`, `ubs_centro_sp`)

**Formato do JWT — Usuário com 1 tenant (auto-select):**
```json
{
  "sub": "user-uuid",
  "preferred_username": "dr.silva",
  "tenant_id": "hospital_einstein",
  "tenants": ["hospital_einstein"],
  "realm_access": {
    "roles": ["medico", "tenant_admin"]
  }
}
```

**Formato do JWT — Usuário multi-org (pré-seleção):**
```json
{
  "sub": "user-uuid",
  "preferred_username": "dr.luiz",
  "tenant_id": null,
  "tenants": ["hospital_einstein", "hospital_sirio", "ubs_centro_sp"],
  "realm_access": {
    "roles": ["medico"]
  }
}
```

**Formato do JWT — Após seleção (token exchange):**
```json
{
  "sub": "user-uuid",
  "preferred_username": "dr.luiz",
  "tenant_id": "hospital_sirio",
  "tenants": ["hospital_einstein", "hospital_sirio", "ubs_centro_sp"],
  "realm_access": {
    "roles": ["medico"]
  }
}
```

### RF-F0-002: Contexto de Tenant Propagado

**Descrição:** Um objeto `TenantContext` deve ser criado por requisição e propagado para todos os serviços, repositórios e dispatchers.

**Regras:**
1. `TenantContext` contém: `tenant_id`, `tenant_schema`, `user_id`, `user_roles`
2. Deve ser injetável via FastAPI `Depends()`
3. Deve ser acessível em qualquer camada (API → Service → Repository → DB)
4. Não pode ser alterado após criação (imutável)

### RF-F0-003: Isolamento de Dados por Schema

**Descrição:** Cada tenant deve ter seu próprio schema no PostgreSQL.

**Regras:**
1. Formato do schema: `tenant_{tenant_id}` (ex: `tenant_hospital_einstein`)
2. Cada schema contém as mesmas tabelas (estrutura idêntica entre tenants)
3. Queries NUNCA devem acessar schema de outro tenant
4. O schema `platform` é reservado para dados da plataforma (admin)
5. O schema `public` NÃO deve ser usado para dados de negócio

### RF-F0-004: Isolamento de Cache Redis

**Descrição:** Cada tenant deve ter seu cache isolado no Redis.

**Regras:**
1. Formato da key: `tenant:{tenant_id}:{module}:{key_original}` 
2. Exemplo: `tenant:hospital_einstein:zilda:cnes:2077485`
3. TTLs permanecem conforme configuração do módulo
4. Streams Redis: `tenant:{tenant_id}:intellicare:{event_type}`

### RF-F0-005: Configuração de Módulo por Tenant

**Descrição:** `BaseModuleConfig` deve suportar configurações específicas por tenant.

**Regras:**
1. Configuração global (env vars) é o fallback
2. Configuração por tenant (banco `platform.tenant_configs`) tem prioridade
3. Cada módulo pode ter configs próprias por tenant (ex: hospital A usa Twilio, hospital B usa Zenvia para SMS)

### RF-F0-006: Fluxo Multi-Organização (Usuário em Múltiplos Tenants)

**Descrição:** Profissionais de saúde frequentemente trabalham em mais de uma organização (ex: Dr. Luiz é médico no Hospital Einstein e na UBS Centro). O sistema deve suportar esse cenário nativamente.

**Regras:**
1. Cada usuário no Keycloak possui um atributo `tenants` (array JSON) com todos os tenant_ids autorizados
2. No momento do login, Keycloak retorna JWT com `tenants: [...]` e `tenant_id: null`
3. Se `tenants.length == 1` → Portal faz **auto-select**: aplica token exchange imediatamente com o único tenant, sem exibir tela de seleção
4. Se `tenants.length > 1` → Portal exibe **Tela de Seleção de Organização** antes de entrar
5. Ao selecionar, Portal faz **Token Exchange** no Keycloak para obter novo JWT com `tenant_id` fixo
6. A partir do token com `tenant_id`, o fluxo segue normalmente (RF-F0-001)
7. Usuário pode trocar de organização a qualquer momento via menu ("Trocar Organização")
8. Trocar de organização = novo token exchange, novo TenantContext, reload dos dados

**Fluxo:**
```
Dr. Luiz → Login Keycloak → JWT: tenants=["hosp_a","hosp_b","ubs_c"], tenant_id=null
                                    │
                           Portal detecta tenants.length > 1
                                    │
                           Exibe Tela de Seleção:
                           ┌──────────────────────┐
                           │ 🏥 Hospital Einstein  │
                           │ 🏥 Hospital Sírio     │
                           │ 🏥 UBS Centro SP      │
                           └──────────────────────┘
                                    │
                           Dr. Luiz seleciona "Hospital Sírio"
                                    │
                           Token Exchange → JWT: tenant_id="hospital_sirio"
                                    │
                           Dashboard carrega com dados do Hospital Sírio
```

**Token Exchange (Keycloak):**
```
POST /realms/bemcuidar/protocol/openid-connect/token
Content-Type: application/x-www-form-urlencoded

grant_type=urn:ietf:params:oauth:grant-type:token-exchange
&subject_token={token_original}
&requested_token_type=urn:ietf:params:oauth:token-type:access_token
&audience=intellicare-portal
&tenant_id=hospital_sirio
```

---

## 3. Requisitos Não-Funcionais

| ID | Requisito | Critério |
|---|---|---|
| RNF-F0-001 | Performance | Overhead de resolução de tenant < 5ms por request |
| RNF-F0-002 | Segurança | Impossível acessar dados de tenant diferente (zero cross-tenant leak) |
| RNF-F0-003 | Compatibilidade | Módulos existentes devem funcionar sem alteração se rodando em modo single-tenant (`tenant_id = "default"`) |
| RNF-F0-004 | Observabilidade | Logs devem incluir `tenant_id` em todas as linhas |

---

## 4. Fluxo Principal

```
[Requisição HTTP]
       │
       ▼
[FastAPI Middleware]
       │ Extrai JWT → claim "tenant_id"
       ▼
[TenantMiddleware]
       │ Cria TenantContext(tenant_id, schema, user)
       │ Injeta no request.state
       ▼
[Depends(get_tenant_context)]
       │ Retorna TenantContext do request.state
       ▼
[Service Layer]
       │ Recebe TenantContext via DI
       ▼
[OperationalDataAccess(schema=ctx.tenant_schema)]
       │ Executa queries no schema correto
       ▼
[PostgreSQL: tenant_{id}.tabela]
```

---

## 5. Cenários de Teste (Critérios de Aceite)

| # | Cenário | Entrada | Saída Esperada |
|---|---|---|---|
| CT-01 | Token com `tenant_id` válido | JWT: `tenant_id: "hosp_a"` | `TenantContext.tenant_id == "hosp_a"` |
| CT-02 | Token sem `tenant_id` nem `tenants` | JWT: sem claims | HTTP 403 "Tenant não identificado" |
| CT-03 | Tenant não provisionado | JWT: `tenant_id: "inexistente"` | HTTP 403 "Tenant não encontrado" |
| CT-04 | Isolamento de query | Tenant A cria registro | Tenant B não vê o registro |
| CT-05 | Redis isolado | Tenant A cacheia valor | Tenant B não encontra a key |
| CT-06 | Modo single-tenant | Sem configuração de tenant | Usa `tenant_id: "default"`, funciona normalmente |
| CT-07 | Log com tenant | Qualquer request | Todas linhas de log contêm `tenant_id` |
| CT-08 | Usuário com 1 tenant (auto-select) | JWT: `tenants: ["hosp_a"]` | Auto token exchange, `tenant_id: "hosp_a"` |
| CT-09 | Usuário multi-org sem seleção | JWT: `tenants: ["a","b"]`, `tenant_id: null` | HTTP 428 "Selecione uma organização" |
| CT-10 | Token exchange com tenant válido | Exchange com `tenant_id: "hosp_b"` | Novo JWT com `tenant_id: "hosp_b"` |
| CT-11 | Token exchange com tenant não autorizado | Exchange com tenant fora do `tenants[]` | HTTP 403 "Acesso negado a este tenant" |
