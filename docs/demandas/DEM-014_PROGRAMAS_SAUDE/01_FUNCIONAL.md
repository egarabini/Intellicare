---
dem: DEM-014
titulo: Programas de Saúde
tipo: especificacao-funcional
status: concluido
modulo: programas
fase: 3
criado: 2026-03-13
---

# DEM-014 — Programas de Saúde

## 1. Contexto

Unidades de saúde gerenciam programas populacionais (hipertensão, diabetes, pré-natal, etc.).
A plataforma precisa de um módulo para criar programas, matricular pacientes e monitorar
cobertura e adesão.

---

## 2. Escopo

### Incluído

| Funcionalidade | Detalhe |
|---|---|
| CRUD de programas | Criar, listar, atualizar programas de saúde (`health_programs`) |
| Matrícula de pacientes | Vincular paciente a um programa (`program_enrollments`) |
| Relatório de cobertura | `enrolled_count / target_count × 100` |
| Relatório de overdue | Pacientes sem visita há mais de N dias |
| Controle de acesso | Roles CLINICO e TENANT_GESTOR |

### Fora do Escopo

- Dashboard gráfico de cobertura (demanda futura)
- Alertas automáticos para pacientes overdue
- Integração FHIR para programas

---

## 3. Requisitos Funcionais

| ID | Requisito |
|---|---|
| RF-01 | Criar programa de saúde com nome, descrição e meta de cobertura (`target_count`) |
| RF-02 | Listar programas do tenant |
| RF-03 | Matricular paciente em um programa |
| RF-04 | Listar matrículas de um programa |
| RF-05 | Calcular cobertura do programa (percentual matriculados vs meta) |
| RF-06 | Listar pacientes overdue: sem consulta há mais de N dias desde a matrícula |

---

## 4. Requisitos Não Funcionais

| ID | Requisito |
|---|---|
| RNF-01 | Multi-tenant via schema PostgreSQL (`tenant_{slug}`) |
| RNF-02 | Endpoints protegidos por JWT (roles CLINICO ou TENANT_GESTOR) |
| RNF-03 | `patient_id` como UUID (compatibilidade com DEM-013) |

---

## 5. Endpoints

| Método | Rota | Descrição |
|---|---|---|
| GET | `/programas/health` | Health check do módulo |
| POST | `/programas/programs` | Criar programa |
| GET | `/programas/programs` | Listar programas |
| POST | `/programas/programs/{id}/enroll` | Matricular paciente |
| GET | `/programas/programs/{id}/enrollments` | Listar matrículas |
| GET | `/programas/programs/{id}/coverage` | Relatório de cobertura |
| GET | `/programas/programs/{id}/overdue?days=N` | Pacientes overdue |

---

## 6. Modelo de Dados

### health_programs

| Coluna | Tipo |
|---|---|
| id | SERIAL PK |
| name | VARCHAR(200) NOT NULL |
| description | TEXT |
| target_count | INTEGER DEFAULT 0 |
| created_at | TIMESTAMPTZ DEFAULT now() |

### program_enrollments

| Coluna | Tipo |
|---|---|
| id | SERIAL PK |
| program_id | INTEGER FK → health_programs.id |
| patient_id | UUID FK → patients.id |
| enrolled_at | TIMESTAMPTZ DEFAULT now() |
| UNIQUE | (program_id, patient_id) |

---

## 7. Dependências

| DEM | Razão |
|---|---|
| DEM-003 | IntelliCare Core (contracts, db session, module_loader) |
| DEM-013 | Tabela `patients` (patient_id UUID) e `encounters` (para overdue) |
