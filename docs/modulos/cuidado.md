---
tipo: nota-modulo
modulo: cuidado
porto: 8004
fase: 3
sprint: "3.3"
status: pendente
dem_principal: DEM-013
tags: [fase-3, cuidado, rag, slm, pgvector]
---

# Módulo: cuidado

**Responsabilidade:** Módulo clínico central — cadastro de pacientes, consultas com evolução SOAP, suporte SLM inline via RAG.

---

## Propósito

Módulo do `CLINICO`. Gerencia o fluxo clínico: cadastro de pacientes, abertura/encerramento de consultas, registro de evoluções no formato SOAP (Subjective, Objective, Assessment, Plan), e consulta à base de conhecimento via SLM durante o atendimento. Dados de pacientes são isolados no schema do tenant.

---

## Endpoints Principais

| Método | Rota | Descrição | Role |
|--------|------|-----------|------|
| GET | `/cuidado/health` | Health check | any |
| POST | `/cuidado/patients` | Cadastrar paciente | `CLINICO` |
| GET | `/cuidado/patients` | Busca por nome (full-text search) | `CLINICO` |
| GET | `/cuidado/patients/{pid}/history` | Timeline de consultas do paciente | `CLINICO` |
| POST | `/cuidado/encounters` | Abrir consulta (com prioridade) | `CLINICO` |
| POST | `/cuidado/encounters/{eid}/notes` | Adicionar evolução SOAP | `CLINICO` |
| POST | `/cuidado/encounters/{eid}/close` | Encerrar consulta | `CLINICO` |
| POST | `/cuidado/encounters/{eid}/ask` | Pergunta clínica → resposta SLM com fontes | `CLINICO` |

---

## Tabelas (schema `tenant_{slug}`)

| Tabela | Descrição |
|--------|-----------|
| `patients` | Cadastro (`full_name`, `cpf` UNIQUE, `birth_date`, `sex`, `phone`, `email`, `address`) |
| `encounters` | Consultas (`patient_id`, `clinician_id`, `status`: open/closed, `priority`: emergency/urgent/normal/low) |
| `encounter_notes` | Evoluções SOAP (`subjective`, `objective`, `assessment`, `plan`) |

### Índices relevantes

- `idx_encounters_patient` — busca por paciente + data
- `idx_notes_encounter` — notas por consulta
- `idx_patients_name` — full-text search GIN em `full_name` (dicionário `portuguese`)

---

## Fluxo de Consulta com SLM

```
Clínico faz pergunta no contexto da consulta
    ↓
RAG: top-k chunks relevantes da knowledge_base (pgvector)
    ↓
SLM (OLLAMA): gera resposta em PT-BR com contexto
    ↓
Resposta fundamentada com source_path rastreável
```

---

## Roles Autorizados

- **`CLINICO`** — acesso a todos os endpoints
- `PACIENTE` → 403 em qualquer endpoint

---

## Stack e Dependências

- FastAPI (APIRouter com prefix `/cuidado`)
- SQLAlchemy async via `tenant_session(ctx)`
- `SLMService` do módulo slm (para endpoint `/ask`)
- Full-text search PostgreSQL (`to_tsvector`, `plainto_tsquery`, dicionário `portuguese`)
- [[decisoes/ADR-003-rag-slm-pgvector]]
- pgvector + OLLAMA (DEM-009, DEM-010)
- intellicare-core/vector/ helpers (DEM-003)

---

## DEMs relacionadas

- **DEM-013**: Cuidado backend (pacientes, consultas SOAP, suporte SLM)
- **DEM-014**: Programas de saúde (matrículas, cobertura)
- **DEM-015**: Frontend clínico MVP
