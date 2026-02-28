# F1 — Especificação Funcional: intellicare-admin

> **Fase:** 1 | **Prioridade:** P0  
> **Depende de:** F0 (TenantContext) | **Bloqueia:** F2, F3, F5  
> **Estimativa:** 10 dias | **Novo módulo:** `intellicare-admin`

---

## 1. Objetivo

Criar o módulo de administração da plataforma IntelliCare SaaS. Este módulo é usado pelos **operadores da plataforma** (super-admins) para gerenciar empresas/organizações (tenants), planos, módulos contratados e monitoramento global.

> [!IMPORTANT]
> Este módulo opera no schema `platform` e **NUNCA** acessa dados de tenants individuais diretamente.

---

## 2. Personas

| Persona | Descrição | Acesso |
|---|---|---|
| **Super-Admin** | Operador IntelliCare (nós) | Total — CRUD tenants, billing, auditoria |
| **Suporte** | Equipe de suporte ao cliente | Read-only em tenants, pode impersonar |
| **Financeiro** | Equipe de cobrança | Billing, relatórios financeiros |

---

## 3. Requisitos Funcionais

### RF-F1-001: Cadastro de Empresas (Tenants)

**Regras:**
1. CRUD completo de tenants (Criar, Ler, Atualizar, Desativar)
2. Campos obrigatórios: `nome_fantasia`, `razao_social`, `cnpj`, `email_admin`
3. Campos opcionais: `logo_url`, `cor_primaria`, `cor_secundaria`, `dominio_custom`
4. CNPJ deve ser único e validado (formato + dígitos verificadores)
5. `tenant_id` (slug) é gerado automaticamente a partir do nome_fantasia
6. Status: `active`, `suspended`, `trial`, `cancelled`
7. Criar tenant = provisionar schema no banco (via script F0)

### RF-F1-002: Planos e Módulos

**Regras:**
1. Cada tenant tem um plano: `trial`, `basico`, `profissional`, `enterprise`
2. Cada plano define quais módulos estão inclusos
3. Módulos ativáveis: Zilda, Oswaldo, Florence, Donabedian, Geralda, Comunicação, Wanda, Grahame
4. Super-admin pode ativar/desativar módulos individualmente por tenant
5. Módulos desativados retornam HTTP 403 para aquele tenant

| Plano | Módulos | Usuários | SMS/mês |
|---|---|---|---|
| Trial | Zilda + Florence | 5 | 100 |
| Básico | Zilda + Florence + Oswaldo + Geralda | 20 | 500 |
| Profissional | Todos exceto Wanda IA | 100 | 2.000 |
| Enterprise | Todos | Ilimitado | 10.000 |

### RF-F1-003: Provisioning Automatizado

**Regras:**
1. Ao criar um tenant, o sistema deve automaticamente:
   - Criar schema `tenant_{id}` no PostgreSQL
   - Rodar migrations nesse schema
   - Criar grupo no Keycloak com mapper `tenant_id`
   - Criar usuário admin-local no Keycloak (email_admin do cadastro)
   - Inserir seed data (roles padrão, configs iniciais)
   - Registrar log de provisionamento
2. Processo deve ser idempotente (retry seguro)
3. Deve ter rollback em caso de falha parcial

### RF-F1-004: Monitoramento Global

**Regras:**
1. Dashboard com visão de todos os tenants
2. Métricas: nº de usuários, requests/dia, storage usado, SMS enviados
3. Alertas: tenant com trial expirando, uso acima do plano, erros frequentes
4. Capacidade de filtrar/buscar tenants

### RF-F1-005: Impersonação (Support)

**Regras:**
1. Suporte pode "entrar" no contexto de um tenant para diagnóstico
2. Toda ação durante impersonação é logada com `actor=support:{user_id}` 
3. Impersonação requer aprovação de outro super-admin (2FA operacional)
4. Sessão de impersonação expira em 30 minutos

### RF-F1-006: Billing

**Regras:**
1. Registrar uso mensal por tenant (usuários ativos, SMS enviados, requests)
2. Gerar registro de cobrança com base no plano
3. Status de pagamento: `pending`, `paid`, `overdue`, `grace`
4. Tenant com billing `overdue` por >15 dias → status `suspended`
5. Relatórios exportáveis (CSV)

---

## 4. API Endpoints

| Método | Endpoint | Descrição | Persona |
|---|---|---|---|
| `POST` | `/admin/tenants` | Criar tenant + provisioning | Super-Admin |
| `GET` | `/admin/tenants` | Listar tenants (paginado) | Super-Admin, Suporte |
| `GET` | `/admin/tenants/{id}` | Detalhes do tenant | Super-Admin, Suporte |
| `PATCH` | `/admin/tenants/{id}` | Atualizar tenant | Super-Admin |
| `POST` | `/admin/tenants/{id}/suspend` | Suspender tenant | Super-Admin |
| `POST` | `/admin/tenants/{id}/activate` | Reativar tenant | Super-Admin |
| `GET` | `/admin/tenants/{id}/modules` | Módulos do tenant | Super-Admin |
| `PATCH` | `/admin/tenants/{id}/modules` | Ativar/desativar módulos | Super-Admin |
| `GET` | `/admin/plans` | Listar planos | Todos |
| `GET` | `/admin/dashboard` | Métricas globais | Super-Admin |
| `POST` | `/admin/impersonate/{tenant_id}` | Iniciar impersonação | Suporte |
| `GET` | `/admin/billing` | Relatório de billing | Financeiro |
| `GET` | `/admin/billing/{tenant_id}` | Billing de um tenant | Financeiro |
| `GET` | `/admin/audit` | Log de auditoria global | Super-Admin |

---

## 5. Cenários de Teste

| # | Cenário | Saída Esperada |
|---|---|---|
| CT-01 | Criar tenant com CNPJ válido | Schema criado, KC grupo criado, status=trial |
| CT-02 | Criar tenant com CNPJ duplicado | HTTP 409 Conflict |
| CT-03 | Suspender tenant | Status=suspended, requests do tenant → 403 |
| CT-04 | Ativar módulo não incluído no plano | HTTP 400 "Módulo não disponível no plano" |
| CT-05 | Billing overdue > 15 dias | Tenant automaticamente suspenso |
| CT-06 | Impersonação sem aprovação | HTTP 403 |
| CT-07 | Listar tenants (paginação) | 20 por página, total correto no header |
