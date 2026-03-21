# DEM-059 — Portal Paciente Notas — Finalização

## Status: ✅ CONCLUÍDA

- **Commit:** `d714194` (`d714194ff345ccfbc3e04aee3f00cf56b673be58`)
- **Mensagem:** `feat(portal): jornadas e notas clinicas com privacidade explicita`
- **Entregador:** CODEX
- **Data:** 2026-04-04

---

## Adaptação arquitetural

O briefing assumia um módulo `portal` separado. A estrutura real do projeto usa o
módulo `cuidado` com rotas do paciente. CODEX adaptou corretamente ao código vivo:

| Briefing | Implementado |
|---|---|
| `GET /portal/me/journeys` | `GET /cuidado/paciente/me/journeys` |
| `GET /portal/me/clinical-notes` | `GET /cuidado/paciente/me/clinical-notes` |
| `modules/portal/` | `modules/cuidado/router.py` + `schemas.py` + `service.py` |

## O que foi entregue

| Artefato | Descrição |
|---|---|
| `modules/cuidado/router.py` | 2 novos endpoints filtrados por paciente autenticado |
| `modules/cuidado/schemas.py` | `PatientJourney` + `PatientNote` (sem `soap_a`) |
| `modules/cuidado/service.py` | Leitura com resumo SOAP controlado (só `soap_s` + `soap_p`) |
| `PacienteUI/pages/JornadasPage.tsx` | Lista paginada de jornadas com badges canal/status |
| `PacienteUI/pages/HistoricoPage.tsx` | Timeline de notas clínicas com resumo sem avaliação |
| `PacienteUI/hooks/usePaciente.ts` | Hooks de chamada dos dois endpoints |
| `PacienteUI/App.tsx` | Rotas e links de navegação adicionados |
| `tests/test_portal_notas.py` | 6 testes passando |

## Privacidade confirmada

- `soap_a` (Avaliação diagnóstica) não exposto no endpoint do paciente ✅
- Resumo SOAP exibe apenas `soap_s` (Queixa) e `soap_p` (Orientações) ✅
- Endpoints exigem role `PACIENTE` — gestor/clínico recebe 403 ✅

---

## Critérios de aceite — verificação final

- [x] `GET /cuidado/paciente/me/journeys` retorna jornadas do paciente autenticado
- [x] `GET /cuidado/paciente/me/clinical-notes` retorna resumo sem `soap_a`
- [x] `JornadasPage` com badges de canal e status no PacienteUI
- [x] `HistoricoPage` com timeline de consultas
- [x] Links de navegação no portal
- [x] 6 testes passando (empty, privacidade soap_a, role guard + variações)
