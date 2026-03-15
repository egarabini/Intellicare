# DEM-030 — Implementacao

## Escopo executado

Implementacao completa do administrativo da plataforma no backend `modules/admin`, migration de plataforma e extensao do `AdminUI` com quatro novas areas:

- Servidores
- Modulos
- Financeiro
- Usuarios Admin

Tambem foi atualizado o dashboard para exibir infraestrutura ativa e custo mensal, e o detalhe do tenant passou a permitir habilitacao de modulos por tenant.

## Arquivos criados

### Banco

- `db/platform_migrations/004_admin_completo.sql`

### Frontend AdminUI

- `frontend/AdminUI/src/hooks/useServers.ts`
- `frontend/AdminUI/src/hooks/useModules.ts`
- `frontend/AdminUI/src/hooks/useFinanceiro.ts`
- `frontend/AdminUI/src/hooks/useAdminUsers.ts`
- `frontend/AdminUI/src/pages/ServersPage.tsx`
- `frontend/AdminUI/src/pages/ModulesPage.tsx`
- `frontend/AdminUI/src/pages/FinanceiroPage.tsx`
- `frontend/AdminUI/src/pages/AdminUsersPage.tsx`

## Arquivos alterados

- `modules/admin/schemas.py`
- `modules/admin/keycloak_client.py`
- `modules/admin/service.py`
- `modules/admin/router.py`
- `frontend/AdminUI/src/App.tsx`
- `frontend/AdminUI/src/components/StatusBadge.tsx`
- `frontend/AdminUI/src/pages/DashboardPage.tsx`
- `frontend/AdminUI/src/pages/TenantDetail.tsx`
- `packages/intellicare-core/intellicare_core/static/admin-ui/index.html`
- `packages/intellicare-core/intellicare_core/static/admin-ui/assets/*`

## Decisoes tecnicas

1. Migration numerada como `004_admin_completo.sql`.
   O `02_TECNICA.md` citava `003_admin_completo.sql`, mas o repositorio ja possui `003_ingest_log.sql`. Foi usado o proximo numero livre para preservar a ordem real de migracoes.

2. `modules/admin/service.py` permaneceu como servico central.
   Em vez de fragmentar em multiplos services agora, a entrega foi mantida no padrao existente do modulo admin para minimizar risco de regressao no bootstrap atual.

3. Keycloak admin users integrados pelo mesmo client do modulo.
   O `keycloak_client.py` foi ampliado para criar, atualizar, desativar e excluir usuarios administrativos com role de realm `PLATFORM_ADMIN`.

4. AdminUI implementado com formularios inline.
   A demanda pedia cobertura funcional completa; foi priorizado fluxo operacional simples e buildavel sobre refinamento de UX com modais ou wizard.

## Desvios da spec

1. O backend publicado tem 31 rotas no router do admin.
   A spec mencionava "16 novos endpoints", mas o escopo real exigiu manter endpoints anteriores de tenants/auditoria e adicionar os novos dominos. O numero final de rotas do router ficou maior por consolidar tudo no mesmo modulo.

2. Exclusao de servidor nao valida vinculacao com tenants.
   A spec mencionava proteger exclusao se existissem associacoes, mas o modelo atual nao possui relacionamento `server -> tenant`. Sem esse contrato no banco, a exclusao foi implementada com validacao apenas de existencia.

3. Financeiro exposto com `PATCH /admin/expenses/{id}` alem do minimo citado.
   O endpoint adicional foi publicado para suportar edicao no AdminUI e evitar uma tela apenas de criacao/exclusao.

## Validacao executada

1. `python -m pytest tests/admin -q`
   Resultado: `8 passed`

2. `python -c "from modules.admin.router import router; print(len(router.routes))"`
   Resultado: `31`

3. `npm run build` em `frontend/AdminUI`
   Resultado: build concluido com sucesso e bundle regenerado em `packages/intellicare-core/intellicare_core/static/admin-ui`

## Pendencias conhecidas

1. O bundle final do AdminUI gera um chunk JS acima de `500 kB`, mas apenas como warning do Vite. Nao bloqueia a entrega funcional.

2. O workspace local contem outras alteracoes paralelas fora da DEM-030. Elas nao fazem parte desta implementacao e nao devem ser misturadas no commit da demanda.
