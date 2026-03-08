# ESPECIFICAÇÃO FUNCIONAL — intellicare-admin

**Módulo:** intellicare-admin
**Versão:** 1.0
**Data:** 2026-03-08
**Status:** Aprovada para implementação

---

## 1. Papel do módulo

O `intellicare-admin` é o **painel de controle da plataforma IntelliCare**.
Ele existe em uma camada acima dos tenants — quem acessa o admin é o
**operador da plataforma** (Eduardo e sua equipe), não o cliente final.

Analogia: se IntelliCare é um SaaS de saúde, o admin é o backoffice da empresa
que vende o SaaS. O gestor é o painel do cliente que comprou o SaaS.

**Quem usa:** usuários com role `PLATFORM_ADMIN` no realm `intellicare`.
**Realm Keycloak:** `intellicare`
**URL:** `admin.intellicare.ia.br`

---

## 2. Funcionalidades

### 2.1 Gestão de Tenants

Um **tenant** é uma organização cliente da plataforma (ex: Clínica São Lucas,
Hospital Regional Norte). Cada tenant tem seus próprios usuários, dados e módulos.

**O admin deve permitir:**

- Listar todos os tenants com: nome, status (ativo/suspenso/trial), plano, data criação
- Criar novo tenant: nome, CNPJ, email responsável, plano, número de usuários contratados
- Ver detalhes de um tenant: todas as informações + módulos ativos + usuários gestores
- Editar dados cadastrais de um tenant
- Ativar / Suspender um tenant
- Encerrar um tenant (soft delete com período de retenção de dados)
- Ver uso atual do tenant: consultas realizadas, armazenamento, usuários ativos

### 2.2 Gestão de Gestores por Tenant

Cada tenant tem um ou mais **gestores** — os usuários responsáveis por operar
o tenant no módulo `intellicare-gestor`.

**O admin deve permitir:**

- Ver quem são os gestores de cada tenant
- Adicionar um gestor a um tenant (cria usuário no Keycloak com role `TENANT_GESTOR` + vincula ao tenant)
- Remover um gestor de um tenant
- Redefinir senha de um gestor

### 2.3 Gestão de Planos

Um **plano** define o que o tenant pode usar: quais módulos, quantos usuários,
quantas consultas por mês, armazenamento.

**O admin deve permitir:**

- Listar planos disponíveis (ex: Starter, Profissional, Enterprise)
- Criar / Editar / Desativar um plano
- Alterar o plano de um tenant
- Ver quais tenants estão em cada plano

### 2.4 Faturamento

**O admin deve permitir:**

- Ver histórico de faturamento por tenant
- Registrar pagamento manual (para clientes que pagam por boleto)
- Ver tenants inadimplentes (vencidos há mais de X dias)
- Gerar relatório de receita mensal

### 2.5 Módulos por Tenant

Cada tenant pode ter diferentes módulos habilitados (Florence, Oswaldo, Donabedian, etc.)

**O admin deve permitir:**

- Ver quais módulos estão ativos por tenant
- Habilitar / Desabilitar um módulo para um tenant
- Ver uso de cada módulo por tenant

### 2.6 Auditoria

**O admin deve registrar e exibir:**

- Todas as ações realizadas no painel (quem fez, o quê, quando)
- Logins de usuários gestores (por tenant)
- Erros críticos nos módulos

### 2.7 Secretarias e Estabelecimentos (futuro)

Gestão de secretarias de saúde e estabelecimentos de saúde vinculados a tenants.
Escopo detalhado a definir na V2 desta spec.

---

## 3. Interface

O módulo tem **dashboard HTML próprio** servido pelo backend FastAPI.
Não depende do portal React para funcionar.

Layout esperado:
```
┌─────────────────────────────────────────────────┐
│  IntelliCare Admin          [admin@plataforma] ▼ │
├────────────┬────────────────────────────────────┤
│            │                                    │
│ Dashboard  │  [conteúdo principal]              │
│ Tenants    │                                    │
│ Gestores   │                                    │
│ Planos     │                                    │
│ Faturamento│                                    │
│ Módulos    │                                    │
│ Auditoria  │                                    │
│            │                                    │
└────────────┴────────────────────────────────────┘
```

A interface usa Keycloak.js para autenticação.
Após login, o token JWT é enviado em todas as chamadas à API.

---

## 4. Regras de negócio

- Somente usuários com role `PLATFORM_ADMIN` no realm `intellicare` têm acesso
- Um tenant suspenso não pode fazer login no gestor nem no portal
- Um tenant encerrado tem seus dados retidos por 90 dias antes da exclusão definitiva
- A criação de um tenant deve provisionar automaticamente:
  - Schema no PostgreSQL
  - Realm ou grupo no Keycloak (a definir na spec técnica)
  - Configuração de Redis com prefixo do tenant
- O plano de um tenant define os limites — exceder limites bloqueia novas operações mas não o acesso existente

---

## 5. Integrações

| Sistema | Como usa |
|---|---|
| Keycloak (realm `intellicare`) | Autenticação do admin, criação de usuários gestores |
| PostgreSQL | Dados de tenants, planos, billing, auditoria |
| intellicare-gestor | Admin cria gestores que então acessam o gestor |
| Todos os módulos | Admin habilita/desabilita módulos por tenant |

---

## 6. O que NÃO é escopo do admin

- Cadastro de pacientes (é do gestor ou do portal)
- Gestão de profissionais (é do gestor)
- Protocolos clínicos (é do Florence)
- Relatórios clínicos (é do Donabedian)
