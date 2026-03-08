# ESPECIFICAÇÃO FUNCIONAL — intellicare-gestor

**Módulo:** intellicare-gestor
**Versão:** 1.0
**Data:** 2026-03-08
**Status:** Aprovada para implementação

---

## 1. Papel do módulo

O `intellicare-gestor` é o **painel de controle do tenant**.
Quem acessa o gestor é o **administrador da clínica/hospital** que contratou
o IntelliCare — ele gerencia as unidades, os profissionais e como os
profissionais estão alocados nas unidades.

Analogia: o admin é a Salesforce (quem vende o CRM). O gestor é o admin interno
de cada empresa que comprou o CRM — ele cria usuários, define papéis, organiza times.

**Quem usa:** usuários com role `TENANT_GESTOR` no realm `intellicare`, vinculados a um tenant específico.
**Realm Keycloak:** `intellicare`
**URL:** `gestor.intellicare.ia.br`
**Isolamento:** um gestor vê APENAS os dados do seu tenant. Nunca dados de outro tenant.

---

## 2. Funcionalidades

### 2.1 Dashboard inicial

Ao entrar, o gestor vê um resumo do tenant:

- Total de unidades cadastradas e ativas
- Total de profissionais cadastrados e ativos
- Total de usuários com acesso ao portal
- Módulos ativos (quais estão habilitados para este tenant)
- Alertas pendentes (ex: profissionais sem unidade alocada)

### 2.2 Gestão de Unidades

Uma **unidade** é um local físico ou virtual onde os atendimentos acontecem
(ex: Clínica Central, Unidade Norte, Pronto-Atendimento).

**O gestor deve permitir:**

- Listar unidades com: nome, tipo, endereço, número de profissionais alocados, status
- Criar nova unidade: nome, tipo (clínica, hospital, UBS, telemedicina), endereço, CNES
- Editar dados de uma unidade
- Ativar / Desativar uma unidade
- Ver quais profissionais estão alocados em cada unidade
- Ver agenda e capacidade da unidade (futuro — integração com módulo de agenda)

### 2.3 Gestão de Profissionais

Um **profissional** é qualquer pessoa que presta serviço nas unidades:
médicos, enfermeiros, técnicos, recepcionistas, etc.

**O gestor deve permitir:**

- Listar profissionais com: nome, CRM/COREN/registro, especialidade, unidades alocadas, status
- Criar profissional: dados pessoais, registro profissional, especialidade, carga horária
- Editar dados de um profissional
- Ativar / Desativar um profissional
- Ver histórico de atendimentos do profissional (futuro — integração FHIR)

### 2.4 Alocação de Profissionais

A **alocação** é o vínculo entre um profissional e uma unidade. Um profissional
pode estar alocado em múltiplas unidades, com diferentes cargas horárias.

**O gestor deve permitir:**

- Alocar um profissional a uma unidade (definir cargo, período, carga horária)
- Remover alocação de um profissional
- Ver todos os profissionais de uma unidade
- Ver todas as unidades de um profissional
- Definir profissional responsável de uma unidade (chefe de serviço)

### 2.5 Gestão de Usuários do Portal

Cada profissional cadastrado pode (ou não) ter acesso ao portal React.
O gestor controla quem tem acesso e com qual perfil.

**O gestor deve permitir:**

- Criar acesso ao portal para um profissional (cria usuário no Keycloak)
- Desativar acesso de um profissional
- Redefinir senha de um profissional
- Definir perfil de acesso: quais módulos o profissional pode usar

### 2.6 Gestão de Roles e Permissões

**O gestor deve permitir:**

- Criar roles personalizadas para o tenant (ex: "Médico Plantonista", "Enfermeiro Chefe")
- Associar módulos e permissões a cada role
- Atribuir roles a profissionais

### 2.7 Configurações do Tenant

**O gestor deve permitir:**

- Editar dados do tenant: nome fantasia, logotipo, cores (white-label)
- Configurar horário de funcionamento padrão das unidades
- Configurar integrações: webhooks, chaves de API de terceiros
- Ver limites do plano atual (quantos usuários restam, armazenamento usado)

### 2.8 Cadastro de Pacientes (básico)

**O gestor deve permitir:**

- Listar pacientes do tenant (nome, CPF, data nascimento, unidade de referência)
- Criar / Editar cadastro básico de paciente
- Importar pacientes via CSV (futuro)

> O módulo clínico completo do paciente (prontuário, consultas, exames) é gerenciado
> pelos módulos Florence, Oswaldo, Donabedian — não pelo gestor.

### 2.9 Auditoria do Tenant

**O gestor deve visualizar:**

- Ações realizadas no painel do gestor (quem fez, o quê, quando)
- Logins dos usuários do tenant
- Alterações em alocações e profissionais

### 2.10 Bots e Automações (futuro)

Configuração de bots do módulo Nise para o tenant.
Escopo detalhado a definir na integração Gestor + Nise.

---

## 3. Interface

O módulo **não tem dashboard HTML próprio** na versão atual.
As duas opções são:
1. **Opção A:** Criar dashboard HTML próprio (como o admin) — serve pelo FastAPI, usa Keycloak.js
2. **Opção B:** Construir as páginas no portal React — gestor acessa via `gestor.intellicare.ia.br` que serve o portal

**Decisão pendente com Eduardo.** Para a Fase 1 de correção, implementar Opção A
(dashboard HTML básico) para ter o módulo funcionando independente do portal.
Portal será a interface definitiva na V2.

---

## 4. Regras de negócio

- Somente usuários com role `TENANT_GESTOR` + claim `tenant_id` correspondente podem acessar
- Um gestor só vê dados do SEU tenant — isolamento é obrigatório em todas as queries
- Um profissional pode estar alocado em no máximo N unidades (N definido pelo plano)
- Desativar uma unidade não remove as alocações — apenas suspende novos atendimentos
- A criação de um usuário no portal deve criar o usuário no Keycloak automaticamente
- Logs de auditoria são imutáveis — não podem ser editados ou excluídos

---

## 5. Integrações

| Sistema | Como usa |
|---|---|
| Keycloak (realm `intellicare`) | Autenticação do gestor, criação de usuários do portal |
| PostgreSQL (schema do tenant) | Todos os dados do tenant: unidades, profissionais, alocações |
| Redis (prefixo do tenant) | Cache de sessão e configurações |
| intellicare-admin | Admin cria o gestor; gestor não acessa o admin |
| intellicare-portal | Portal usa os dados de profissionais/unidades do gestor |
| intellicare-zilda | Validação de CNES das unidades (futuro) |

---

## 6. O que NÃO é escopo do gestor

- Gerenciar tenants (é do admin)
- Gerenciar planos e billing (é do admin)
- Prontuário clínico de pacientes (é Florence/Oswaldo)
- Indicadores de qualidade (é Donabedian)
- Protocolos clínicos (é Florence)
