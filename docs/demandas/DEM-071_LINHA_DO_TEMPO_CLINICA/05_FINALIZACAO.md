---
tipo: finalizacao
demanda: DEM-071
titulo: Linha do Tempo Clínica
status: concluida
commit: ef40df8
dev: DEV-2
data-entrega: 2026-03-22
---

# DEM-071 — Finalização

## Commit

```
ef40df8  feat(cuidado): clinical timeline — unified patient history (encounters, notes, prescriptions, care tasks)
```

**7 arquivos | 718 inserções**

---

## O que foi entregue

| Camada | Arquivo | O que foi construído |
|--------|---------|---------------------|
| API | `router.py` | `GET /cuidado/patients/{pid}/clinical-timeline?limit&offset` |
| Service | `service.py` | `clinical_timeline()` — 4 fontes, tenant session, merge + sort por `occurred_at DESC`, paginado |
| Schemas | `schemas.py` | `TimelineEvent` (encounter/clinical_note/prescription/care_task), `ClinicalTimelineResponse` |
| Componente | `ClinicalTimeline.tsx` | Mantine Timeline com filtro por tipo, agrupamento por data, badges de status, tags CID, paginação |
| Página | `PatientProfile.tsx` | Aba "Linha do Tempo" como aba padrão (primeira aba) |
| Hook | `usePatients.ts` | `useClinicalTimeline()` react-query hook |
| Testes | `test_clinical_timeline.py` | **9 testes — todos passando** |

---

## Fontes unificadas na timeline

| Fonte | Tabela | Campo de data | Detalhe |
|-------|--------|--------------|---------|
| Consultas | `cuidado.encounters` | `opened_at` | chief_complaint, CID, status |
| Notas Florence | `florence.clinical_notes` | `created_at` | SOAP/free text, autor |
| Prescrições | `oswaldo.prescriptions` | `created_at` | medicamentos, CID, status |
| Tarefas CarePlanner | `careplanner.journey_tasks` | `created_at` | canal, tipo, status |

---

## Destaques de implementação

**Aba padrão no PatientProfile:** "Linha do Tempo" é agora a primeira aba, substituindo a aba anterior como default. Decisão acertada — o médico tem visão longitudinal imediata ao abrir o perfil do paciente.

**Graceful fallback para care_tasks:** Se a tabela `careplanner.journey_tasks` não existir (ambientes sem CarePlanner configurado), o service absorve o erro e retorna a timeline sem esse tipo. Sem crash, sem 500.

**Isolamento tenant:** Todas as 4 queries passam por `tenant_session(ctx)` — sem risco de cross-tenant data leak.

---

## Cobertura de testes

```
test_timeline_returns_all_types          PASSED
test_timeline_filter_by_type_encounter   PASSED
test_timeline_filter_by_type_note        PASSED
test_timeline_filter_by_type_prescription PASSED
test_timeline_pagination_limit           PASSED
test_timeline_pagination_offset          PASSED
test_timeline_empty_patient              PASSED
test_timeline_sort_desc                  PASSED
test_timeline_graceful_fallback_care_tasks PASSED
```

---

## Observação para DEM-074

O smoke de staging para DEM-071 usa um `patient_id` real do ambiente. DEV-2 deve fornecer um ID de referência (ou o smoke script do `03_PLANO.md` de DEM-074 deverá consultar `GET /cuidado/patients` primeiro para obter um ID válido).
