# Fase 1 - Especificação Funcional: Módulo Admin - Core

> **Fase:** 1/4 | **Prioridade:** P0 (Crítica) | **Estimativa:** 12 dias
> **Depende de:** Fase 0 (TenantContext) | **Bloqueia:** Fase 2, Fase 3
> **DEV Atribuído:** A definir

---

## 1. Objetivo da Fase

Implementar o núcleo do módulo **intellicare-admin**, focado em:
1. CRUD completo de Tenants (empresas/organizações)
2. Provisionamento automatizado (schema DB + Keycloak + seed)
3. Validações e regras de negócio
4. API REST para consumo pelo frontend admin

---

## 2. Requisitos Funcionais

### RF-F1-001: Cadastro de Tenants

**Descrição:** Sistema deve permitir cadastro completo de organizações (hospitais, clínicas, UBS).

**Campos Obrigatórios:**

| Campo | Tipo | Validações | Exemplo |
|-------|------|------------|---------|
| `nome_fantasia` | string(3-150) | Obrigatório, único | "Hospital Santa Clara" |
| `razao_social` | string(3-200) | Obrigatório | "Santa Clara S.A." |
| `cnpj` | string(14) | Formato XX.XXX.XXX/XXXX-XX, dígitos verificadores, único | "12.345.678/0001-90" |
| `email_admin` | string(Email) | Obrigatório, válido, único | "admin@santaclara.com.br" |
| `telefone` | string(11-15) | Obrigatório, formato BR | "+5511999999999" |
| `plano_id` | integer | FK para plans, obrigatório | 1 (trial) |

**Campos Opcionais:**

| Campo | Tipo | Default | Descrição |
|-------|------|---------|-----------|
| `logo_url` | string(255) | NULL | URL da logo do tenant |
| `cor_primaria` | string(7) | "#6366f1" | Cor principal (hex) |
| `cor_secundaria` | string(7) | "#8b5cf6" | Cor secundária (hex) |
| `dominio_custom` | string(100) | NULL | Subdomínio customizado (ex: santaclara.intellicare.ia.br) |
| `endereco` | jsonb | NULL | Endereço completo |
| `configuracoes` | jsonb | {} | Configs extras (limite SMS, etc.) |

**Regras de Negócio:**

1. `tenant_id` (slug) é gerado automaticamente a partir de `nome_fantasia`:
   - Remove caracteres especiais
   - Substitui espaços por hífen
   - Adiciona sufixo numérico se duplicado
   - Ex: "Hospital Santa Clara" → "hospital-santa-clara"

2. Status inicial é sempre `trial`

3. CNPJ deve ser validado:
   - Formato correto (regex)
   - Dígitos verificadores
   - Unicidade no banco

4. Email admin não pode existir em outro tenant

**Exemplo Request:**
```json
POST /admin/tenants
{
  "nome_fantasia": "Hospital Santa Clara",
  "razao_social": "Santa Clara Sociedade Beneficente Hospitalar LTDA",
  "cnpj": "12.345.678/0001-90",
  "email_admin": "admin@santaclara.com.br",
  "telefone": "+5511999999999",
  "plano_id": 1,
  "logo_url": "https://santaclara.com.br/logo.png",
  "cor_primaria": "#3b82f6"
}
```

**Exemplo Response (201 Created):**
```json
{
  "id": 42,
  "tenant_id": "hospital-santa-clara",
  "nome_fantasia": "Hospital Santa Clara",
  "razao_social": "Santa Clara Sociedade Beneficente Hospitalar LTDA",
  "cnpj": "12.345.678/0001-90",
  "email_admin": "admin@santaclara.com.br",
  "telefone": "+5511999999999",
  "plano_id": 1,
  "plano_nome": "Trial (30 dias)",
  "status": "trial",
  "provisionado": false,
  "criado_em": "2026-02-28T09:30:00Z",
  "atualizado_em": "2026-02-28T09:30:00Z"
}
```

---

### RF-F1-002: Provisionamento Automatizado

**Descrição:** Ao criar tenant, sistema deve automaticamente provisionar infraestrutura.

**Fluxo de Provisionamento:**

