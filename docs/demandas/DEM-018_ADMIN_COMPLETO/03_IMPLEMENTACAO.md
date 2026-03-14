# DEM-018 — Implementação Admin Completo

## Resumo das Alterações

A demanda DEM-018 expande o módulo **admin** para gerenciar todas as funcionalidades de usuários e auditar eventos da plataforma de maneira visível e escalável.

### Backend (Módulo Admin)
* Adogados 6 novos modelos Pydantic no arquivo `schemas.py`: `TenantUpdateRequest`, `AuditLogEntry`, `AuditLogResponse`, `UserInviteRequest`, e `UserInviteResponse`.
* Adicionado método `delete_group(group_id)` ao arquivo `keycloak_client.py` para remover grupos correspondentes a tenants arquivados.
* Implementados na classe `TenantService` de `service.py`:
  * `get_dashboard_stats`: Consulta KPIs como número de tenants totais, ativos, suspensos e receita baseada em invoices recentes (com fallback para `0` ou `0.0`).
  * `invite_user`: Adiciona usuário ao grupo do tenant no Keycloak providenciando roles apropriadas.
  * `deactivate_user`: Soft delete na conta Keycloak para suspender acesso.
  * `update_tenant`: Permite modificar metadados do tenant no DB como nome e descrição.
  * `delete_tenant`: Realiza a exclusão completa do schema PostgreSQL para deleção rigorosa e remove grupo no Keycloak.
  * `get_audit_log`: Retorna eventos registrados por paginas e filtra logs de infraestrutura da tabela `platform_audit_log`.
* Expostos 6 rotas REST no arquivo `router.py` correspondendo aos métodos acima.

### Frontend (AdminUI)
* Atualizado `useTenants.ts` incluindo os hooks `useDashboardStats`, `useInviteUser`, `useDeactivateUser`, `useDeleteTenant` e `useAuditLog`.
* Criada e estilizada a página `DashboardPage.tsx` com `SimpleGrid` e cartões `StatCard` exibindo estatísticas recebidas da API `stats`.
* Implementada `TenantUsers.tsx` substituindo as exibições genéricas do list profile para comportar a desativação de usuários e modais de convite vinculados via formulários `@mantine/form`.
* Criada `AuditLog.tsx`, tabela detalhada que expõe a listagem da API contendo filtros por cor baseado no endpoint `/admin/audit`.
* Inclusas novas rotas em `App.tsx` para cobrir as rotas listadas acima, além do atalho "Audit Log" dentro de `AppShell.Navbar`.

### Infraestrutura & Proxy (Traefik)
* Atualizado o `docker-compose.yml` introduzindo labels de SSL Let's Encrypt atreladas ao subdomínio `admin.intellicare.ia.br`.
* Provisionada chave `websecure:443` e regra de middleware de redirecionamento `http->https` forçado via Traefik.
* Configurado path de armazenamento `/letsencrypt/acme.json`.

---

### Execução de Configuração (Checklist)

Para aplicar essa implementação no ambiente:
1. Re-dar build na interface: `cd frontend/AdminUI && npm install && npm run build`
2. Reiniciar API e serviços: `docker compose -f infra/docker-compose.yml up -d`
3. Apontar servidor DNS "admin" da zona ia.br para o IP que acomoda a stack Traefik para Let's Encrypt atestar a chave.
