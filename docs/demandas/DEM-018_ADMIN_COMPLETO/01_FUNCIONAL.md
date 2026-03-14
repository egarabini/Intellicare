# DEM-018 — Admin Module Completo

## 1. Contexto

O módulo admin entregue no DEM-005/006 cobre ~60% do necessário. O core de tenant funciona (criar, listar, suspender), mas faltam: gerenciamento completo de usuários, log de auditoria visível, dashboard com KPIs reais e roteamento por subdomínio (`admin.intellicare.ia.br`).

---

## 2. Escopo

### 2.1 Backend — Endpoints faltantes

| Endpoint | Função |
|---|---|
| `POST /admin/tenants/{slug}/users/invite` | Convidar usuário para tenant (cria no Keycloak + envia email) |
| `PATCH /admin/tenants/{slug}/users/{user_id}/deactivate` | Desativar usuário no Keycloak |
| `GET /admin/audit` | Listar log de auditoria da plataforma (paginado, filtros) |
| `GET /admin/dashboard/stats` | KPIs da plataforma (totais, receita, saúde) |
| `DELETE /admin/tenants/{slug}` | Remover tenant (schema + grupo Keycloak + soft delete) |
| `PATCH /admin/tenants/{slug}` | Editar nome/descrição do tenant |

### 2.2 Frontend — Páginas faltantes

| Página | Conteúdo |
|---|---|
| Dashboard melhorado | KPIs reais: total tenants, ativos, suspensos, receita mensal, módulos healthy |
| Gerenciamento de usuários | Convidar usuário por email + role, desativar usuário |
| Audit Log | Tabela filtável: ator, ação, alvo, data |
| Confirmação de exclusão | Dialog modal antes de deletar tenant |

### 2.3 Infraestrutura — Subdomínio

| Item | Detalhe |
|---|---|
| Traefik labels | Rotear `admin.intellicare.ia.br` → `intellicare-service:8000/admin-ui/` |
| Let's Encrypt | Certificado SSL automático via Traefik ACME |
| DNS | Eduardo configura entrada A no provedor de domínio |

---

## 3. Critérios de Aceite

- [ ] Gestor convidado recebe email e consegue logar
- [ ] Usuário desativado não consegue obter token no Keycloak
- [ ] Audit log mostra as últimas 100 ações com filtro por data
- [ ] Dashboard mostra KPIs reais (não hardcoded)
- [ ] Deletar tenant remove schema + grupo Keycloak
- [ ] `https://admin.intellicare.ia.br` abre o AdminUI com SSL válido
- [ ] `http://admin.intellicare.ia.br` redireciona para HTTPS

---

## 4. Dependências

| DEM | Razão |
|---|---|
| DEM-005 | Backend base — métodos `invite_user` e `deactivate_user` já existem no `keycloak_client.py` |
| DEM-006 | Frontend base — só adicionar páginas e hooks |
| DEM-002 | Traefik já configurado — adicionar labels de subdomínio |