```
1. VALIDAÇÃO
   ├─ CNPJ único
   ├─ Email único
   └─ Plano existe

2. CRIAR TENANT (DB)
   ├─ INSERT INTO platform.tenants
   └─ Gerar tenant_id slug

3. CRIAR SCHEMA DB
   ├─ CREATE SCHEMA tenant_hospital_santa_clara
   ├─ Rodar Alembic migrations (target schema)
   └─ Inserir seed data (roles, configs)

4. KEYCLOAK: GROUP
   ├─ POST /admin/realms/bemcuidar/groups
   │  {
   │    "name": "tenant_hospital_santa_clara",
   │    "attributes": {
   │      "tenant_id": ["hospital-santa-clara"]
   │    }
   │  }
   └─ Capturar group_id

5. KEYCLOAK: MAPPER
   ├─ PUT /groups/{id}/protocol/mappers/add-model
   │  {
   │    "name": "tenant_id",
   │    "protocol": "openid-connect",
   │    "protocolMapper": "oidc-usermodel-attribute-mapper",
   │    "consentRequired": false,
   │    "claimName": "tenant_id",
   │    "userAttribute": "tenant_id"
   │  }

6. KEYCLOAK: USUÁRIO ADMIN
   ├─ POST /admin/realms/bemcuidar/users
   │  {
   │    "username": "admin_hospital_santa_clara",
   │    "email": "admin@santaclara.com.br",
   │    "enabled": true,
   │    "emailVerified": false,
   │    "attributes": {
   │      "tenant_id": ["hospital-santa-clara"],
   │      "role": ["ADMIN"]
   │    }
   │  }
   └─ Capturar user_id

7. KEYCLOAK: SENHA ADMIN
   ├─ PUT /users/{id}/execute-actions-email
   │  ["UPDATE_PASSWORD"]

8. ASSOCIAR USUÁRIO AO GRUPO
   ├─ PUT /users/{user_id}/groups/{group_id}

9. FINALIZAR
   ├─ UPDATE tenants SET provisionado=true, provisionado_em=NOW()
   └─ Registrar em audit_global

ERRO EM QUALQUER PASSO?
   ├─ ROLLBACK: deletar schema criado
   ├─ ROLLBACK: deletar grupo KC criado
   ├─ ROLLBACK: deletar usuário KC criado
   └─ SET provisionado=false, provisionamento_erro=...
```

**Regras:**

1. Processo é **assíncrono** (background task)
2. Timeout máximo: 30 segundos
3. 3 tentativas automáticas em caso de falha transitória
4. Logs detalhados de cada passo
5. Rollback parcial em caso de falha

**Status de Provisionamento:**

| Status | Descrição |
|--------|-----------|
| `pending` | Aguardando processamento |
| `provisioning` | Em andamento |
| `provisioned` | Concluído com sucesso |
| `failed` | Falhou (ver provisionamento_erro) |

---

### RF-F1-003: Listagem e Busca de Tenants

**Endpoint:** `GET /admin/tenants`

**Query Params:**

| Param | Tipo | Default | Descrição |
|-------|------|---------|-----------|
| `page` | integer | 1 | Número da página |
| `per_page` | integer | 20 | Itens por página (max 100) |
| `status` | string | ALL | Filtra por status (trial, active, suspended, cancelled) |
| `plano_id` | integer | ALL | Filtra por plano |
| `search` | string | NULL | Busca por nome/cnpj/email |
| `sort_by` | string | criado_em | Campo de ordenação |
| `sort_order` | string | desc | asc ou desc |

**Exemplo Response:**
```json
{
  "data": [
    {
      "id": 42,
      "tenant_id": "hospital-santa-clara",
      "nome_fantasia": "Hospital Santa Clara",
      "cnpj": "12.345.678/0001-90",
      "email_admin": "admin@santaclara.com.br",
      "status": "trial",
      "plano_nome": "Trial (30 dias)",
      "provisionado": true,
      "usuarios_count": 5,
      "criado_em": "2026-02-28T09:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 42,
    "total_pages": 3
  }
}
```

---

### RF-F1-004: Detalhes do Tenant

**Endpoint:** `GET /admin/tenants/{id}`

**Retorna informações completas do tenant:**

