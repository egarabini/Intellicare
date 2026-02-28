# W9-B — $find + $book (Agendamento) — Especificação Funcional

**Workstream:** W9-B
**Responsável:** DEV1
**Módulo:** `intellicare-grahame` (FHIR operations)
**Status:** 📋 Especificação
**Data:** 2026-02-24

---

## 1. Objetivo

Implementar operações FHIR de agendamento conforme Medplum v5.0.12+:
- **`Schedule/$find`** — buscar slots disponíveis em um período
- **`Appointment/$book`** — reservar um slot e criar Appointment

---

## 2. Contexto de Negócio

### Problema Atual
Sistemas de agendamento precisam de integração customizada. Sem operações FHIR padronizadas, cada integrador implementa sua própria lógica.

### Solução Proposta
Operações FHIR padrão que permitem:
- Portal/App buscar slots disponíveis
- Paciente ou sistema reservar slot
- Integração com qualquer sistema FHIR

### Benefícios
- **Reservas online** — paciente agenda via portal
- **Interoperabilidade** — sistemas externos usam FHIR
- **Padrão** — alinhado a Medplum e FHIR R4

---

## 3. Requisitos Funcionais

### RF-001 — Schedule/$find
- **Endpoint:** `POST /fhir/Schedule/$find`
- **Input:** Parameters com `actor`, `start`, `end`, `service-type`
- **Output:** Lista de Slot disponíveis
- **Regras:** Filtrar por actor (Practitioner/HealthcareService), período, tipo de serviço

### RF-002 — Appointment/$book
- **Endpoint:** `POST /fhir/Appointment/$book`
- **Input:** Parameters com `slot`, `patient`, `practitioner?`, `comment?`
- **Output:** Appointment criado
- **Regras:** Validar slot disponível; criar Appointment; marcar Slot como busy

### RF-003 — Validação de Conflitos
- Antes de $book: verificar se Slot ainda está livre
- Se ocupado: retornar OperationOutcome com conflito
- Transação atômica (Slot + Appointment)

### RF-004 — Recursos FHIR
- **Schedule:** Define horários de um Practitioner/HealthcareService
- **Slot:** Intervalos de tempo disponíveis
- **Appointment:** Reserva confirmada

### RF-005 — Filtros
- $find: filtrar por `actor`, `start`, `end`, `service-type`, `status`

---

## 4. Requisitos Não-Funcionais

### RNF-001 — Performance
- $find: < 500ms para 7 dias de slots
- $book: < 200ms

### RNF-002 — Concorrência
- Lock otimista em Slot para evitar double-booking
- Retry em caso de conflito

---

## 5. Cenários de Teste

| # | Cenário | Entrada | Saída |
|---|---------|---------|-------|
| 1 | $find slots | actor, start, end | Lista de Slot |
| 2 | $book sucesso | slot, patient | Appointment criado |
| 3 | $book conflito | slot já ocupado | OperationOutcome error |
| 4 | $find sem resultados | período sem slots | Lista vazia |

---

## 6. Referências

- FHIR Schedule: https://www.hl7.org/fhir/schedule.html
- FHIR Slot: https://www.hl7.org/fhir/slot.html
- FHIR Appointment: https://www.hl7.org/fhir/appointment.html
- Medplum $find/$book: v5.0.12+
