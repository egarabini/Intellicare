# W9-B — $find + $book — Plano de Implementação

**Workstream:** W9-B
**Estimativa:** 14 dias
**Responsável:** DEV1

---

## Ordem de Execução

| # | Task | Dias | Depende |
|---|------|------|---------|
| 1 | Modelos Schedule, Slot (se não existir) | 2 | — |
| 2 | Migrations para Schedule, Slot | 1 | 1 |
| 3 | ScheduleFindOperation | 3 | 1, 2 |
| 4 | Lógica de geração de Slots a partir de Schedule | 2 | 3 |
| 5 | AppointmentBookOperation | 3 | 1, 2 |
| 6 | Transação atômica + lock | 1 | 5 |
| 7 | Registrar operações no router FHIR | 1 | 3, 5 |
| 8 | Testes | 1 | 7 |

---

## Passo a Passo

### Passo 1: Modelos
- Schedule: actor (ref), planningHorizon, serviceCategory
- Slot: schedule (ref), start, end, status

### Passo 2: Migrations
- Tabelas `schedule`, `slot` no schema FHIR
- Índices: schedule_id, start, end, status

### Passo 3: ScheduleFindOperation
- Parse Parameters
- Buscar Schedules por actor
- Para cada Schedule: gerar ou buscar Slots no período
- Retornar Bundle com Slots free

### Passo 4: Geração de Slots
- Se Schedule tem recurrence: gerar Slots dinamicamente
- Ou: Slots pré-cadastrados
- Filtrar por service-type se informado

### Passo 5: AppointmentBookOperation
- Parse Parameters
- Buscar Slot
- Validar status=free
- Criar Appointment
- Atualizar Slot para busy

### Passo 6: Transação
- Usar transação DB
- Lock otimista no Slot (version ou status check)
- Retry em caso de conflito

### Passo 7: Router
- Registrar `Schedule/$find` e `Appointment/$book`
- Documentar em CapabilityStatement

### Passo 8: Testes
- test_schedule_find
- test_appointment_book_success
- test_appointment_book_conflict

---

## Checklist de Entrega

- [ ] Schedule/$find retorna Slots
- [ ] Appointment/$book cria Appointment
- [ ] Conflito retorna OperationOutcome
- [ ] Transação atômica
- [ ] Testes passando