```json
{
  "id": 42,
  "tenant_id": "hospital-santa-clara",
  "nome_fantasia": "Hospital Santa Clara",
  "razao_social": "Santa Clara Sociedade Beneficente Hospitalar LTDA",
  "cnpj": "12.345.678/0001-90",
  "email_admin": "admin@santaclara.com.br",
  "telefone": "+5511999999999",
  "logo_url": "https://santaclara.com.br/logo.png",
  "cor_primaria": "#3b82f6",
  "cor_secundaria": "#8b5cf6",
  "dominio_custom": null,
  "endereco": null,
  "plano": {
    "id": 1,
    "nome": "Trial (30 dias)",
    "max_usuarios": 5,
    "max_sms_mes": 100,
    "modulos": ["zilda", "florence"]
  },
  "modulos_ativos": ["zilda", "florence"],
  "status": "trial",
  "provisionado": true,
  "provisionado_em": "2026-02-28T09:31:00Z",
  "trial_expira_em": "2026-03-30T00:00:00Z",
  "configuracoes": {
    "limite_sms": 100,
    "limite_usuarios": 5
  },
  "metricas": {
    "usuarios_count": 3,
    "sms_enviados_mes": 12,
    "requests_ultimas_24h": 1456,
    "armazenamento_mb": 23
  },
  "criado_em": "2026-02-28T09:30:00Z",
  "atualizado_em": "2026-02-28T09:31:00Z"
}
```

---

### RF-F1-005: Atualização de Tenant

**Endpoint:** `PATCH /admin/tenants/{id}`

**Campos Editáveis:**

| Campo | Regras |
|-------|--------|
| `nome_fantasia` | Pode alterar, regenera tenant_id se não houver usuários |
| `razao_social` | Livre |
| `email_admin` | Deve ser único, requer reprovisionamento usuário KC |
| `telefone` | Livre |
| `logo_url` | Livre |
| `cor_primaria` | Livre |
| `cor_secundaria` | Livre |
| `dominio_custom` | Único global |
| `plano_id` | Apenas se upgrade (não downgrade) |
| `configuracoes` | Merge com existente |

**Campos NÃO editáveis:**
- `cnpj` (imutável)
- `tenant_id` (imutável após provisionamento)

---

### RF-F1-006: Suspensão e Reativação

**Suspender Tenant:**
```
POST /admin/tenants/{id}/suspend

Body: {
  "motivo": "Atraso no pagamento",
  "suspendido_por": "sistema"
}

Response: 200 OK
{
  "id": 42,
  "status": "suspended",
  "suspendido_em": "2026-02-28T10:00:00Z",
  "motivo_suspensao": "Atraso no pagamento"
}
```

**Regras:**
- Tenant suspenso NÃO pode acessar APIs (HTTP 403)
- Usuários existentes não conseguem fazer login
- Dados são mantidos (não é delete)

**Reativar Tenant:**
```
POST /admin/tenants/{id}/activate

Body: {
  "novo_plano_id": 2,  // opcional: mudar plano ao reativar
  "reativado_por": "admin@intellicare.ia.br"
}

Response: 200 OK
{
  "id": 42,
  "status": "active",
  "reativado_em": "2026-02-28T11:00:00Z"
}
```

---

### RF-F1-007: Validações e Errors

**Códigos de Erro:**

| Código | HTTP | Descrição |
|--------|------|-----------|
| `TENANT_EXISTS` | 409 | CNPJ ou email já cadastrado |
| `TENANT_NOT_FOUND` | 404 | Tenant não encontrado |
| `INVALID_CNPJ` | 400 | CNPJ inválido |
| `INVALID_EMAIL` | 400 | Email inválido |
| `PLAN_NOT_FOUND` | 404 | Plano não existe |
| `PROVISIONING_FAILED` | 500 | Falha no provisionamento |
| `CANNOT_DOWNGRADE_PLAN` | 400 | Não é permitido fazer downgrade de plano |
| `CANNOT_EDIT_PROVISIONED` | 400 | Campo não editável após provisionamento |

**Exemplo Error Response:**
```json
{
  "error": "TENANT_EXISTS",
  "message": "Já existe um tenant com este CNPJ",
  "details": {
    "field": "cnpj",
    "value": "12.345.678/0001-90",
    "existing_tenant_id": 23
  }
}
```

