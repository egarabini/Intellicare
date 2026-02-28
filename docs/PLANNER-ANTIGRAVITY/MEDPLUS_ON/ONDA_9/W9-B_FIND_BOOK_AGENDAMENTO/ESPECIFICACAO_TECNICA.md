# W9-B — $find + $book — Especificação Técnica

**Workstream:** W9-B
**Módulo:** `intellicare-grahame`
**Data:** 2026-02-24

---

## 1. Arquitetura

```
Cliente
    │
    │ POST /fhir/Schedule/$find
    │ Body: Parameters { actor, start, end }
    ▼
┌─────────────────────────────────────────────────┐
│  Grahame FHIR Router                            │
│  - Roteia $find para ScheduleFindOperation      │
└─────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────┐
│  ScheduleFindOperation                          │
│  - Busca Schedule por actor                     │
│  - Gera ou consulta Slots no período            │
│  - Filtra por status=free                        │
│  - Retorna Bundle com Slots                     │
└─────────────────────────────────────────────────┘

Cliente
    │
    │ POST /fhir/Appointment/$book
    │ Body: Parameters { slot, patient }
    ▼
┌─────────────────────────────────────────────────┐
│  AppointmentBookOperation                       │
│  - Valida Slot existe e status=free             │
│  - Cria Appointment                              │
│  - Atualiza Slot status=busy                    │
│  - Transação atômica                            │
└─────────────────────────────────────────────────┘
```

---

## 2. Contratos

### Schedule/$find — Request

```json
{
  "resourceType": "Parameters",
  "parameter": [
    { "name": "actor", "valueReference": { "reference": "Practitioner/123" } },
    { "name": "start", "valueDateTime": "2026-03-01T08:00:00Z" },
    { "name": "end", "valueDateTime": "2026-03-07T18:00:00Z" }
  ]
}
```

### Schedule/$find — Response

```json
{
  "resourceType": "Bundle",
  "type": "searchset",
  "entry": [
    { "resource": { "resourceType": "Slot", "status": "free", ... } }
  ]
}
```

### Appointment/$book — Request

```json
{
  "resourceType": "Parameters",
  "parameter": [
    { "name": "slot", "valueReference": { "reference": "Slot/456" } },
    { "name": "patient", "valueReference": { "reference": "Patient/789" } }
  ]
}
```

---

## 3. Estrutura de Código

```
intellicare-grahame/
├── grahame/
│   ├── fhir/
│   │   └── operations/
│   │       ├── schedule_find.py    # NOVO
│   │       └── appointment_book.py # NOVO
│   └── models/
│       └── schedule_slot.py        # Modelos Schedule, Slot (se não existir)
```

---

## 4. Modelo de Dados

- **Schedule:** Referência a Practitioner/HealthcareService, recurrence
- **Slot:** Referência a Schedule, start, end, status (free|busy|unavailable)
- **Appointment:** Referência a Slot, Patient, Participant

---

## 5. Transação $book

```python
async def book_appointment(slot_id, patient_id):
    async with db.begin():
        slot = await get_slot(slot_id)
        if slot.status != "free":
            raise ConflictError("Slot ocupado")
        appointment = create_appointment(slot, patient_id)
        slot.status = "busy"
        await save(appointment)
        await save(slot)
```
