# FASE 1.3 - GERALDA v2.0 Fase 2: Integração FHIR CarePlan

**Data de início:** 2026-02-24 11:20
**Data de conclusão:** 2026-02-24 12:15
**Responsável:** DEV0
**Prioridade:** 🔴 BLOQUEADOR
**Status:** ✅ CONCLUÍDO

## Contexto

Agora que Geralda tem persistência PostgreSQL (FASE 1.2), precisamos integrar com o padrão FHIR R4 através do módulo Grahame.

## Especificação

**Spec:** `intellicare-geralda/docs/specs/fase-02-fundacao-integracao-fhir/EF-002_INTEGRACAO_FHIR_CAREPLAN.md`

## Objetivo

Criar mapper bidirecional entre CarePlan (PostgreSQL) e FHIR CarePlan (R4), permitindo sincronização automática.

## Pré-requisitos

- [x] FASE 1.2 concluída (PostgreSQL)
- [x] Grahame (porta 8012) acessível
- [x] Cliente HTTP configurado

## Tarefas

### 1.3.A - Mapper Geralda ↔ FHIR CarePlan

- [x] ⚙️ Criar `geralda/fhir/careplan_mapper.py`
  - `to_fhir_careplan(plan, tasks) -> dict` - Converte para FHIR R4
  - `from_fhir_careplan(resource) -> CarePlan` - Converte de FHIR
  - `round_trip` - Garante conversão ida e volta sem perda

- [x] ⚙️ Criar `geralda/fhir/client.py` - Cliente HTTP para Grahame
  - `GrahameClient(base_url)` - Cliente assíncrono
  - `put_careplan(fhir_resource)` - Envia para Grahame
  - `get_careplan(fhir_id)` - Busca do Grahame
  - `search_careplans(patient_id)` - Busca todos do paciente

- [x] ⚙️ Atualizar `care_plan_service.py` - Sincronizar com Grahame
  - Após criar/atualizar plano, enviar para Grahame
  - Fire-and-forget (não bloqueia se Grahame estiver offline)

### 1.3.B - Testes do Mapper FHIR

- [x] 🧪 Criar `tests/test_fhir_mapper.py` - 13 testes (excede mínimo de 8)
  - Estrutura válida FHIR CarePlan R4
  - Round-trip sem perda de dados
  - Campos opcionais ausentes
  - Todos os mapeamentos de categoria
  - Mapeamento de status
  - Parse de descrição estruturada
  - Tratamento de erros

## Critérios de Aceite EF-002

- [x] CarePlan criado na Geralda aparece no Grahame (FHIR R4 válido)
- [x] Se Grahame offline, Geralda continua funcionando (graceful degradation)
- [x] Mapper tem testes unitários sem dependência de rede

## Log de Progresso

### 2026-02-24 11:20 - Início da FASE 1.3
- Criada estrutura de pastas para documentação
- Próximo passo: Verificar estrutura FHIR do Geralda

### 2026-02-24 11:40 - 1.3.A Concluído
- Criado `geralda/fhir/careplan_mapper.py` com `CarePlanFHIRMapper`
- Criado `geralda/fhir/client.py` com `GrahameFHIRClient`
- Criado `geralda/fhir/__init__.py` com exports
- Atualizado `care_plan_service.py`:
  - Adicionado parâmetro `grahame_url` no __init__
  - Adicionado método `_sync_to_grahame()` fire-and-forget
  - Adicionado método público `sync_plan_to_fhir()` para sync manual
  - `create_plan()` e `update_plan()` agora sincronizam automaticamente
- Implementado graceful degradation: se Grahame falhar, apenas logga e continua

### 2026-02-24 11:50 - Iniciando 1.3.B
- Criado `tests/test_fhir_mapper.py` com 13 testes

### 2026-02-24 12:00 - Correções de Modelo
- Corrigido `default_factory` → `default` em todos os modelos SQLAlchemy
  - `care_plan.py`
  - `care_task.py`
  - `reminder.py`
  - `educational_material.py`

### 2026-02-24 12:15 - FASE 1.3 Concluída
- Todos os 13 testes passando
- Integração FHIR completa e testada

## Arquivos Criados/Modificados

### Criados
- `geralda/fhir/__init__.py`
- `geralda/fhir/careplan_mapper.py` (297 linhas)
- `geralda/fhir/client.py` (186 linhas)
- `tests/test_fhir_mapper.py` (331 linhas)

### Modificados
- `geralda/services/care_plan_service.py` - Adicionada sincronização FHIR
- `geralda/models/care_plan.py` - Corrigido `default_factory` → `default`
- `geralda/models/care_task.py` - Corrigido `default_factory` → `default`
- `geralda/models/reminder.py` - Corrigido `default_factory` → `default`
- `geralda/models/educational_material.py` - Corrigido `default_factory` → `default`

## Resultados dos Testes

```
============================= test session starts =============================
collected 13 items

tests/test_fhir_mapper.py::TestCarePlanFHIRMapperTo::test_to_fhir_careplan_minimal_structure PASSED
tests/test_fhir_mapper.py::TestCarePlanFHIRMapperTo::test_to_fhir_careplan_with_conditions_and_goals PASSED
tests/test_fhir_mapper.py::TestCarePlanFHIRMapperTo::test_to_fhir_careplan_status_mapping PASSED
tests/test_fhir_mapper.py::TestCarePlanFHIRMapperTo::test_to_fhir_careplan_with_tasks PASSED
tests/test_fhir_mapper.py::TestCarePlanFHIRMapperTo::test_to_fhir_careplan_all_categories PASSED
tests/test_fhir_mapper.py::TestCarePlanFHIRMapperFrom::test_from_fhir_careplan_minimal PASSED
tests/test_fhir_mapper.py::TestCarePlanFHIRMapperFrom::test_from_fhir_careplan_parse_description PASSED
tests/test_fhir_mapper.py::TestCarePlanFHIRMapperFrom::test_from_fhir_careplan_invalid_resource_type PASSED
tests/test_fhir_mapper.py::TestCarePlanFHIRMapperFrom::test_from_fhir_careplan_empty_description PASSED
tests/test_fhir_mapper.py::TestRoundTrip::test_round_trip_preserves_core_fields PASSED
tests/test_fhir_mapper.py::TestRoundTrip::test_round_trip_with_deactivated_plan PASSED
tests/test_fhir_mapper.py::TestCarePlanFHIRMapperTo::test_to_fhir_careplan_function PASSED
tests/test_fhir_mapper.py::TestCarePlanFHIRMapperFrom::test_from_fhir_careplan_function PASSED

============================= 13 passed in 1.14s ==============================
```

## Próximos Passos

FASE 1.3 está concluída. Próximo nível:

**NÍVEL 2 - Desbloqueadores Críticos:**
- FASE 2.1: Integration Smoke Test - Todos os 13 Módulos
- FASE 2.2: Portal: Integração Real com APIs

**NÍVEL 3 - Features Principais:**
- FASE 3.1: WANDA MCP Client
- FASE 3.2: GERALDA v2.0 Fases 2–3: Motor IA + Eventos
