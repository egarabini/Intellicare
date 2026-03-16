# DEM-029 — 05_FINALIZACAO

## Entrega

Integração de agendamento entre ClinicoUI e PacienteUI concluída sobre o backend
existente.

## Resultado

- Portal do paciente agora resolve corretamente o paciente logado mesmo em
  tenants com schema legado do gestor.
- Portal do paciente passou a exibir o nome do clínico responsável pelo
  agendamento quando disponível.
- Confirmação e cancelamento de consulta retornam erro HTTP coerente (`404`)
  quando o agendamento não existe ou não pertence ao paciente.
- Agenda clínica passou a refletir melhor o estado compartilhado dos
  agendamentos, incluindo confirmações e cancelamentos feitos no portal.
- As duas UIs foram configuradas para atualização periódica, reduzindo defasagem
  visual entre clínico e paciente.

## Arquivos principais alterados

- `modules/cuidado/service.py`
- `modules/cuidado/router.py`
- `frontend/ClinicoUI/src/hooks/useMyAgenda.ts`
- `frontend/ClinicoUI/src/pages/Agenda.tsx`
- `frontend/PacienteUI/src/hooks/usePaciente.ts`
- `frontend/PacienteUI/src/pages/AgendaPage.tsx`
- `frontend/PacienteUI/src/pages/PainelPage.tsx`
- `packages/intellicare-core/tests/test_cuidado_portal.py`

## Validação

- Backend: `3 passed` em `tests/test_cuidado_portal.py`
- Frontend: build do ClinicoUI concluído
- Frontend: build do PacienteUI concluído

## Pendência documental

Os documentos `01_FUNCIONAL.md` e `02_TECNICA.md` da DEM-029 ainda precisam ser
criados para alinhar a demanda ao workflow padrão do repositório.
