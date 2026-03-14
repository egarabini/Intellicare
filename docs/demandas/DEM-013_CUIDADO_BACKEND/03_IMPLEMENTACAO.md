---
dem: DEM-013
titulo: Cuidado Backend — Implementação
tipo: IMPLEMENTACAO
status: concluído
criado: 2026-03-14
---

# DEM-013 · 03 — Implementação

## Arquivos Criados

| Arquivo | Papel |
|---------|-------|
| `db/tenant_migrations/004_cuidado_tables.sql` | DDL: `patients`, `encounters`, `encounter_notes` + 3 índices |
| `modules/cuidado/__init__.py` | Marcador de pacote |
| `modules/cuidado/schemas.py` | 7 Pydantic models (Patient, Encounter, Note, ClinicalAsk) |
| `modules/cuidado/service.py` | `CuidadoService` — CRUD pacientes, consultas SOAP |
| `modules/cuidado/router.py` | `APIRouter(/cuidado)` — 8 endpoints |
| `modules/cuidado/main.py` | `Module(BaseModule)` — contrato obrigatório |
| `tests/cuidado/test_cuidado.py` | 14 testes unitários — todos passando |

## Endpoints

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/cuidado/health` | Health check |
| POST | `/cuidado/patients` | Cadastrar paciente (201) |
| GET | `/cuidado/patients` | Buscar pacientes (full-text PT-BR) |
| GET | `/cuidado/patients/{pid}/history` | Timeline de consultas |
| POST | `/cuidado/encounters` | Abrir consulta (201) |
| POST | `/cuidado/encounters/{eid}/notes` | Adicionar evolução SOAP (201) |
| POST | `/cuidado/encounters/{eid}/close` | Encerrar consulta |
| POST | `/cuidado/encounters/{eid}/ask` | Pergunta clínica → SLM com RAG |

## Fluxo Clínico

```
Clínico autenticado (role CLINICO)
  → POST /patients → cadastra paciente no schema do tenant
  → POST /encounters → abre consulta vinculada ao paciente
  → POST /encounters/{id}/notes → registra evolução SOAP
  → POST /encounters/{id}/ask → consulta SLM com base de conhecimento
  → POST /encounters/{id}/close → encerra consulta (closed_at)
```

## Isolamento Multi-Tenant

- Todas as queries usam `tenant_session(ctx)` → schema `tenant_{slug}`
- Pacientes de tenant_a nunca visíveis para tenant_b
- Full-text search usa `to_tsvector('portuguese', ...)` no schema do tenant

## Integração SLM

- Endpoint `/encounters/{eid}/ask` delega para `SLMService.ask()`
- RAG busca chunks no pgvector do tenant → OLLAMA gera resposta PT-BR
- Erros de conexão/timeout → HTTP 503

## Testes

```
tests/cuidado/test_cuidado.py — 14 passed
  ✓ test_patient_create_minimal
  ✓ test_patient_create_full
  ✓ test_patient_create_sex_literal
  ✓ test_patient_create_invalid_sex
  ✓ test_patient_response
  ✓ test_encounter_create_defaults
  ✓ test_encounter_create_custom
  ✓ test_encounter_create_invalid_priority
  ✓ test_encounter_response
  ✓ test_note_create_defaults
  ✓ test_note_create_soap
  ✓ test_note_response
  ✓ test_clinical_ask_defaults
  ✓ test_clinical_ask_custom
```

## Dependências

- `intellicare-core` (DEM-003): `BaseModule`, `TenantContext`, `require_role`, `tenant_session`
- `modules/slm` (DEM-010): `SLMService` para suporte clínico inline
- PostgreSQL: schema por tenant com tabelas clínicas

