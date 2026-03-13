---
dem: DEM-013
titulo: Cuidado Backend — Prontuário e Consultas Clínicas
tipo: FUNCIONAL
status: aprovado
criado: 2026-03-13
dependencias: [DEM-003, DEM-010, DEM-011]
---

# DEM-013 · 01 — Especificação Funcional

## Contexto

Módulo clínico central: consultas, evoluções SOAP e suporte SLM inline.
Dados de pacientes isolados no schema do tenant — nunca expostos a outros tenants.

## Escopo Incluído

- **Pacientes**: cadastro, busca por nome (full-text), perfil demográfico
- **Consultas**: abertura, evolução SOAP, encerramento
- **Suporte SLM**: endpoint de consulta à base de conhecimento no contexto da consulta
- **Histórico clínico**: timeline de consultas e evoluções do paciente

## Excluído

- Prescrições, exames → pós-V3
- Interface web → DEM-015

## Modelo de Dados (schema tenant_{slug})

```sql
CREATE TABLE patients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name TEXT NOT NULL,
    cpf TEXT UNIQUE,
    birth_date DATE,
    sex CHAR(1) CHECK (sex IN ('M','F','O')),
    phone TEXT, email TEXT, address TEXT,
    active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE encounters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patients(id),
    clinician_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open','closed')),
    chief_complaint TEXT,
    priority TEXT NOT NULL DEFAULT 'normal'
              CHECK (priority IN ('emergency','urgent','normal','low')),
    opened_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    closed_at TIMESTAMPTZ
);

CREATE TABLE encounter_notes (
    id BIGSERIAL PRIMARY KEY,
    encounter_id UUID NOT NULL REFERENCES encounters(id),
    clinician_id TEXT NOT NULL,
    subjective TEXT, objective TEXT, assessment TEXT, plan TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

## Endpoints

| Método | Rota | Acesso |
|---|---|---|
| GET/POST | `/cuidado/patients` | CLINICO |
| GET | `/cuidado/patients/{id}/history` | CLINICO |
| POST | `/cuidado/encounters` | CLINICO |
| POST | `/cuidado/encounters/{id}/notes` | CLINICO |
| POST | `/cuidado/encounters/{id}/close` | CLINICO |
| POST | `/cuidado/encounters/{id}/ask` | CLINICO (→ SLM) |
| GET | `/cuidado/health` | any |

## Critérios de Aceite

| # | Critério |
|---|---|
| AC-1 | POST `/cuidado/patients` → criado no schema do tenant |
| AC-2 | Isolamento: tenant_a não vê pacientes de tenant_b |
| AC-3 | POST `/cuidado/encounters/{id}/notes` → evolução SOAP registrada |
| AC-4 | POST `/cuidado/encounters/{id}/ask` → resposta SLM com fontes |
| AC-5 | PACIENTE em `/cuidado/patients` (POST) → 403 |
| AC-6 | Fechar consulta → `closed_at` registrado, novas evoluções bloqueadas |
