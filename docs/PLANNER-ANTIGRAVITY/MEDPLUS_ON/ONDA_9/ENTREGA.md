# ONDA_9 — Entrega

**Data:** 2026-02-19
**Status:** Implementado

---

## Resumo

A ONDA_9 (UX e Flexibilidade) foi implementada no módulo `intellicare-grahame`:

| Workstream | Status | Arquivos |
|------------|--------|----------|
| W9-A AI Operation + SSE | OK | ai_operation_service.py, ai_routes.py |
| W9-B $find + $book | OK | schedule_find.py, appointment_book.py |
| W9-C On-behalf-of | OK | on_behalf_of.py (middleware) |

---

## Endpoints

- `POST /api/v1/ai` — Operação AI (JSON ou SSE)
- `POST /api/v1/fhir/$ai` — Operação FHIR $ai
- `POST /api/v1/fhir/Schedule/$find` — Busca slots disponíveis
- `POST /api/v1/fhir/Appointment/$book` — Reserva slot e cria Appointment

---

## Config

| Variável | Default |
|----------|---------|
| INTELLICARE_WANDA_URL | http://localhost:8002 |
| INTELLICARE_FLORENCE_URL | http://localhost:8002 |
| INTELLICARE_GERALDA_URL | http://localhost:8006 |
| INTELLICARE_AI_OPERATION_TIMEOUT | 120 |
| INTELLICARE_ON_BEHALF_OF_ENABLED | true |

---

## Próximos Passos

- Testes de integração com Wanda/Florence/Geralda
- Rate limit na operação AI
- Auditoria de operações AI
