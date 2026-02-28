# F2 — Especificação Funcional: intellicare-gestor

> **Fase:** 2 | **Prioridade:** P1  
> **Depende de:** F0 (TenantContext), F1 (intellicare-admin provisiona o tenant)  
> **Pode rodar em paralelo com:** F3, F5  
> **Estimativa:** 8 dias | **Novo módulo:** `intellicare-gestor`

---

## 1. Objetivo

Criar o módulo de gestão **por tenant** do IntelliCare. Diferente do `intellicare-admin` (que é da plataforma), o `intellicare-gestor` é usado pelo **administrador local** de cada organização para gerenciar seus próprios usuários, permissões, setores e configurações.

> [!IMPORTANT]
> Este módulo opera no schema `tenant_{id}` — cada tenant tem sua instância lógica isolada.

---

## 2. Personas

| Persona | Descrição | Acesso |
|---|---|---|
| **Admin-Local** | Administrador da organização (ex: diretor do hospital) | Total dentro do tenant |
| **Gestor de Setor** | Coordenador de um setor (ex: coordenador UTI) | Gerencia seu setor |
| **Profissional** | Médico, enfermeira, técnico | Read-only (ver seu perfil) |

---

## 3. Requisitos Funcionais

### RF-F2-001: Gestão de Usuários do Tenant

**Regras:**
1. CRUD de usuários vinculados ao tenant
2. Campos: `nome`, `email`, `cpf`, `cargo`, `conselho` (CRM/COREN), `setor_id`, `ativo`
3. Vincular ao Keycloak: cada usuário tem um `keycloak_user_id`
4. Admin-local pode ativar/desativar usuários (não deletar — soft delete)
5. Limite máximo de usuários conforme plano do tenant (validar via `platform.tenants.max_users`)
6. Convite por email: admin-local insere email → sistema envia convite (via intellicare-comunicacao)

### RF-F2-002: Roles e Permissões (RBAC)

**Regras:**
1. Roles padrão (seed): `admin_local`, `gestor_setor`, `medico`, `enfermeiro`, `tecnico`, `recepcao`
2. Admin-local pode criar roles customizadas
3. Cada role tem uma lista de permissões (JSON)
4. Permissões são granulares: `{modulo}.{acao}` (ex: `oswaldo.classificar`, `florence.ver_resultados`, `comunicacao.enviar_sms`)
5. Um usuário pode ter múltiplas roles
6. Roles do Keycloak devem refletir as roles do gestor (sincronização)

**Tabela de permissões padrão:**

| Role | Permissões |
|---|---|
| `admin_local` | `*` (todas) |
| `gestor_setor` | `{modulo}.ver`, `{modulo}.editar` para seu setor |
| `medico` | `oswaldo.*`, `florence.ver`, `geralda.*`, `comunicacao.enviar_email` |
| `enfermeiro` | `florence.*`, `geralda.ver`, `comunicacao.enviar_email` |
| `tecnico` | `florence.ver`, `zilda.ver` |
| `recepcao` | `zilda.buscar`, `comunicacao.ver` |

### RF-F2-003: Setores/Unidades

**Regras:**
1. CRUD de setores organizacionais
2. Campos: `nome`, `tipo` (UTI, Enfermaria, Ambulatório, Administração), `responsavel_id`
3. Usuários pertencem a um setor (ou mais)
4. Métricas podem ser filtradas por setor
5. Hierarquia simples (setor → sub-setor) com máximo 2 níveis

### RF-F2-004: Configurações do Tenant

**Regras:**
1. Admin-local configura: nome exibido, logo, cores, fuso horário
2. Configuração de canais de comunicação: qual provedor de SMS usar, SMTP settings
3. Configuração de módulos: parâmetros específicos (ex: alertas de Oswaldo a partir de qual estágio DRC)
4. Formato: chave-valor com tipo (string, number, boolean, json)

### RF-F2-005: Auditoria Local

**Regras:**
1. Registrar toda ação relevante dos profissionais do tenant
2. Campos: `user_id`, `ação`, `recurso`, `detalhes`, `ip`, `timestamp`
3. Log imutável (append-only)
4. Pesquisável por data, usuário, ação
5. Exportável (CSV) para compliance LGPD

### RF-F2-006: Dashboard do Gestor

**Regras:**
1. Visão geral do tenant: nº usuários ativos, módulos ativos, uso mensal
2. Últimas atividades (timeline)
3. Alertas (ex: "Plano atingindo limite de SMS", "Usuário inativo há 30 dias")

---

## 4. API Endpoints

| Método | Endpoint | Descrição | Persona |
|---|---|---|---|
| `GET` | `/gestor/users` | Listar usuários do tenant | Admin-Local |
| `POST` | `/gestor/users` | Criar/convidar usuário | Admin-Local |
| `PATCH` | `/gestor/users/{id}` | Atualizar usuário | Admin-Local |
| `DELETE` | `/gestor/users/{id}` | Desativar usuário | Admin-Local |
| `GET` | `/gestor/roles` | Listar roles | Admin-Local |
| `POST` | `/gestor/roles` | Criar role customizada | Admin-Local |
| `PATCH` | `/gestor/roles/{id}` | Atualizar permissões | Admin-Local |
| `GET` | `/gestor/sectors` | Listar setores | Admin-Local, Gestor |
| `POST` | `/gestor/sectors` | Criar setor | Admin-Local |
| `PATCH` | `/gestor/sectors/{id}` | Atualizar setor | Admin-Local |
| `GET` | `/gestor/settings` | Listar configs | Admin-Local |
| `PATCH` | `/gestor/settings` | Atualizar configs | Admin-Local |
| `GET` | `/gestor/audit` | Logs de auditoria | Admin-Local |
| `GET` | `/gestor/dashboard` | Dashboard do gestor | Admin-Local |

> [!WARNING]
> Todos os endpoints recebem `TenantContext` automaticamente via F0. O tenant é extraído do JWT — nunca do path.

---

## 5. Cenários de Teste

| # | Cenário | Saída Esperada |
|---|---|---|
| CT-01 | Criar usuário dentro do limite | Usuário criado, email de convite enviado |
| CT-02 | Criar usuário acima do limite | HTTP 402 "Limite de usuários atingido" |
| CT-03 | Admin de tenant A tenta ver users de tenant B | HTTP 403 (TenantContext impede) |
| CT-04 | Atribuir role com permissão inexistente | HTTP 400 "Permissão inválida" |
| CT-05 | Desativar último admin-local | HTTP 400 "Deve haver pelo menos 1 admin" |
| CT-06 | Buscar auditoria por data | Registros filtrados corretamente |
| CT-07 | Configurar SMS provider | Config salva, próximo SMS usa o novo provider |