---

## 3. Casos de Teste

### CT-F1-001: Criar Tenant com Sucesso

**Dado:** CNPJ válido, email único, plano existe
**Quando:** POST /admin/tenants com dados completos
**Então:**
- Retorna 201 Created
- Tenant criado no banco (status=pending)
- Job de provisionamento iniciado
- Email enviado para email_admin

### CT-F1-002: CNPJ Duplicado

**Dado:** CNPJ já cadastrado
**Quando:** POST /admin/tenants com CNPJ duplicado
**Então:**
- Retorna 409 Conflict
- Error code: TENANT_EXISTS
- Mensagem informa qual tenant possui o CNPJ

### CT-F1-003: CNPJ Inválido

**Dado:** CNPJ com dígitos verificadores errados
**Quando:** POST /admin/tenants com CNPJ inválido
**Então:**
- Retorna 400 Bad Request
- Error code: INVALID_CNPJ
- Mensagem informa formato correto

### CT-F1-004: Provisionamento Completo

**Dado:** Tenant criado com sucesso
**Quando:** Job de provisionamento executa
**Então:**
- Schema DB criado
- Migrations rodadas no schema
- Grupo Keycloak criado
- Usuário admin criado no Keycloak
- Email de reset de senha enviado
- Tenant marcado como provisionado=true
- Audit log registrado

### CT-F1-005: Falha no Provisionamento com Rollback

**Dado:** Keycloak offline durante provisionamento
**Quando:** Job tenta criar grupo no KC
**Então:**
- Schema DB criado é deletado (rollback)
- Tenant marcado como provisionado=false
- provisionamento_erro preenchido
- Suporte notificado
- 3 retentativas automáticas

### CT-F1-006: Suspender Tenant

**Dado:** Tenant ativo
**Quando:** POST /admin/tenants/{id}/suspend
**Então:**
- Status muda para "suspended"
- suspendido_em preenchido
- Usuários do tenant não conseguem mais login (403)
- APIs do tenant retornam 403

### CT-F1-007: Listar com Filtros

**Dado:** 50 tenants cadastrados
**Quando:** GET /admin/tenants?status=trial&plano_id=1
**Então:**
- Retorna apenas tenants com status=trial E plano_id=1
- Paginação correta
- Total no header correto

### CT-F1-008: Atualizar Campo Imutável

**Dado:** Tenant provisionado com CNPJ
**Quando:** PATCH /admin/tenants/{id} tentando alterar cnpj
**Então:**
- Retorna 400 Bad Request
- Error code: CANNOT_EDIT_PROVISIONED
- Mensagem: "CNPJ não pode ser alterado após provisionamento"

---

## 4. Non-Functional Requirements

### NFR-F1-001: Performance

| Operação | P50 | P95 | P99 |
|----------|-----|-----|-----|
| Criar tenant | 100ms | 200ms | 500ms |
| Listar tenants | 50ms | 100ms | 200ms |
| Detalhes tenant | 30ms | 80ms | 150ms |
| Provisionamento | 10s | 20s | 30s |

### NFR-F1-002: Segurança

1. Todas as ações require autenticação JWT
2. Role obrigatório: `PLATFORM_ADMIN`
3. Auditoria: TODAS as ações registradas em `audit_global`
4. Senhas NUNCA armazenadas (apenas no Keycloak)
5. CNPJ criptografado no banco (opcional, GDPR)

### NFR-F1-003: Disponibilidade

- API: 99.9% uptime
- Provisionamento: 99.5%成功率
- Retry automático: 3 tentativas

---

## 5. Documentação de API

### OpenAPI 3.0

```yaml
/admin/tenants:
  post:
    summary: Criar novo tenant
    tags: [Tenants]
    security:
      - BearerAuth: []
    requestBody:
      required: true
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/TenantCreate'
    responses:
      '201':
        description: Tenant criado
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Tenant'
      '400':
        description: Validação falhou
      '409':
        description: CNPJ ou email já existe

  get:
    summary: Listar tenants
    tags: [Tenants]
    security:
      - BearerAuth: []
    parameters:
      - name: page
        in: query
        schema:
          type: integer
          default: 1
      - name: status
        in: query
        schema:
          type: string
          enum: [trial, active, suspended, cancelled]
    responses:
      '200':
        description: Lista de tenants
```

