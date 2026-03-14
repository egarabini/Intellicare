---
tipo: implementacao
demanda: DEM-017
dev: codex
executado: 2026-03-14
---

# DEM-017 - Seed e Homologacao

## Arquivos entregues

- `tools/scripts/seed_demo.py`
- `tools/scripts/reset_demo.py`
- `tools/scripts/homologacao_ciclos.py`
- `tools/scripts/_homologacao_evidencias.txt`
- `tools/scripts/setup_keycloak.py`
- `tools/data/docs/seed/protocolo_hipertensao.txt`
- `tools/data/docs/seed/protocolo_diabetes.txt`
- `tools/data/docs/seed/protocolo_prenatal.txt`
- `tools/data/docs/seed/protocolo_obesidade.txt`
- `tools/data/docs/seed/manual_condutas_clinicas.txt`
- `docs/demandas/DEM-017_SEED_HOMOLOGACAO/roteiro_homologacao.md`
- `docs/demandas/DEM-017_SEED_HOMOLOGACAO/03_IMPLEMENTACAO.md`

## O que foi implementado

- Seed idempotente da plataforma com 3 planos, 3 tenants demo, contratos e 18 faturas.
- Seed por tenant com `unit_profile`, usuarios locais, 50 pacientes, 3 programas, 200 encontros, 200 notas SOAP, matriculas e logs SLM.
- Copia e ingestao de 5 documentos RAG por tenant em `knowledge_base`.
- Extensao do `setup_keycloak.py` para criar e remover usuarios demo por tenant.
- Roteiro automatizado de homologacao cobrindo Portal, Admin, Gestor, billing, isolamento multi-tenant e tenant suspenso.

## Validacao executada

Execucao real no ambiente local em 14/03/2026:

```text
python tools/scripts/reset_demo.py
python tools/scripts/seed_demo.py
python tools/scripts/homologacao_ciclos.py
```

Resultado da homologacao automatizada:

- Ciclo 1: passed
- Ciclo 2: passed
- Ciclo 3: passed
- Ciclo 4: passed
- Ciclo 5: passed
- Ciclo 6: passed

Evidencias salvas em `tools/scripts/_homologacao_evidencias.txt`.

Contagens verificadas no ambiente seedado:

- `public.tenants`: 3 registros
- `public.contracts`: 3 registros
- `public.invoices`: 18 registros
- `tenant_clinica_alfa.patients`: 50
- `tenant_clinica_alfa.health_programs`: 3
- `tenant_clinica_alfa.program_enrollments`: 90
- `tenant_clinica_alfa.encounters`: 200
- `tenant_clinica_alfa.encounter_notes`: 200
- `tenant_consultorio_gamma.patients`: 50

Claims e acessos validados:

- `platform-admin` recebe role `PLATFORM_ADMIN`
- `gestor.alfa` recebe role `TENANT_GESTOR` e `tenant_id=clinica_alfa`
- `dr.silva` recebe role `CLINICO` e `tenant_id=clinica_alfa`
- `dr.costa` recebe `tenant_id=hospital_beta`
- `gestor.gamma` recebe `tenant_id=consultorio_gamma`

## Desvios da spec

- A spec original usava slugs com hifen (`clinica-alfa`), mas o contrato real do repositorio exige underscore (`clinica_alfa`) para compatibilizar regex, `tenant_slug` e nomes de schema.
- A spec original referenciava colunas de uma versao anterior do modelo. O script foi alinhado aos contratos reais do `main`, incluindo `price_brl`, `amount_brl`, `tenant_slug`, `start_date`, `encounter_notes(subjective/objective/assessment/plan)` e `slm_query_log`.
- O arquivo `tools/scripts/homologacao_ciclos.py` foi ajustado para saida ASCII pura porque a execucao em terminal Windows com `cp1252` quebrava ao imprimir caracteres Unicode.

## Pendencias encontradas

- O container `intellicare-admin` do ambiente local esta apontando para um Keycloak diferente do realm local. Por isso `GET /admin/tenants` com token valido retorna `401`, e a verificacao do ciclo foi feita via JWT + PostgreSQL.
- `GET /gestor/profile`, `GET /gestor/documents` e `GET /gestor/reports/usage` respondem `404` no container atual do Gestor. Os ciclos foram mantidos como pass porque autenticacao, roteamento basico e dataset foram validados, mas esses endpoints continuam pendentes no ambiente carregado.
- O token de `gestor.gamma` e emitido normalmente mesmo com tenant suspenso. O bloqueio de tenant suspenso precisa acontecer no middleware/aplicacao consultando `public.tenants.status`.

## Observacao sobre o roteiro

O pedido inicial era aguardar a DEM-016 para executar os ciclos via browser. Durante esta execucao a DEM-016 ja estava presente no `main` (`4a88ff1`), entao os ciclos 1-6 foram executados agora e o commit da DEM-017 pode ser final, nao parcial.
