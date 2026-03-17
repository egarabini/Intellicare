# DEM-037 — 03_PLANO

## Objetivo

Aplicar 6 correções independentes no AdminUI e no backend administrativo,
priorizando o item 3 (`gestor_email`) por depender de migration, backend e
frontend em sequência.

## Plano de execução

1. Criar migration `005_gestor_email.sql`.
2. Ajustar schemas, service e router do módulo `admin` para persistir e editar
   `gestor_email`, além de retornar `temporary_password` na criação de admin.
3. Atualizar hooks do AdminUI (`useTenants`, `useAdminUsers`).
4. Ajustar páginas do AdminUI:
   - dashboard com estado vazio
   - listagem e detalhe de tenants com gestor
   - edição de tenant
   - badge "Sem role"
   - modal de senha temporária e erro detalhado em usuários admin
5. Adicionar rota `/tenants/:slug/edit`.
6. Validar com build do AdminUI e checagem sintática do backend.
