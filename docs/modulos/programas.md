---
tipo: nota-modulo
modulo: programas
porto: TBD
fase: 3
sprint: "3.x"
status: pendente
dem_principal: DEM-014
tags: [fase-3, programas, saude-publica]
---

# Módulo: programas

**Responsabilidade:** Gestão de programas de saúde — criação, matrícula de pacientes, relatórios de cobertura e pacientes em atraso.

---

## Propósito

Permite ao `TENANT_GESTOR` criar programas de saúde (ex: Hipertensão, Diabetes, Pré-natal) com metas de cobertura. Clínicos e gestores matriculam pacientes, acompanham adesão e identificam pacientes sem visita recente. Integra com as tabelas de pacientes e consultas do módulo cuidado.

---

## Endpoints Principais

| Método | Rota | Descrição | Role |
|--------|------|-----------|------|
| GET | `/programas/` | Lista programas (filtro ativo/todos) | `CLINICO`, `TENANT_GESTOR` |
| POST | `/programas/` | Cria programa de saúde | `TENANT_GESTOR` |
| DELETE | `/programas/{id}` | Desativa programa (soft delete) | `TENANT_GESTOR` |
| POST | `/programas/{id}/enroll` | Matricula paciente no programa | `CLINICO`, `TENANT_GESTOR` |
| GET | `/programas/{id}/patients` | Lista pacientes matriculados | `CLINICO`, `TENANT_GESTOR` |
| DELETE | `/programas/{id}/patients/{pid}` | Alta do paciente do programa | `CLINICO`, `TENANT_GESTOR` |
| GET | `/programas/{id}/overdue` | Pacientes sem visita há N dias | `CLINICO`, `TENANT_GESTOR` |
| GET | `/programas/{id}/coverage` | Relatório de cobertura (%) | `TENANT_GESTOR` |

---

## Tabelas (schema `tenant_{slug}`)

| Tabela | Descrição |
|--------|-----------|
| `health_programs` | Programas (`name`, `description`, `target_count`, `active`, `created_by`) |
| `program_enrollments` | Matrículas (`program_id`, `patient_id`, `status`: active/discharged/suspended, `notes`) |

### Constraints

- `UNIQUE (program_id, patient_id)` — previne dupla matrícula
- `ON CONFLICT` com upsert — reativa paciente suspenso ao re-matricular
- FK para `patients` (módulo cuidado) e `health_programs`

---

## Relatórios

### Pacientes em atraso (`overdue`)

Pacientes matriculados sem consulta há mais de N dias (default 30). Cruza `program_enrollments` com `encounters` para calcular `days_without_visit`.

### Cobertura (`coverage`)

```
coverage_pct = enrolled_count / target_count × 100
```

Retorna também `overdue_count` para visibilidade do gestor.

---

## Roles Autorizados

- **`TENANT_GESTOR`** — todos os endpoints, incluindo criação/desativação e relatório de cobertura
- **`CLINICO`** — listagem, matrícula, alta, pacientes em atraso

---

## Stack e Dependências

- FastAPI (APIRouter com prefix `/programas`)
- SQLAlchemy async via `tenant_session(ctx)`
- Tabelas `patients` e `encounters` do módulo cuidado (DEM-013)
- [[decisoes/ADR-001-schema-autonomo]]
- intellicare-core (DEM-003)

---

## DEMs relacionadas

- **DEM-014**: Programas de Saúde (matrículas, cobertura, overdue)
- **DEM-013**: Cuidado backend (pacientes e consultas referenciados)

