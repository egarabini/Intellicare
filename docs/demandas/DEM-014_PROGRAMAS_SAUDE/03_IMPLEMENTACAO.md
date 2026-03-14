# DEM-014 - Implementacao

## Escopo funcional executado

Como o `01_FUNCIONAL.md` nao estava presente no repositorio, o escopo funcional foi reconstruido a partir do pedido e da `02_TECNICA.md`:

- gerenciar programas de saude (`health_programs`)
- matricular pacientes em programas (`program_enrollments`)
- identificar pacientes sem visita ha mais de `N` dias
- calcular cobertura do programa (`enrolled_count / target_count * 100`)

## Arquivos criados

- `db/tenant_migrations/005_programas_tables.sql`
- `modules/programas/__init__.py`
- `modules/programas/schemas.py`
- `modules/programas/service.py`
- `modules/programas/router.py`
- `modules/programas/main.py`
- `tests/programas/test_programas_service.py`

## Arquivos alterados

- `packages/intellicare-core/intellicare_core/module_loader/loader.py`
- `packages/intellicare-core/intellicare_core/main.py`

## Decisoes de implementacao

- O modulo foi alinhado aos contratos reais do repo, usando `TenantContext` de `intellicare_core.contracts.base` e `tenant_session()` de `intellicare_core.db.session`, seguindo o padrao de `modules/cuidado`.
- O router local de `programas` nao recebeu prefixo proprio. O prefixo final `/programas` e aplicado pelo `ModuleLoader`, evitando repetir o erro de `/programas/programas`.
- A migration `005_programas_tables.sql` usa `patient_id UUID` porque `patients.id` na migration `004_cuidado_tables.sql` ja foi estabilizado como `UUID`, nao `BIGINT`.
- O relatorio de overdue usa `encounters.opened_at` e, para pacientes sem consulta, calcula `days_without_visit` a partir de `program_enrollments.enrolled_at`. Isso preserva o requisito de listar pacientes sem visita mesmo quando `last_encounter_date` e `NULL`.
- O controle de acesso com multiplas roles foi implementado no proprio router (`CLINICO` ou `TENANT_GESTOR`) porque o helper atual `require_role()` do core aceita apenas uma role por vez.

## Desvios da spec

- A spec referencia imports antigos (`intellicare_core.context`, `intellicare_core.base_module`, `get_tenant_session`, `get_tenant_context`). Todos foram adaptados para os contratos reais do repo.
- A spec previa `patient_id BIGINT`; o repositorio atual exige `UUID` por compatibilidade com o DEM-013 ja mergeado.
- A spec mencionava registro no `module_loader` por API de `register()`, mas o repositorio atual usa o dicionario `AVAILABLE_MODULES` e `loader.load(...)`.

## Validacoes executadas

- `python -m pytest tests/programas -v` -> `6 passed`
- `GET /programas/health` via `TestClient` -> `200`
- Aplicacao da migration em `tenant_dev`:
  - `db/tenant_migrations/004_cuidado_tables.sql`
  - `db/tenant_migrations/005_programas_tables.sql`
- Confirmacao em PostgreSQL:
  - `tenant_dev.health_programs` existe
  - `tenant_dev.program_enrollments` existe

## Observacoes de ambiente

- A validacao SQL mostrou que o banco local ainda nao tinha a migration `004_cuidado_tables.sql` aplicada em `tenant_dev`, apesar do arquivo ja estar no `main`. Para validar a DEM-014 de ponta a ponta, foi necessario aplicar `004` e `005` em sequencia no ambiente local.
