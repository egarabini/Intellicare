# STEP-001: Criar Projeto e Migrar Engine

## Status: 🟢 Concluido

## Objetivo
Criar a estrutura do projeto e migrar o engine do monolito.

## Pre-requisitos
- intellicare-core v1.0.0 instalavel localmente ✅

## Tarefas
- [x] Criar pyproject.toml com dependencia de intellicare-core
- [x] Migrar `engine/` inteiro do monolito (core_logic, staging, alerts, models)
- [x] Migrar `profiles/` inteiro (models, registry, loader, schema, YAMLs)
- [x] Migrar `datastore/` (FHIRDataStore)
- [x] Adaptar imports para usar intellicare-core (BaseModuleConfig, HealthCheck, ModuleInfo)
- [x] Criar API REST (FastAPI) com 6 endpoints
- [x] Criar Dockerfile (multi-stage: api + ui) e docker-compose.yml
- [x] Validar que `pip install -e .` funciona
- [x] Rodar testes — **98 testes, 79% cobertura**

## Adaptacoes feitas na migracao
- `from engine.xxx` → `from oswaldo.engine.xxx` (todos os imports)
- `OswaldoConfig` agora extends `BaseModuleConfig` (pydantic-settings) em vez de dataclass
- `PatientSummary` renomeado para `OswaldoPatientSummary` (evita conflito com intellicare-core)
- `trend_direction` ajustado de "higher"/"lower" para "higher_is_better"/"lower_is_better" (match YAML)
- API endpoints seguem contrato `/api/v1/health` e `/api/v1/info` do intellicare-core

## Entregavel
Engine funcional como pacote Python — staging, alerts e trends funcionando em testes unitarios.
API REST pronta com 6 endpoints. Docker pronto para deploy.

## Metricas
- 98 testes passando
- 79% cobertura de codigo
- 3 doencas: CKD (KDIGO), DM2 (ADA), HAS (ESC/ESH)
- 3+1 estrategias de estadiamento
- 2 tipos de alerta (threshold, trend)
- 11 arquivos de teste
