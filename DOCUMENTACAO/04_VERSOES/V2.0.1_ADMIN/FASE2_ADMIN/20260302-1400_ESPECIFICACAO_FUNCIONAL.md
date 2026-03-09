# ESPECIFICAÇÃO FUNCIONAL - IntelliCare Admin

**Data**: 2026-03-02
**Status**: 🟡 Especificação Funcional em Elaboração
**Prioridade**: 🚨 ALTA PRIORIDADE
**Rastreabilidade**: README.md → FASE2_ADMIN
**Versão**: 1.0.0

---

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Problema](#problema)
3. [Definição de Escopo](#definição-de-escopo)
4. [Princípios Funcionais](#princípios-funcionais)
5. [Arquitetura Conceitual](#arquitetura-conceitual)
6. [Atores e Casos de Uso](#atores-e-casos-de-uso)
7. [Requisitos Funcionais](#requisitos-funcionais)
8. [Garantias e Restrições](#garantias-e-restrições)
9. [Estrutura de Dados](#estrutura-de-dados)
10. [Fluxos de Operação](#fluxos-de-operação)

---

## 🎯 Visão Geral

O **intellicare-admin** é o módulo de administração da plataforma IntelliCare SaaS, acessível exclusivamente por usuários com a role **PLATFORM_ADMIN**. Este módulo permite:

- ✅ **Gestão de Estabelecimentos**: Cadastro de hospitais, clínicas, laboratórios, secretarias de saúde
- ✅ **Gestão de Usuários Plataforma**: Criação e gerenciamento de usuários com roles `PLATFORM_GESTOR`, `PLATFORM_SUPPORT`, `PLATFORM_BILLING`
- ✅ **Controle de Módulos**: Gerenciamento de quais módulos cada estabelecimento pode acessar
- ✅ **Parâmetros do Sistema**: Configurações por estabelecimento
- ✅ **Billing**: Acompanhamento de uso mensal e geração de cobranças
- ✅ **Monitoramento**: Dashboard global com métricas da plataforma
- ✅ **Auditoria**: Log completo de ações administrativas

> **NOTA IMPORTANTE**:
> - A gestão de **Unidades** e **Usuários de Saúde (HEALTH_*)** é feita pelo módulo **intellicare-gestor** (FASE3), não por este módulo.
> - Este módulo gerencia o nível **PLATAFORMA** (estabelecimentos + usuários plataforma)
> - O módulo **intellicare-gestor** gerencia o nível **SAÚDE** (unidades + usuários de saúde)

### Contexto de Segurança

```
┌─────────────────────────────────────────────────────────────────────┐
│  CAMADA PLATAFORMA (Schema: platform)                                 │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  intellicare-admin (PORT 8010) 🆕 FASE2                      │   │
│  │  ┌────────────────────────────────────────────────────────┐  │   │
│  │  │ 🔒 Protegido por PLATFORM_ADMIN (apenas)                │  │   │
│  │  │                                                          │  │   │
│  │  │ GERENCIA:                                               │  │   │
│  │  │ - Estabelecimentos (Hospitais, Clínicas, Secretarias)    │  │   │
│  │  │ - Usuários PLATAFORMA:                                  │  │   │
│  │  │   • PLATFORM_GESTOR                                     │  │   │
│  │  │   • PLATFORM_SUPPORT                                    │  │   │
│  │  │   • PLATFORM_BILLING                                   │  │   │
│  │  │ - Módulos habilitados por estabelecimento               │  │   │
│  │  │ - Parâmetros do sistema por estabelecimento             │  │   │
│  │  │ - Planos e Billing                                     │  │   │
│  │  └────────────────────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  intellicare-gestor (PORT 8011) 🆕 FASE3                      │   │
│  │  ┌────────────────────────────────────────────────────────┐  │   │
│  │  │ 🔒 Protegido por PLATFORM_ADMIN                          │  │   │
│  │  │          ou PLATFORM_GESTOR                              │  │   │
│  │  │                                                          │  │   │
│  │  │ GERENCIA (por Estabelecimento/Unidade):                 │  │   │
│  │  │ - Unidades de cada Estabelecimento                      │  │   │
│  │  │ - Usuários de SAÚDE (HEALTH_*):                         │  │   │
│  │  │   • HEALTH_MANAGER                                     │  │   │
│  │  │   • HEALTH_PROFESSIONAL                                 │  │   │
│  │  │   • HEALTH_RECEPTIONIST                                 │  │   │
│  │  │   • HEALTH_AUDITOR                                      │  │   │
│  │  │   • HEALTH_CAREGIVER                                   │  │   │
│  │  │   • HEALTH_PATIENT                                     │  │   │
│  │  │                                                          │  │   │
│  │  │ NOTA: PLATFORM_ADMIN deve especificar qual              │  │   │
│  │  │       estabelecimento/unidade está assumindo            │  │   │
│  │  └────────────────────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### Hierarquia de Gerenciamento

```
PLATAFORMA (intellicare-admin)        SAÚDE (intellicare-gestor)
┌──────────────────────────────┐    ┌──────────────────────────────┐
│ PLATFORM_ADMIN (root)         │    │ PLATFORM_ADMIN ou           │
│ Acesso: PORT 8010              │    │ PLATFORM_GESTOR             │
│                               │    │ Acesso: PORT 8011             │
│ Gerencia:                      │    │                               │
│ ├─ Estabelecimentos           │    │ Gerencia:                    │
│ │  ├─ Hospital X              │    │ ├─ Unidades                  │
│ │  ├─ Clínica Y               │    │ │  ├─ Hospital X - U1        │
│ │  └─ Secretária Z            │    │ │  ├─ Hospital X - U2        │
│ │                              │    │ │  └─ Clínica Y - U1         │
│ ├─ Usuários PLATAFORMA:        │    │ │                              │
│ │  ├─ PLATFORM_GESTOR ───────┐│    │ └─ Usuários SAÚDE (HEALTH_*): │
│ │  ├─ PLATFORM_SUPPORT        ││    │    ├─ HEALTH_MANAGER         │
│ │  └─ PLATFORM_BILLING       ││    │    ├─ HEALTH_PROFESSIONAL     │
│ │                              ││    │    ├─ HEALTH_RECEPTIONIST     │
│ ├─ Módulos por estabelecimento││    │    ├─ HEALTH_AUDITOR          │
│ └─ Parâmetros do sistema      ││    │    ├─ HEALTH_CAREGIVER        │
│                               ││    │    └─ HEALTH_PATIENT          │
│ └──────────────────────────────┘│    │                              │
│                                │    └──────────────────────────────┘
└────────────────────────────────┘
```

### Diferença: admin vs gestor

| Aspecto | **intellicare-admin** (FASE2) | **intellicare-gestor** (FASE3) |
|---------|-------------------------------|-------------------------------|
| **Porta** | 8010 | 8011 |
| **Acesso** | PLATFORM_ADMIN (apenas) | PLATFORM_ADMIN + PLATFORM_GESTOR |
| **Gerencia** | Estabelecimentos + Usuários PLATAFORMA | Unidades + Usuários SAÚDE (HEALTH_*) |
| **Escopo** | Nível PLATAFORMA | Nível SAÚDE |
| **Impersonação** | Não aplicável (já é admin) | PLATFORM_ADMIN especifica estabelecimento/unidade |

---

## 🚨 Problema

### Contexto Atual

A plataforma IntelliCare precisa de um módulo administrativo centralizado que:

1. **Controle Multi-Tenant**: Gerencie múltiplas organizações (tenants) de forma isolada
2. **Provisionamento Automático**: Crie automaticamente schemas DB, grupos Keycloak e usuários admin
3. **Controle de Acesso**: Gerencie quais módulos cada tenant pode acessar
4. **Billing**: Acompanhe uso mensal e gere base para cobranças
5. **Segurança**: Restrinja acesso a apenas administradores da plataforma (PLATFORM_ADMIN)

### O Risco sem Módulo Admin

Sem o intellicare-admin:

❌ Provisionamento manual de tenants (propenso a erros)
❌ Sem controle de quem acessa quais módulos
❌ Impossível trackear uso para billing
❌ Sem visibilidade global da plataforma
❌ Dificuldade de suporte (sem impersonação)
❌ Auditoria espalhada ou inexistente

---

## 📐 Definição de Escopo

### Escopo Inclui

1. **CRUD de Estabelecimentos**
   - Cadastro de hospitais, clínicas, laboratórios (estabelecimentos de saúde)
   - Edição de configurações (nome, CNES, logo, contato)
   - Suspensão/reativação de estabelecimentos
   - Exclusão com cleanup completo

2. **Gestão de Usuários Gestores (PLATFORM_GESTOR)**
   - Criação de usuários gestores por estabelecimento
   - Edição de permissões de gestores
   - Desativação de gestores
   - Associação de gestor a estabelecimento(s)

3. **Provisionamento Automático**
   - Criação de schema PostgreSQL por estabelecimento
   - Criação de grupo no Keycloak
   - Configuração de módulos habilitados

4. **Gestão de Planos**
   - Planos seed: trial, básico, profissional, enterprise
   - Limites por plano (usuários, storage, API calls)
   - Up/downgrade de planos
   - Controle de módulos por plano

4. **Billing Básico**
   - Registro mensal de uso
   - Contagem de usuários ativos
   - Contagem de chamadas API
   - Status de pagamento

5. **Monitoramento**
   - Dashboard global de métricas
   - Métricas por tenant
   - Alertas de uso anormal
   - Status de saúde da plataforma

6. **Auditoria**
   - Log de todas as ações administrativas
   - Who, what, when, why
   - Consulta filtrável por período/ator/tenant

7. **Suporte**
   - Impersonação de tenant
   - Acesso temporário ao contexto do tenant
   - Log de sessões de suporte

### Escopo Exclui

❌ Integração com gateway de pagamento (V2.0.2)
❌ Relatórios financeiros completos (V2.0.2)
❌ Auto-scaling de infraestrutura (V2.1.x)
❌ Marketplace de apps (V2.2.x)
❌ Gestão de permissões granulares (V2.0.2)

---

## 🔑 Princípios Funcionais

### P1: Acesso Exclusivo PLATFORM_ADMIN

```
✅ PLATFORM_ADMIN pode acessar intellicare-admin
❌ TENANT_ADMIN NÃO pode acessar intellicare-admin
❌ Usuários sem role não podem acessar
```

**Garantia**: Todo endpoint `/api/v1/admin/*` deve validar role PLATFORM_ADMIN via Keycloak JWT.

### P2: Isolamento de Dados

```
Schema: platform (intellicare-admin)
├── tenants           ← Metadados de tenants
├── plans             ← Planos disponíveis
├── subscriptions     ← Assinaturas por tenant
├── billing_records   ← Registros de uso
└── audit_logs        ← Auditoria

Schema: tenant_{id} (criado por provisioning)
├── users             ← Usuários do tenant
├── settings          ← Configurações específicas
└── ...               ← Outros módulos
```

### P3: Provisionamento Transacional

```
Criar Tenant =
  1. VALIDAR dados (CNPJ, domínio único)
  2. CRIAR registro em platform.tenants
  3. CRIAR schema tenant_{id}
  4. CRIAR grupo no Keycloak
  5. CRIAR usuário admin
  6. SE falha em qualquer passo:
      → ROLLBACK completo
```

### P4: Auditoria Imutável

```
Toda ação em /api/v1/admin/*:
  ├─ WHO: user_id, email, role
  ├─ WHAT: ação, endpoint, payload
  ├─ WHEN: timestamp UTC
  ├─ WHERE: IP, user_agent
  └─ WHY: razão (se aplicável)

Registro em audit_logs (NUNCA deletado)
```

### P5: Impersonação Rastreável

```
Suportista inicia impersonação:
  ├─ Requer role PLATFORM_SUPPORT
  ├─ Registra em audit_logs
  ├─ Gera token temporário com tenant context
  └─ Expira em 1 hora

Ações durante impersonação:
  └─ Auditadas como "original_user AS tenant_user"
```

---

## 🏗️ Arquitetura Conceitual

### Camadas

```
┌──────────────────────────────────────────────────────────┐
│           CAMADA DE APRESENTAÇÃO (API)                    │
│  ┌────────────────────────────────────────────┐          │
│  │  FastAPI + Pydantic                       │          │
│  │  Endpoints: /api/v1/admin/*               │          │
│  │  Docs: /api/v1/docs (OpenAPI)             │          │
│  └────────────────────────────────────────────┘          │
├──────────────────────────────────────────────────────────┤
│           CAMADA DE AUTENTICAÇÃO                          │
│  ┌────────────────────────────────────────────┐          │
│  │  Keycloak JWT Validation                   │          │
│  │  Required Role: PLATFORM_ADMIN             │          │
│  └────────────────────────────────────────────┘          │
├──────────────────────────────────────────────────────────┤
│           CAMADA DE DOMÍNIO                              │
│  ┌──────────┬──────────┬──────────┬──────────┐          │
│  │ Tenant   │ Plan     │ Billing  │ Audit    │          │
│  │ Service  │ Service  │ Service  │ Service  │          │
│  └──────────┴──────────┴──────────┴──────────┘          │
├──────────────────────────────────────────────────────────┤
│           CAMADA DE ACESSO A DADOS                        │
│  ┌────────────────────────────────────────────┐          │
│  │  SQLAlchemy + AsyncPG                      │          │
│  │  Schemas: platform + tenant_{id}          │          │
│  └────────────────────────────────────────────┘          │
├──────────────────────────────────────────────────────────┤
│           CAMADA DE INTEGRAÇÃO                           │
│  ┌──────────┬──────────┬──────────┬──────────┐          │
│  │Keycloak │PostgreSQL│  Redis  │ Prometheus│          │
│  │ Admin   │  Mgmt    │  Cache  │ Metrics   │          │
│  └──────────┴──────────┴──────────┴──────────┘          │
└──────────────────────────────────────────────────────────┘
```

---

## 👥 Atores e Casos de Uso

### Atores

1. **PLATFORM_ADMIN** (Administrador da Plataforma)
   - Acesso total ao módulo intellicare-admin
   - Gerencia estabelecimentos (hospitais, clínicas, etc.)
   - Cria e gerencia usuários PLATFORM_GESTOR
   - Gerencia planos e billing
   - Visualiza métricas globais
   - Realiza auditoria

2. **PLATFORM_GESTOR** (Gestor de Estabelecimento)
   - Criado por PLATFORM_ADMIN
   - Gerencia estabelecimento específico
   - Acesso ao módulo **intellicare-gestor** (PORT 8011)
   - Pode gerenciar usuários de saúde (HEALTH_*) do seu estabelecimento

3. **PLATFORM_SUPPORT** (Suporte)
   - Acesso limitado para diagnósticos
   - Pode impersonar estabelecimentos
   - Visualiza logs de auditoria
   - Não pode modificar estabelecimentos

4. **Sistema** (Jobs Automáticos)
   - Job de billing mensal
   - Job de limpeza de logs antigos
   - Job de verificação de saúde

### Hierarquia de Roles

```
PLATFORM_ADMIN (só acessa intellicare-admin)
    │
    ├─► Cria/gerencia estabelecimentos
    │
    └─► Cria/gerencia PLATFORM_GESTOR
            │
            └─► Acessa intellicare-gestor
                    │
                    ├─► Cria/gerencia HEALTH_MANAGER
                    ├─► Cria/gerencia HEALTH_PROFESSIONAL
                    ├─► Cria/gerencia HEALTH_RECEPTIONIST
                    ├─► Cria/gerencia HEALTH_AUDITOR
                    ├─► Cria/gerencia HEALTH_CAREGIVER
                    └─► Cria/gerencia HEALTH_PATIENT
```

### Casos de Uso Principais

#### UC1: Criar Estabelecimento e Usuário Gestor

```gherkin
Cenário: PLATFORM_ADMIN cria novo hospital e gestor
  Dado que ele tem role PLATFORM_ADMIN
  E ele acessa POST /api/v1/admin/estabelecimentos
  Quando ele envia:
    {
      "nome": "Hospital Santa Clara",
      "cnes": "1234567",
      "cnpj": "12.345.678/0001-90",
      "tipo": "HOSPITAL",
      "gestor": {
        "nome": "Maria Silva",
        "email": "maria.santaclara@email.com",
        "role": "PLATFORM_GESTOR"
      },
      "plano_id": "profissional",
      "modulos": ["florence", "oswaldo", "wanda"]
    }
  Então Sistema:
    - Valida CNES único
    - Valida CNPJ único
    - Cria estabelecimento.status = "provisioning"
    - Cria usuário gestor com role PLATFORM_GESTOR
    - Inicia provisioning assíncrono
  E Sistema garante que:
    - Schema estabelecimento_{uuid} é criado no PostgreSQL
    - Grupo "estabelecimento_{uuid}" é criado no Keycloak
    - Usuário gestor é criado e associado ao estabelecimento
    - Credenciais do gestor são enviadas por email
    - Audit log registra: "WHO criou estabelecimento {uuid}"
    - Provisionamento leva <30s
```

#### UC2: Suspender Estabelecimento

```gherkin
Cenário: PLATFORM_ADMIN suspende estabelecimento por falta de pagamento
  Dado que estabelecimento tem billing.status = "overdue"
  Quando admin chama POST /api/v1/admin/estabelecimentos/{id}/suspender
    {
      "razao": "Pagamento atrasado há 30 dias",
      "data_efetiva": "2026-03-02"
    }
  Então:
    - estabelecimento.status muda para "suspended"
    - Todos os usuários do estabelecimento perdem acesso
    - Keycloak revoga todos os tokens do estabelecimento
    - Email de notificação é enviado ao gestor
    - Audit log registra ação com razão
  E estabelecimento continua:
    - Dados preservados no DB
    - Cobranças acumulando juros
```

#### UC3: Gerenciar Usuário Gestor

```gherkin
Cenário: PLATFORM_ADMIN cria novo gestor para estabelecimento existente
  Dado que estabelecimento "Hospital Santa Clara" existe
  Quando admin chama POST /api/v1/admin/estabelecimentos/{id}/gestores
    {
      "nome": "João Santos",
      "email": "joao.santaclara@email.com",
      "role": "PLATFORM_GESTOR",
      "permissoes": {
        "pode_gerenciar_usuarios": true,
        "pode_gerenciar_pacientes": true,
        "pode_ver_relatorios": true
      }
    }
  Então:
    - Usuário é criado no Keycloak
    - Role PLATFORM_GESTOR é atribuída
    - Usuário é associado ao estabelecimento
    - Email de boas-vindas é enviado
    - Gestor pode acessar intellicare-gestor
  E gestor pode:
    - Gerenciar usuários de saúde (HEALTH_*) do estabelecimento
    - Não pode modificar dados do estabelecimento
```

#### UC4: Impersonar Estabelecimento (Suporte)

```gherkin
Cenário: PLATFORM_SUPPORT precisa diagnosticar problema em estabelecimento
  Dado que ele tem role PLATFORM_SUPPORT
  E estabelecimento tem ticket aberto
  Quando ele chama POST /api/v1/admin/estabelecimentos/{id}/impersonar
  Então:
    - Sistema solicita: "Qual estabelecimento você está assumindo?"
    - Suportista informa: "Hospital Santa Clara"
    - Sistema gera token temporário (1h)
    - Token contém estabelecimento_id e role = "PLATFORM_GESTOR"
    - Audit log registra: "WHO impersonou estabelecimento {id}"
    - Suportista pode acessar módulos como gestor do estabelecimento
  E durante impersonação:
    - Todas as ações são auditadas com "ACTED_AS"
    - Token expira em 1 hora
    - Não pode modificar billing do estabelecimento
```

#### UC5: Gerar Billing Mensal

```gherkin
Cenário: Job de billing roda no dia 1 de cada mês
  Dado que são 00:00 UTC do dia 1
  Quando billing-job roda
  Então para cada estabelecimento ativo:
    - Conta usuários ativos no mês anterior
    - Conta gestores (PLATFORM_GESTOR) ativos
    - Conta chamadas API no mês anterior
    - Calcula storage utilizado
    - Verifica limites do plano
    - Cria billing_record para o mês
    - Compara com limite do plano
    - Se excedeu: marca "overdue" + notifica gestor
  E sistema:
    - Publica métrica: billing_generated_total
    - Registra duração do job
    - Envia resumo para PLATFORM_ADMIN
```

---

## ✅ Requisitos Funcionais

### RF1: Controle de Acesso

- [x] Todo endpoint valida JWT do Keycloak
- [x] Todo endpoint requer role PLATFORM_ADMIN
- [x] Endpoints de suporte requerem PLATFORM_SUPPORT
- [x] Tokens expirados são rejeitados com 401
- [x] Tokens sem role correta são rejeitados com 403

### RF2: Gestão de Estabelecimentos

- [x] Criar estabelecimento com validação de CNES/CNPJ únicos
- [x] Atualizar dados do estabelecimento
- [x] Suspender estabelecimento (bloqueia acesso, preserva dados)
- [x] Reativar estabelecimento
- [x] Excluir estabelecimento (após confirmação + cleanup)
- [x] Listar estabelecimentos (paginado, filtrável)

### RF3: Gestão de Usuários Gestores

- [x] Criar usuário PLATFORM_GESTOR
- [x] Associar gestor a estabelecimento
- [x] Remover associação de gestor
- [x] Listar gestores por estabelecimento
- [x] Desativar gestor (bloqueia acesso)

### RF4: Provisionamento

- [x] Criar schema PostgreSQL estabelecimento_{uuid}
- [x] Criar grupo Keycloak estabelecimento_{uuid}
- [x] Criar usuário admin do tenant
- [x] Enviar credenciais por email
- [x] Rollback completo em caso de falha
- [x] Status de provisionamento atualizável em tempo real

### RF4: Planos e Módulos

- [x] CRUD de planos (trial, básico, profissional, enterprise)
- [x] Definir limites por plano (usuários, storage, API)
- [x] Definir módulos incluídos por plano
- [x] Atualizar plano de tenant (up/downgrade)
- [x] Atualizar módulos habilitados

### RF5: Billing

- [x] Registrar uso mensal (usuários, API, storage)
- [x] Calcular valor baseado no plano
- [x] Marcar status (paid, overdue, cancelled)
- [x] Notificar overdue
- [x] Histórico completo de cobranças

### RF6: Monitoramento

- [x] Dashboard global com métricas:
  - Total tenants (ativos, suspended, trial)
  - Total usuários por plano
  - Uso de API (chamadas no mês)
  - Storage total utilizado
  - Billing (receita mensal, inadimplência)
- [x] Dashboard por tenant
- [x] Métricas Prometheus

### RF7: Auditoria

- [x] Registrar toda ação administrativa
- [x] Campos: who, what, when, where, why
- [x] Logs são imutáveis
- [x] Consulta filtrável por período/ator/tenant
- [x] Export (CSV, JSON)

### RF8: Suporte

- [x] Impersonação de estabelecimento (PLATFORM_SUPPORT)
- [x] Token temporário expira em 1h
- [x] Ações durante impersonação são auditadas
- [x] Log de sessões de suporte

---

## 🔐 Garantias e Restrições

### Garantias

✅ **Garantia 1: Acesso Seguro**
Apenas PLATFORM_ADMIN pode modificar estabelecimentos.

✅ **Garantia 2: Provisionamento Atômico**
Ou provisiona tudo, ou rollback tudo (estado consistente).

✅ **Garantia 3: Auditoria Completa**
Toda ação é registrada e não pode ser alterada.

✅ **Garantia 4: Isolamento de Dados**
Dados de um estabelecimento nunca vazam para outro.

✅ **Garantia 5: Impersonação Rastreável**
Sessões de suporte são totalmente auditadas.

### Restrições

🔒 **Restrição 1: Sem Auto-Atribuição de Role**
PLATFORM_ADMIN não pode promover outro usuário para PLATFORM_ADMIN (requer super-admin).

🔒 **Restrição 2: Sem Exclusão Dura**
Estabelecimentos suspensos não são excluídos automaticamente (requer cleanup manual).

🔒 **Restrição 3: Sem Edição de Billing Passado**
Registros de billing de meses fechados são imutáveis.

🔒 **Restrição 4: Sem Impersonação Ilimitada**
Impersonação expira em 1h e requer reautenticação.

🔒 **Restrição 5: Sem Acesso a Dados de Estabelecimento**
PLATFORM_ADMIN não tem acesso direto aos dados dentro de estabelecimento_{id} (usuários de saúde, etc).

---

## 📊 Estrutura de Dados

### Schema: platform

```sql
-- estabelecimentos
CREATE TABLE estabelecimentos (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  nome VARCHAR NOT NULL,
  cnes VARCHAR(15) UNIQUE, -- CNES do DATASUS
  cnpj VARCHAR UNIQUE,
  tipo VARCHAR NOT NULL, -- HOSPITAL, CLINICA, LABORATORIO, etc

  -- Contato do gestor principal
  gestor_nome VARCHAR,
  gestor_email VARCHAR,
  gestor_telefone VARCHAR,

  logo_url VARCHAR,
  status VARCHAR DEFAULT 'provisioning', -- provisioning, active, suspended, cancelled
  plano_id VARCHAR REFERENCES planos(id),

  -- Configurações
  configuracoes JSONB DEFAULT '{}', -- tema, idioma, timezone

  -- Metadata
  criado_em TIMESTAMP DEFAULT NOW(),
  atualizado_em TIMESTAMP DEFAULT NOW(),
  criado_por UUID,
  provisionado_em TIMESTAMP,
  suspenso_em TIMESTAMP,
  cancelado_em TIMESTAMP,

  rowversion INT DEFAULT 1
);

-- gestores (usuários PLATFORM_GESTOR)
CREATE TABLE gestores (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  estabelecimento_id UUID REFERENCES estabelecimentos(id),

  -- Dados do usuário Keycloak
  usuario_keycloak_id UUID NOT NULL,
  nome VARCHAR NOT NULL,
  email VARCHAR NOT NULL,

  -- Permissões específicas
  permissoes JSONB DEFAULT '{}', -- {"pode_gerenciar_usuarios": true, ...}

  -- Status
  ativo BOOLEAN DEFAULT true,

  -- Metadata
  criado_em TIMESTAMP DEFAULT NOW(),
  criado_por UUID,

  UNIQUE(estabelecimento_id, email)
);

-- planos
CREATE TABLE planos (
  id VARCHAR PRIMARY KEY, -- trial, basico, profissional, enterprise
  nome VARCHAR NOT NULL,
  descricao TEXT,
  preco_mensal NUMERIC,
  moeda VARCHAR DEFAULT 'BRL',

  -- Limites
  max_gestores INT,
  max_usuarios_saude INT,
  max_storage_gb INT,
  max_chamadas_api_mensal INT,

  -- Módulos incluídos
  modulos JSONB DEFAULT '[]', -- ["florence", "oswaldo", "wanda"]

  status VARCHAR DEFAULT 'active',
  criado_em TIMESTAMP DEFAULT NOW()
);

-- modulos_por_estabelecimento (override por estabelecimento)
CREATE TABLE modulos_por_estabelecimento (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  estabelecimento_id UUID REFERENCES estabelecimentos(id),
  nome_modulo VARCHAR NOT NULL,
  habilitado BOOLEAN DEFAULT true,
  configuracao JSONB DEFAULT '{}',
  UNIQUE(estabelecimento_id, nome_modulo)
);

-- registros_billing
CREATE TABLE registros_billing (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  estabelecimento_id UUID REFERENCES estabelecimentos(id),
  periodo_ano INT NOT NULL,
  periodo_mes INT NOT NULL,

  -- Uso
  gestores_ativos INT DEFAULT 0,
  usuarios_saude_ativos INT DEFAULT 0,
  chamadas_api INT DEFAULT 0,
  storage_gb NUMERIC DEFAULT 0,

  -- Valores
  preco_base NUMERIC,
  preco_excedente NUMERIC DEFAULT 0,
  preco_total NUMERIC,

  -- Status
  status VARCHAR DEFAULT 'pending', -- pending, paid, overdue, cancelled
  pago_em TIMESTAMP,
  data_vencimento DATE,

  criado_em TIMESTAMP DEFAULT NOW(),
  UNIQUE(estabelecimento_id, periodo_ano, periodo_mes)
);

-- audit_logs
CREATE TABLE audit_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  ator_id UUID NOT NULL,
  ator_email VARCHAR NOT NULL,
  ator_role VARCHAR NOT NULL,

  acao VARCHAR NOT NULL, -- CREATE_ESTABELECIMENTO, SUSPEND_ESTABELECIMENTO, etc
  tipo_alvo VARCHAR, -- estabelecimento, gestor, plano, billing
  id_alvo UUID,

  payload JSONB,
  resultado VARCHAR, -- success, failure
  mensagem_erro TEXT,

  ip VARCHAR,
  user_agent TEXT,

  impersonado_como UUID, -- se aplicável
  razao TEXT,

  criado_em TIMESTAMP DEFAULT NOW()
);

-- sessoes_suporte (impersonation)
CREATE TABLE sessoes_suporte (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  usuario_suporte_id UUID NOT NULL,
  estabelecimento_id UUID REFERENCES estabelecimentos(id),
  impersonado_como UUID, -- user_id sendo impersonado

  iniciado_em TIMESTAMP DEFAULT NOW(),
  encerrado_em TIMESTAMP,
  razao TEXT,

  status VARCHAR DEFAULT 'active', -- active, expired, ended
  token_hash VARCHAR, -- hash do token gerado
);
```

---

## 🔄 Fluxos de Operação

### Fluxo 1: Provisionamento de Tenant

```
[POST /api/v1/admin/tenants]
    │ Validar JWT (PLATFORM_ADMIN)
    │ Validar payload (CNPJ, domínio)
    ▼
[Criar Tenant Record]
    INSERT INTO platform.tenants
    VALUES (status='provisioning')
    ▼
[Publicar Evento: tenant.provisioning]
    Redis Stream / RabbitMQ
    ▼
[Provisioning Worker]
    1. Criar schema tenant_{uuid}
    2. Criar tabelas base
    3. Criar grupo Keycloak
    4. Criar usuário admin
    5. Enviar email
    6. Atualizar tenant.status='active'
    ▼
[Sucesso] ou [Rollback + Erro]
```

### Fluxo 2: Suspensão de Tenant

```
[POST /api/v1/admin/tenants/{id}/suspend]
    │ Validar JWT (PLATFORM_ADMIN)
    │ Verificar tenant existe
    ▼
[Atualizar Tenant]
    UPDATE tenants
    SET status='suspended', suspended_at=NOW()
    WHERE id={id}
    ▼
[Keycloak Revoke]
    Desabilitar todos os usuários do tenant
    Revogar tokens ativos
    ▼
[Notificar]
    Enviar email para admin do tenant
    ▼
[Auditar]
    INSERT INTO audit_logs
    (action='SUSPEND_TENANT', ...)
```

### Fluxo 3: Impersonação

```
[POST /api/v1/admin/tenants/{id}/impersonate]
    │ Validar JWT (PLATFORM_SUPPORT)
    │ Verificar ticket existe
    ▼
[Criar Sessão Suporte]
    INSERT INTO support_sessions
    (support_user_id, tenant_id, status='active')
    ▼
[Gerar Token Temporário]
    JWT com:
    - sub: original_user_id
    - tenant_id: {id}
    - roles: ["TENANT_ADMIN"]
    - act_as: {tenant_admin_id}
    - exp: now() + 1h
    ▼
[Retornar Token]
    { "token": "eyJ...", "expires_at": "..." }
    ▼
[Auditar]
    INSERT INTO audit_logs
    (action='IMPERSONATE', impersonated_as={id})
```

### Fluxo 4: Billing Mensal

```
[Job: 00:00 UTC dia 1]
    │ Para cada tenant ativo:
    ▼
[Contar Usuários Ativos]
    SELECT COUNT(*) FROM tenant_{id}.users
    WHERE last_active >= previous_month_start
    ▼
[Contar Chamadas API]
    SUM(api_calls) FROM metrics
    WHERE tenant_id={id} AND month=previous
    ▼
[Calcular Storage]
    SUM(table_size) FROM pg_tables
    WHERE schemaname='tenant_{id}'
    ▼
[Criar Billing Record]
    INSERT INTO billing_records
    (tenant_id, period, usage, total_price)
    ▼
[Verificar Limites]
    IF usage > plan.limits:
      status='overdue'
      NOTIFICAR admin
    ▼
[Publicar Métricas]
    billing_total, billing_overdue, etc
```

---

## 📝 Resumo de Entregas Funcionais

| Requisito | Descrição | Prioridade |
|-----------|-----------|:---:|
| Autenticação PLATFORM_ADMIN | JWT + Keycloak role validation | 🔴 CRÍTICA |
| CRUD Tenants | Cadastro completo de organizações | 🔴 CRÍTICA |
| Provisionamento Automático | Schema + KC + usuário admin | 🔴 CRÍTICA |
| Gestão de Planos | Planos seed + limites | 🔴 CRÍTICA |
| Billing Básico | Uso mensal + status | 🟡 ALTA |
| Dashboard Global | Métricas da plataforma | 🟡 ALTA |
| Auditoria | Logs imutáveis | 🔴 CRÍTICA |
| Impersonação | Suporte técnico | 🟢 MÉDIA |

---

## 🚀 Próximos Passos

1. **Aprovação**: Validar esta especificação com stakeholder
2. **Especificação Técnica**: Ver `20260302-1405_ESPECIFICACAO_TECNICA.md`
3. **Plano de Implementação**: Ver `20260302-1410_PLANO_IMPLEMENTACAO.md`
4. **Desenvolvimento**: Seguir passos em `PASSOS_IMPLEMENTACAO.md`

---

**Especificação Funcional v1.0.0**
**Data**: 2026-03-02
**Responsável**: IntelliCare Team
**Aprovado por**: ___________
**Data Aprovação**: ___________
