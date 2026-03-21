# DEM-054 — CarePlanner × Agendamento — Finalização

## Status: ✅ CONCLUÍDA

- **Commit:** `945f08a`
- **Entregador:** DEV-1
- **Data:** 2026-03-21
- **Volume:** 10 arquivos, +366 linhas

---

## O que foi entregue

| Camada | Mudança |
|---|---|
| **Migration** | `appointment_id` UUID + índice parcial em `care_tasks` |
| **Repository** | `get_task_by_appointment()`, `link_task_to_appointment()` |
| **Service / Routes** | `appointment_id` em `open_task` / `trigger_journey` + `GET /appointments/{id}/journey` |
| **TriggerJourneyModal** | Campo opcional de ID do agendamento |
| **JourneyDetail** | Alert com link para o agendamento vinculado |
| **AppointmentCalendar** | Coluna "Jornada" com badge linkando à jornada ativa |

## Testes

- **5 testes Phase K** (novos) — link, get, not found, e variações de estado
- **10 testes Phase B** (regressão) — todos passando

---

## Critérios de aceite — verificação final

- [x] Migration 012 aplicada sem erro
- [x] `open_task` aceita `appointment_id` opcional e persiste no banco
- [x] `GET /appointments/{id}/journey` retorna 200 ou 404 correto
- [x] `TriggerJourneyModal` com campo opcional de agendamento
- [x] `CareplannerJourneyDetail` exibe link para agendamento quando vinculado
- [x] `AppointmentCalendar` exibe badge de jornada ativa
- [x] 5 testes Phase K passando + 10 regressão Phase B passando
