# F3 — Especificação Funcional: Portal Multi-Tenant

> **Fase:** 3 | **Prioridade:** P1  
> **Depende de:** F0 (TenantContext), F1 (tenants cadastrados)  
> **Pode rodar em paralelo com:** F2, F4  
> **Estimativa:** 5 dias | **Módulo:** `intellicare-portal` (MODIFICAR)

---

## 1. Objetivo

Adaptar o `intellicare-portal` para funcionar em modo multi-tenant. O portal deve identificar o tenant do usuário logado e apresentar apenas os módulos, branding e dados daquele tenant.

---

## 2. Requisitos Funcionais

### RF-F3-001: Login com Roteamento por Tenant

**Regras:**
1. Login via Keycloak retorna JWT com `tenants[]` (array de tenants autorizados) e possivelmente `tenant_id` (se single-tenant)
2. Portal decodifica JWT e verifica:
   - Se `tenants.length == 1` → **auto-select**: faz token exchange silencioso e entra direto
   - Se `tenants.length > 1` e `tenant_id == null` → exibe **Tela de Seleção de Organização**
   - Se `tenant_id` presente → entra direto no tenant selecionado
3. Após seleção, portal armazena o novo JWT (com `tenant_id` fixo) no state global
4. Todas as chamadas API incluem `Authorization: Bearer {token}` (tenant extraído do JWT no backend)
5. Se token não contiver `tenant_id` nem `tenants[]` → tela de erro "Organização não configurada"

### RF-F3-002: Branding por Tenant

**Regras:**
1. Após login, portal busca branding do tenant: `GET /gestor/settings?category=branding`
2. Aplicar: nome da organização (header), logo, cores primária/secundária
3. Fallback: se branding não configurado, usar tema IntelliCare padrão
4. CSS Variables dinâmicas (`--color-primary`, `--color-secondary`, etc.)

### RF-F3-003: Módulos Condicionais

**Regras:**
1. Após login, buscar módulos ativos: `GET /admin/tenants/{id}/modules` ou claim do JWT
2. Dashboard exibe apenas módulos ativos para aquele tenant
3. Módulos desativados não devem ter rota acessível
4. Menu lateral mostra apenas módulos disponíveis

### RF-F3-004: Multi-Tenant Transparente

**Regras:**
1. O usuário final **não precisa saber** que a aplicação é multi-tenant
2. Nenhuma URL contém `tenant_id` (segurança)
3. Isolamento é 100% via JWT — frontend não manipula tenant diretamente
4. Trocar de organização = botão "Trocar Organização" no menu do usuário (não precisa refazer login)

### RF-F3-005: Tela de Seleção de Organização

> [!IMPORTANT]
> Este requisito é **obrigatório** para suportar profissionais que trabalham em múltiplas organizações (cenário comum em saúde).

**Descrição:** Quando Dr. Luiz faz login e trabalha em 3 hospitais diferentes, ele vê uma tela para escolher em qual hospital deseja acessar.

**Regras:**
1. Exibida automaticamente quando `tenants.length > 1` e `tenant_id == null`
2. Lista todos os tenants do array `tenants[]` com nome e logo de cada organização
3. Ao clicar em uma organização, Portal faz **Token Exchange** no Keycloak:
   ```
   POST /realms/bemcuidar/protocol/openid-connect/token
   grant_type=urn:ietf:params:oauth:grant-type:token-exchange
   &subject_token={jwt_original}
   &tenant_id={tenant_selecionado}
   ```
4. Novo JWT retornado contém `tenant_id` fixo → armazenar e prosseguir
5. Não exibida se usuário tem apenas 1 tenant (auto-select silencioso)
6. Design: tela limpa, central, com cards por organização

### RF-F3-006: Trocar de Organização

**Descrição:** Um usuário multi-org pode trocar de organização sem refazer login.

**Regras:**
1. Botão "Trocar Organização" visível no menu do usuário (apenas se `tenants.length > 1`)
2. Ao clicar, exibe a mesma Tela de Seleção (RF-F3-005)
3. Ao selecionar outro tenant: novo Token Exchange, atualizar TenantContext, recarregar dados
4. Limpar cache local (branding, módulos, dados do dashboard anterior)
5. Header exibe o nome da organização atual para orientação do usuário

---

## 3. Cenários de Teste

| # | Cenário | Saída Esperada |
|---|---|---|
| CT-01 | Login com tenant_id válido (single-tenant) | Dashboard com branding do tenant |
| CT-02 | Login com tenant sem módulo Oswaldo | OswaldoPage não aparece no menu |
| CT-03 | Acesso direto a `/oswaldo` com módulo desativado | Redirect para dashboard |
| CT-04 | Tenant com branding customizado | Logo e cores do tenant aplicados |
| CT-05 | Tenant sem branding | Tema padrão IntelliCare |
| CT-06 | Login multi-org (3 tenants) | Tela de Seleção exibida com 3 opções |
| CT-07 | Selecionar organização na tela | Token exchange, dashboard carrega com tenant selecionado |
| CT-08 | Trocar de organização via menu | Nova tela de seleção, dados recarregados |
| CT-09 | Login com 1 tenant (auto-select) | Nenhuma tela de seleção, entra direto |
