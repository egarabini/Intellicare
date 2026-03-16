# DEM-029 — 04_DIARIO

## 2026-03-16

- Localizadas apenas referências da DEM-029 em `docs/demandas/_dashboard.md`.
- Confirmado que a spec formal ainda não foi criada.
- Mapeados os endpoints existentes:
  - `GET /cuidado/my-agenda`
  - `GET /cuidado/paciente/appointments`
  - `PATCH /cuidado/paciente/appointments/{id}/confirm`
  - `DELETE /cuidado/paciente/appointments/{id}`
- Identificado bloqueio real da integração:
  - `CuidadoService` dependia de `patients.user_id` e `patients.full_name`
  - schemas ativos do gestor expõem `patients.name` e podem não ter `user_id`
- Implementada compatibilidade dinâmica de schema em `modules/cuidado/service.py`.
- Adicionado fallback por e-mail para vínculo do paciente sem quebrar schemas
  que não possuem `user_id`.
- Adicionado enriquecimento do nome do clínico via `tenant_users.keycloak_id`.
- Corrigido tratamento de erro no router do paciente para retornar `404` em vez
  de erro interno ao confirmar/cancelar agendamento inexistente.
- ClinicoUI:
  - auto refresh da agenda
  - correção de data local para evitar deslocamento por `toISOString()`
  - filtros por tipo e status
  - cards-resumo de confirmados/cancelados/em atendimento
- PacienteUI:
  - tipagem dos hooks
  - auto refresh
  - nome do profissional no painel e na agenda
  - invalidação do painel após confirmar/cancelar
  - feedback de erro nas ações
- Teste de integração criado em
  `packages/intellicare-core/tests/test_cuidado_portal.py`.
- Validações executadas:
  - `PYTHONPATH=c:\Users\egara\INTELLICARE pytest tests\test_cuidado_portal.py -q`
  - `npm run build` em `frontend/ClinicoUI`
  - `npm run build` em `frontend/PacienteUI`
