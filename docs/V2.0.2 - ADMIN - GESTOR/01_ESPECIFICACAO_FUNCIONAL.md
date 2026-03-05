# ESPECIFICAÇÃO FUNCIONAL — Admin + Gestor + Portal Auth

**Data**: 2026-03-05
**Status**: 🟡 Em Especificação
**Prioridade**: 🚀 P0 — Crítica
**Versão**: 2.0.2
**Rastreabilidade**: README.md → V2.0.2-ADMIN-GESTOR

---

## 📋 Índice

1. [Visão Geral](#1-visão-geral)
2. [Atores e Perfis](#2-atores-e-perfis)
3. [Premissas Funcionais](#3-premissas-funcionais)
4. [Fluxo de Login e Redirecionamento](#4-fluxo-de-login-e-redirecionamento)
5. [Casos de Uso — PLATFORM_ADMIN](#5-casos-de-uso--platform_admin)
6. [Casos de Uso — TENANT_GESTOR](#6-casos-de-uso--tenant_gestor)
7. [Descrição de Telas](#7-descrição-de-telas)
8. [Regras de Negócio](#8-regras-de-negócio)
9. [Critérios de Aceite](#9-critérios-de-aceite)

---

## 🎯 1. Visão Geral

O IntelliCare é uma plataforma SaaS **multi-tenant** para gestão de saúde. Os módulos `intellicare-admin` e `intellicare-gestor` constituem a **camada administrativa completa**:

| Módulo | Quem acessa | O que faz |
|--------|-------------|-----------|
| `intellicare-admin` | PLATFORM_ADMIN (equipe IntelliCare) | Gerencia clientes (tenants), contratos, planos, módulos habilitados |
| `intellicare-gestor` | TENANT_GESTOR (administrador do cliente) | Gerencia unidades, setores e usuários do seu tenant |
| Portal `/login` | Todos os usuários | Ponto único de autenticação — redireciona por role |

> **Princípio central:** O portal React (porta 3001) é o único ponto de entrada. Um único login redireciona cada usuário para sua área específica conforme a role Keycloak.

---

## 👥 2. Atores e Perfis

| Ator | Role Keycloak | Destino após login | Escopo de acesso |
|------|---------------|-------------------|------------------|
| **PLATFORM_ADMIN** | `PLATFORM_ADMIN` | `/admin` | Toda a plataforma — todos os tenants |
| **TENANT_GESTOR** | `TENANT_GESTOR` | `/gestor` | Apenas seu próprio tenant (tenant_id do JWT) |
| **Profissional de saúde** | `CLINICO` / `MEDICO` / `ENFERMEIRO` | `/dashboard` | Portal clínico com módulos habilitados do tenant |
| **Paciente** | `PACIENTE` | `/paciente` | Área do paciente *(escopo futuro)* |

### Prioridade de roles (usuário com múltiplas roles)

```
PLATFORM_ADMIN > TENANT_GESTOR > CLINICO/MEDICO/ENFERMEIRO > PACIENTE
```

---

## 📌 3. Premissas Funcionais

- ✅ Um **tenant** representa uma organização de saúde (hospital, clínica, operadora)
- ✅ Cada tenant tem dados **completamente isolados** de outros tenants (schema PostgreSQL separado)
- ✅ O PLATFORM_ADMIN **não acessa** área clínica; o TENANT_GESTOR **não acessa** `/admin`
- ✅ **Ativação de módulos clínicos** é responsabilidade exclusiva do PLATFORM_ADMIN
- ✅ O TENANT_GESTOR pode criar usuários clínicos, mas **não pode habilitar módulos**
- ✅ Toda autenticação é via **Keycloak** (OIDC/PKCE) — sem autenticação própria no portal
- ✅ **Isolamento garantido por JWT**: o backend usa o `tenant_id` do token, nunca do body

---

## 🔑 4. Fluxo de Login e Redirecionamento

```
Usuário acessa portal.intellicare.ia.br
         │
         ▼
 ProtectedRoute verifica token
         │
    ┌────┴────┐
    │Sem token│──► /login (preserva rota destino)
    └─────────┘
         │
   Clica "Entrar"
         │
         ▼
 Keycloak OIDC Authorization Code + PKCE
         │
   Retorna ?code=...
         │
         ▼
 authService troca code → access_token + id_token
         │
         ▼
 RoleRouter decodifica JWT → extrai realm_roles
         │
    ┌────┴─────────────────────────────┐
    │                                  │
PLATFORM_ADMIN    TENANT_GESTOR    CLINICO/MEDICO    PACIENTE    (sem role)
    │                  │                 │              │            │
  /admin           /gestor         /dashboard      /paciente   /sem-permissao
```

### Tabela de redirecionamento

| Role (realm_roles no JWT) | Rota destino | Observação |
|---------------------------|--------------|------------|
| `PLATFORM_ADMIN` | `/admin` | Acesso irrestrito à plataforma |
| `TENANT_GESTOR` | `/gestor` | Isolado ao tenant_id do token |
| `CLINICO`, `MEDICO`, `ENFERMEIRO` | `/dashboard` | Módulos conforme habilitados |
| `PACIENTE` | `/paciente` | Escopo futuro |
| *(sem role conhecida)* | `/sem-permissao` | Página explicativa |

> ⚠️ **Segurança PKCE**: NÃO usar Implicit Flow (deprecated). Token **não** vai para localStorage (XSS). Usar memória/sessionStorage apenas.

---

## 🏛️ 5. Casos de Uso — PLATFORM_ADMIN

### CU-01 — Login e acesso ao painel admin

| Campo | Detalhe |
|-------|---------|
| **Ator** | PLATFORM_ADMIN |
| **Pré-condição** | Usuário no Keycloak com realm role `PLATFORM_ADMIN` |
| **Fluxo** | Acessa portal → Autenticado Keycloak → Redirecionado `/admin/dashboard` |
| **Pós-condição** | Dashboard visível com KPIs e últimas atividades |
| **Exceção** | Token sem role → redirecionado `/sem-permissao` |

---

### CU-02 — Cadastrar novo tenant

| Campo | Detalhe |
|-------|---------|
| **Ator** | PLATFORM_ADMIN |
| **Pré-condição** | CNPJ não cadastrado anteriormente |
| **Fluxo** | Clica "Novo Tenant" → Preenche form (nome, CNPJ, e-mail, plano) → Sistema provisiona schema PG + realm Keycloak → Exibe detalhe |
| **Regras** | CNPJ válido (dígitos verificadores); Nome fantasia único; Plano obrigatório |
| **Pós-condição** | Tenant na lista; schema isolado criado; status "Trial" |

---

### CU-03 — Habilitar/desabilitar módulo para tenant

- Admin abre detalhe do tenant → aba **Módulos Contratados**
- Grid de todos os módulos disponíveis com toggle ON/OFF por módulo
- Toggle → `PATCH /admin/tenants/{id}/modules`
- Mudança reflete imediatamente para o gestor do tenant

---

### CU-04 — Gerenciar usuários gestores do tenant

- Admin → aba **Gestores** → "Adicionar Gestor" → form (nome, e-mail, telefone)
- Sistema cria usuário no Keycloak com role `TENANT_GESTOR` + atributo `tenant_id`
- Gestor recebe e-mail de boas-vindas com link de primeiro acesso
- Remover gestor: revoga role no Keycloak (não exclui o usuário)

---

### CU-05 — Gerenciar contrato do tenant

- Admin → aba **Contrato** → plano vigente + período + valor mensal
- "Alterar Plano" → seleciona novo plano + início/fim de vigência
- Histórico de contratos anteriores em tabela colapsável

---

### CU-06 — Suspender / reativar tenant

- Ação "Suspender" exige confirmação (digitar nome do tenant)
- Tenant suspenso: todos os usuários recebem HTTP 402 ao acessar
- Reativar: restabelece acesso imediatamente
- Registra motivo no audit log

---

## 🏥 6. Casos de Uso — TENANT_GESTOR

### CU-10 — Login e acesso ao painel gestor

| Campo | Detalhe |
|-------|---------|
| **Ator** | TENANT_GESTOR |
| **Pré-condição** | Role `TENANT_GESTOR` + atributo `tenant_id` no Keycloak |
| **Fluxo** | Portal → Keycloak valida → RoleRouter lê role → `/gestor/dashboard` |
| **Isolamento** | JWT contém `tenant_id`. Backend valida tenant_id do token = recurso acessado |

---

### CU-11 — Gerenciar unidades/setores

- Acessa `/gestor/unidades` → árvore hierárquica de unidades
- Cria nova unidade: nome, tipo, unidade-pai (opcional), responsável
- Edita via modal; desativa (soft delete — usuários vinculados ficam "sem unidade")
- Limite de hierarquia: **3 níveis** (Hospital → Ala → Setor)

---

### CU-12 — Gerenciar usuários do tenant

- Lista com filtros: busca, unidade, cargo, status (Ativo/Inativo)
- Cria usuário: nome, e-mail, CPF, cargo, conselho, unidade
- Toggle "Enviar convite por e-mail" ao criar
- Edita dados; desativa (soft delete — não exclui do Keycloak)
- ⚠️ **Alerta visual** para usuários sem unidade atribuída (badge vermelho)

---

### CU-13 — Associar usuários a unidades em lote

- Detalhe de unidade → "Gerenciar Usuários"
- Lista todos os usuários do tenant com checkbox
- Salva seleção → `POST /gestor/sectors/{id}/users` com array de `user_ids`

---

### CU-14 — Visualizar módulos habilitados

- Dashboard exibe lista **read-only** dos módulos habilitados pelo PLATFORM_ADMIN
- Cada módulo: nome, ícone, status (Ativo/Inativo)
- Gestor **não pode alterar** — apenas visualizar

---

### CU-15 — Configurações do tenant

- Nome de exibição, fuso horário padrão, e-mails para alertas críticos
- Dados do contrato: **somente leitura** (gerenciado pelo PLATFORM_ADMIN)

---

## 🖥️ 7. Descrição de Telas

### 7.1 Tela: Login (`/login`)

```
┌─────────────────────────────────────────────┐
│          [Logo IntelliCare / White-label]    │
│                                             │
│       Bem-vindo ao IntelliCare              │
│                                             │
│       ┌─────────────────────────────┐       │
│       │   Entrar com sua conta  →   │       │
│       └─────────────────────────────┘       │
│                                             │
│    suporte@intellicare.ia.br  |  v2.1.0    │
└─────────────────────────────────────────────┘
```

- Logo white-label se subdomínio mapeado (ex: `hsaolucas.intellicare.ia.br`)
- Banner de erro (vermelho) se sessão expirada
- Botão único: dispara fluxo Keycloak OIDC

---

### 7.2 Telas Admin — estrutura geral

```
┌──────────────────────────────────────────────────────┐
│ [AdminHeader: "IntelliCare Admin"  [nome admin] [→]] │
├──────────────┬───────────────────────────────────────┤
│              │                                        │
│  📊 Dashboard │           [Conteúdo da rota]          │
│  🏢 Tenants   │                                        │
│  📦 Planos   │                                        │
│  📋 Auditoria │                                        │
│  ⚙️ Config   │                                        │
│              │                                        │
└──────────────┴───────────────────────────────────────┘
```

---

### 7.3 Admin Dashboard (`/admin`)

| Elemento | Conteúdo |
|----------|----------|
| **4 KPI cards** | Total Tenants / Ativos / Em Trial / Suspensos |
| **Gráfico** | Top 5 módulos por nº de tenants ativos (barras) |
| **Alerta** | Tenants com trial expirando em 7 dias (badge laranja) |
| **Tabela** | Últimas 10 atividades: Data \| Ação \| Recurso \| Operador \| Tenant |

---

### 7.4 Admin — Lista de Tenants (`/admin/tenants`)

- Filtros: busca livre + select Status (Todos / Ativo / Trial / Suspenso)
- Tabela paginada (20/página): CNPJ \| Nome \| Plano \| Criado em \| Status \| Ações
- Status: badge colorido (🟢 Ativo, 🟡 Trial, 🔴 Suspenso)
- Ações por linha: `[Detalhes]` `[Suspender/Reativar]`
- Botão "Novo Tenant" → modal de criação

---

### 7.5 Admin — Detalhe do Tenant (`/admin/tenants/:id`)

Header: nome + CNPJ + badge status + `[Suspender]` / `[Reativar]`

**5 abas:**

| Aba | Conteúdo |
|-----|----------|
| **Dados Cadastrais** | Form: nome, e-mail, telefone, branding (logo, cor), domínio |
| **Módulos Contratados** | Grid de cards com toggle ON/OFF por módulo |
| **Gestores** | Lista + "Adicionar Gestor" (modal) + ação "Remover" |
| **Contrato** | Plano vigente + histórico + "Alterar Plano" (modal) |
| **Auditoria** | Log paginado com filtro de período e tipo de ação |

---

### 7.6 Telas Gestor — estrutura geral

```
┌────────────────────────────────────────────────────────┐
│ [Logo tenant / white-label]   [nome gestor]  [→ Sair] │
├──────────────┬─────────────────────────────────────────┤
│  📊 Dashboard │                                         │
│  🏗️ Unidades  │         [Conteúdo da rota]              │
│  👥 Usuários  │                                         │
│  ⚙️ Config   │                                         │
└──────────────┴─────────────────────────────────────────┘
```

---

### 7.7 Gestor Dashboard (`/gestor`)

| Elemento | Conteúdo |
|----------|----------|
| **4 KPI cards** | Total Unidades / Usuários Ativos / 🔴 Sem Unidade / Módulos Habilitados |
| **Mini-tabela** | Top 5 unidades por nº de usuários ativos |
| **Alerta** | "X usuários sem unidade — clique para ver" |
| **Atividades** | Últimas 10 entradas do LocalAuditLog |

---

### 7.8 Gestor — Unidades (`/gestor/unidades`)

- Árvore hierárquica: expandir/colapsar por nível
- Colunas: Nome \| Tipo \| Responsável \| Nº Usuários \| Ações
- Ações: `[Editar]` `[Ver Usuários]` `[Desativar]`
- Botão "Nova Unidade" → modal com form

**Form de unidade:**
- Nome (obrigatório)
- Tipo: `UTI | Enfermaria | Ambulatório | Centro Cirúrgico | Administração | Outro`
- Unidade pai (opcional — sub-unidades)
- Responsável (select de usuários cadastrados)

---

### 7.9 Gestor — Usuários (`/gestor/usuarios`)

- Filtros: busca textual + Unidade + Cargo + toggle Ativo/Inativo
- Tabela: Nome \| E-mail \| Unidade \| Cargo \| Status \| Ações
- ⚠️ Linhas com **fundo amarelo** para usuários sem unidade
- Ações: `[Editar]` `[Desativar]`

**Form de usuário:**
- Nome completo (obrigatório)
- E-mail (obrigatório, único no tenant)
- CPF (opcional)
- Cargo (texto livre: Médico, Enfermeiro, Técnico, Administrativo...)
- Conselho (texto livre: CRM-SP 123456, COREN-SP 789...)
- Unidade (select de unidades ativas)
- Toggle: "Enviar convite por e-mail ao criar"

---

## 📏 8. Regras de Negócio

### RN-01 — Isolamento multi-tenant (crítica)
> Todo dado do gestor é filtrado pelo `tenant_id` **extraído do JWT** — nunca do body da request. Backend rejeita HTTP 403 se `tenant_id` do token ≠ recurso acessado.

### RN-02 — Validação de CNPJ
> CNPJ obrigatório para criação de tenant. Validação dos dígitos verificadores no backend. CNPJ deve ser único em `platform.tenants`.

### RN-03 — Soft delete
> Usuários e unidades **nunca são excluídos fisicamente** — campo `active=false`. Registros inativos não aparecem nas listagens padrão mas ficam no audit log.

### RN-04 — Hierarquia de unidades
> Máximo **3 níveis** de hierarquia (Hospital → Ala → Setor). Não é possível desativar unidade pai sem antes desativar ou reassociar os filhos.

### RN-05 — Módulos habilitados
> A lista de módulos visíveis no portal clínico é determinada **exclusivamente** pelo PLATFORM_ADMIN. Gestor apenas visualiza — não pode habilitar.

### RN-06 — Contrato e trial
> Tenant sem contrato ativo: status "Trial" (30 dias padrão). Após expiração sem contrato: status "Suspenso" (job diário). Suspenso: HTTP 402 para qualquer endpoint do tenant.

### RN-07 — Prioridade de roles
> Usuário com múltiplas roles segue: `PLATFORM_ADMIN > TENANT_GESTOR > CLINICO > PACIENTE`.

---

## ✅ 9. Critérios de Aceite

### CA-01 — Autenticação e Redirecionamento

| Cenário | Resultado esperado |
|---------|--------------------|
| Login com `PLATFORM_ADMIN` | Redirecionado para `/admin/dashboard` em < 3s |
| Login com `TENANT_GESTOR` | Redirecionado para `/gestor/dashboard` em < 3s |
| Acesso a `/admin` com role `TENANT_GESTOR` | HTTP 403 + página "Sem Permissão" |
| Token expirado (após 1h) | Refresh automático; sem logout involuntário |
| Refresh token expirado (após 8h) | Logout + redirect `/login` com "Sessão expirada" |
| Logout clicado | Store limpo + redirect `/login` |

### CA-02 — intellicare-admin

- ✅ `GET /admin/dashboard` retorna totais corretos de tenants por status
- ✅ `POST /admin/tenants` com CNPJ inválido retorna HTTP 422 com campo identificado
- ✅ Toggle de módulo salva e reflete em GET imediato (sem reload)
- ✅ Criar gestor: usuário aparece no Keycloak com role `TENANT_GESTOR`
- ✅ Todos os endpoints retornam 401 sem token, 403 com token sem `PLATFORM_ADMIN`

### CA-03 — intellicare-gestor

- ✅ `GET /gestor/users` com token `tenant_A` retorna APENAS usuários do tenant A
- ✅ Dashboard: badge vermelho visível quando há usuários sem unidade
- ✅ Árvore de unidades: expand/collapse funcional com sub-unidades indentadas
- ✅ Linha de usuário sem unidade: fundo amarelo na tabela
- ✅ Token de tenant diferente: HTTP 403 (isolamento validado)

---

*Documento gerado em: 2026-03-05 | Versão: 2.0.2 | Confidencial — IntelliCare © 2026*
