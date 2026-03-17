# DEM-037 — 04_DIARIO

## 2026-03-17

- Lidas `01_FUNCIONAL.md` e `02_TECNICA.md`.
- Confirmado que o item 3 exigia ordem rígida:
  migration → backend → frontend.
- Criada migration `db/platform_migrations/005_gestor_email.sql`.
- Backend ajustado em `modules/admin/`:
  - `TenantResponse` com `gestor_email`
  - `TenantUpdate` criado
  - `AdminUserOut` com `temporary_password`
  - criação de tenant persistindo `gestor_email`
  - update de tenant suportando `name` e `gestor_email`
  - endpoint alterado para `PUT /tenants/{slug}`
  - criação de admin retornando `temporary_password`
- Frontend AdminUI ajustado:
  - `DashboardPage` com alert de ambiente vazio
  - `TenantList` com coluna Gestor e botão editar
  - `TenantDetail` exibindo gestor
  - `TenantForm` refatorado para criação e edição (`TenantEditForm`)
  - `TenantUsers` com badge cinza "Sem role"
  - `AdminUsersPage` com modal de senha temporária e erro detalhado
  - `App.tsx` com rota `/tenants/:slug/edit`
- Validação executada:
  - `npm run build` em `frontend/AdminUI`
  - `py_compile` em `modules/admin/schemas.py`, `service.py`, `router.py`
