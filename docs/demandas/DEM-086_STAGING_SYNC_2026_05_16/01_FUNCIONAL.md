---
tipo: funcional
demanda: DEM-086
titulo: Staging Sync 2026-05-16
status: planejada
dev: DEV-1
sprint: 2026-05-16
criado: 2026-03-23
---

# DEM-086 — Funcional: Staging Sync 2026-05-16

## Objetivo

Sincronizar o ambiente de staging com todas as entregas da sprint 2026-05-16: identity foundation, integração de pacientes com identidade centralizada e correções de saneamento.

---

## O que será validado

| Entrega | Smoke |
|---------|-------|
| Migration 021 — `platform.pessoa*` | Schema criado, tabelas presentes |
| Identity service | `GET /identity/pessoas/cpf/{cpf}` → 404 em CPF novo |
| `POST /identity/pessoas` | find-or-create idempotente |
| Migration 022 — `paciente.pessoa_id` | Coluna UUID presente, nullable |
| `POST /cuidado/patients` com CPF | `pessoa_id` preenchido no retorno |
| Mesmo CPF em dois tenants | mesmo `pessoa_id` |
| `platform.pessoa_estabelecimento` | Registro criado ao vincular paciente |
| Redis auth CarePlanner | Sem erros de auth no log |
| `clinical_notes.encounter_id` | Tipo UUID confirmado |
| Suite completa | Zero falhas |

---

## Critérios de aceite

- [ ] Migration 021 aplicada no platform schema sem erro
- [ ] Migration 022 aplicada em todos os tenant schemas ativos
- [ ] Identity service respondendo em `/identity/pessoas`
- [ ] Paciente criado via API tem `pessoa_id` não-null quando CPF fornecido
- [ ] Pacientes legados (sem `pessoa_id`) continuam funcionando
- [ ] CarePlanner dispatcher sem erro Redis por 60s
- [ ] Suite pytest completa: zero falhas