---

## 6. Mockups de UI (Referência para Frontend)

### Tela de Listagem

```
┌─────────────────────────────────────────────────────────────┐
│ Empresas                                    [Novo +] [Filtros]│
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ ┌──────────────────────────────────────────────────────────┐│
│ │ Hospital Santa Clara                    Trial  Ativo  ●   ││
│ │ 12.345.678/0001-90                         5 usuários    ││
│ │ admin@santaclara.com.br                                   ││
│ └──────────────────────────────────────────────────────────┘│
│                                                             │
│ ┌──────────────────────────────────────────────────────────┐│
│ │ UBS Centro                              Básico  Ativo  ●   ││
│ │ 98.765.432/0001-10                         12 usuários   ││
│ │ admin@ubscentro.com.br                                    ││
│ └──────────────────────────────────────────────────────────┘│
│                                                             │
│ Página 1 de 3    ◀ anterior | 1 | 2 | 3 | próximo ▶        │
└─────────────────────────────────────────────────────────────┘
```

### Tela de Detalhes

```
┌─────────────────────────────────────────────────────────────┐
│ Hospital Santa Clara                                    [X] │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ DADOS CADASTRAIS                                           │
│ ───────────────────────────────────────────────────────────  │
│ Nome Fantasia: Hospital Santa Clara                         │
│ Razão Social: Santa Clara S.A.                              │
│ CNPJ: 12.345.678/0001-90                                    │
│ Email Admin: admin@santaclara.com.br                        │
│ Telefone: +55 11 99999-9999                                 │
│ Status: ✅ Trial (expira em 30 dias)                        │
│ Provisionado: ✅ Sim (2026-02-28 09:31)                      │
│                                                             │
│ PLANO E MÓDULOS                                             │
│ ───────────────────────────────────────────────────────────  │
│ Plano Atual: Trial (30 dias)                 [Upgrade ▶]     │
│                                                             │
│ ✅ Zilda        ✅ Florence                                 │
│ ⬜ Oswaldo      ⬜ Geralda                                  │
│ ⬜ Donabedian   ⬜ Comunicação                              │
│                                                             │
│ MÉTRICAS                                                    │
│ ───────────────────────────────────────────────────────────  │
│ Usuários: 3/5                                              │
│ SMS enviados (mês): 12/100                                  │
│ Storage: 23 MB                                              │
│ Requests (24h): 1,456                                       │
│                                                             │
│ AÇÕES                                                      │
│ ───────────────────────────────────────────────────────────  │
│ [✏️ Editar]  [⏸️ Suspender]  [👁️ Impersonar]  [📊 Analytics]│
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 7. Critérios de Aceite da Fase 1

### Funcionais

- [ ] Super-admin pode criar tenant via API
- [ ] CNPJ validado (formato + dígitos)
- [ ] Email único validado
- [ ] Provisionamento cria schema DB automaticamente
- [ ] Provisionamento cria grupo no Keycloak
- [ ] Provisionamento cria usuário admin no Keycloak
- [ ] Provisionamento envia email de reset de senha
- [ ] Tenant pode ser listado (paginação + filtros)
- [ ] Tenant pode ser editado (campos permitidos)
- [ ] Tenant pode ser suspenso (403 para usuários)
- [ ] Tenant pode ser reativado
- [ ] Audit log registra todas as ações

### Técnicos

- [ ] Schema `platform` criado com tabela `tenants`
- [ ] API REST documentada (OpenAPI)
- [ ] Testes unitários (≥80% cobertura)
- [ ] Testes de integração com Keycloak
- [ ] Migrations Alembic idempotentes
- [ ] Logs estruturados em JSON
- [ ] Background tasks para provisionamento
- [ ] Rollback automatizado em caso de falha

---

## 8. Próximos Passos

Após conclusão da **Fase 1**:

1. ✅ Validar com DEV atribuído
2. 🔵 Iniciar **Fase 2** - Planos e Billing
3. 🔵 Paralelamente: F4 (Módulos Clínicos) podem usar `tenant_id`

---

**Especificação aprovada por:** ___________
**Data:** ___________
