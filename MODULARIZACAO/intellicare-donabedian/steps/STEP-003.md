# STEP-003: Schemas Pydantic

**Objetivo:** Criar schemas Pydantic para validação e serialização de dados.

**Tempo Estimado:** 2h
**Status:** ✅ CONCLUÍDO

---

## 📋 Tarefas

- [x] Criar schemas para Pillar (Create, Update, Read, List)
- [x] Criar schemas para Indicator (Create, Update, Read, List)
- [x] Criar schemas para IndicatorPillar (Create, Update, Read, List)
- [x] Criar schemas para Measurement (Create, Update, Read, List)
- [x] Criar schemas de resposta (PaginatedResponse, ErrorResponse)
- [x] Adicionar validações customizadas
- [x] Criar testes unitários para schemas

---

## 🎯 Schemas a Criar

### 1. Pillar Schemas
- `PillarBase` - Campos comuns
- `PillarCreate` - Criação (sem id)
- `PillarUpdate` - Atualização (campos opcionais)
- `PillarRead` - Leitura (com id, timestamps)
- `PillarList` - Lista paginada

### 2. Indicator Schemas
- `IndicatorBase` - Campos comuns
- `IndicatorCreate` - Criação (sem id, timestamps)
- `IndicatorUpdate` - Atualização (campos opcionais)
- `IndicatorRead` - Leitura (com id, timestamps, relationships)
- `IndicatorList` - Lista paginada

### 3. IndicatorPillar Schemas
- `IndicatorPillarBase` - Campos comuns
- `IndicatorPillarCreate` - Criação
- `IndicatorPillarUpdate` - Atualização
- `IndicatorPillarRead` - Leitura (com relationships)
- `IndicatorPillarList` - Lista paginada

### 4. Measurement Schemas
- `MeasurementBase` - Campos comuns
- `MeasurementCreate` - Criação (sem status - auto-calculado)
- `MeasurementUpdate` - Atualização
- `MeasurementRead` - Leitura (com status, timestamps)
- `MeasurementList` - Lista paginada

### 5. Common Schemas
- `PaginatedResponse[T]` - Resposta paginada genérica
- `ErrorResponse` - Resposta de erro
- `HealthResponse` - Health check
- `InfoResponse` - Module info

---

## 🔧 Validações Customizadas

### Pillar
- `display_order`: 1-7
- `name`: max 50 chars, unique

### Indicator
- `target_value`: > 0
- `weight`: 0.0-1.0
- `formula`: não vazio

### IndicatorPillar
- `weight`: 0.0-1.0

### Measurement
- `period_end` >= `period_start`
- `value`: >= 0

---

## 📝 Progresso

**Início:** 2026-02-10
**Fim:** 2026-02-10
**Tempo Real:** ~45min

---

## 📦 Arquivos Criados

### Schemas (6 arquivos)
1. ✅ `src/donabedian/schemas/common.py` - Schemas comuns (PaginatedResponse, ErrorResponse, etc.)
2. ✅ `src/donabedian/schemas/pillar.py` - Schemas de Pillar (Create, Update, Read, List)
3. ✅ `src/donabedian/schemas/indicator.py` - Schemas de Indicator (Create, Update, Read, List)
4. ✅ `src/donabedian/schemas/indicator_pillar.py` - Schemas de IndicatorPillar (Create, Update, Read, List)
5. ✅ `src/donabedian/schemas/measurement.py` - Schemas de Measurement (Create, Update, Read, List)
6. ✅ `src/donabedian/schemas/__init__.py` - Exports de todos os schemas

### Testes (3 arquivos)
1. ✅ `tests/unit/test_schemas_pillar.py` - Testes de Pillar schemas
2. ✅ `tests/unit/test_schemas_indicator.py` - Testes de Indicator schemas
3. ✅ `tests/unit/test_schemas_measurement.py` - Testes de Measurement schemas

---

## 🎯 Schemas Implementados

### Common Schemas (6 schemas)
- ✅ `PaginatedResponse[T]` - Resposta paginada genérica
- ✅ `ErrorDetail` - Detalhe de erro
- ✅ `ErrorResponse` - Resposta de erro
- ✅ `HealthResponse` - Health check
- ✅ `InfoResponse` - Informações do módulo
- ✅ `MessageResponse` - Mensagem simples

### Pillar Schemas (5 schemas)
- ✅ `PillarBase` - Campos comuns
- ✅ `PillarCreate` - Criação (validação: display_order 1-7, name não vazio)
- ✅ `PillarUpdate` - Atualização (campos opcionais)
- ✅ `PillarRead` - Leitura (com id)
- ✅ `PillarList` - Lista simplificada

### Indicator Schemas (7 schemas)
- ✅ `TriadDimensionSchema` - Enum (structure, process, outcome)
- ✅ `TargetOperatorSchema` - Enum (>=, <=, ==)
- ✅ `IndicatorBase` - Campos comuns
- ✅ `IndicatorCreate` - Criação (validação: target_value > 0, strings não vazias)
- ✅ `IndicatorUpdate` - Atualização (campos opcionais)
- ✅ `IndicatorRead` - Leitura (com id, timestamps)
- ✅ `IndicatorList` - Lista simplificada

### IndicatorPillar Schemas (6 schemas)
- ✅ `IndicatorPillarBase` - Campos comuns
- ✅ `IndicatorPillarCreate` - Criação (validação: weight 0.0-1.0)
- ✅ `IndicatorPillarUpdate` - Atualização (apenas weight)
- ✅ `IndicatorPillarRead` - Leitura (com id)
- ✅ `IndicatorPillarWithNames` - Leitura com nomes relacionados
- ✅ `IndicatorPillarList` - Lista simplificada

### Measurement Schemas (8 schemas)
- ✅ `PeriodTypeSchema` - Enum (daily, weekly, monthly, quarterly, yearly)
- ✅ `MeasurementStatusSchema` - Enum (green, yellow, red)
- ✅ `MeasurementBase` - Campos comuns
- ✅ `MeasurementCreate` - Criação (validação: period_end >= period_start, value >= 0)
- ✅ `MeasurementUpdate` - Atualização (campos opcionais)
- ✅ `MeasurementRead` - Leitura (com id, status, timestamps)
- ✅ `MeasurementList` - Lista simplificada
- ✅ `MeasurementWithIndicator` - Leitura com nome do indicador

**Total:** 32 schemas criados

---

## ✅ Validações Implementadas

### Pillar
- ✅ `display_order`: 1-7 (ge=1, le=7)
- ✅ `name`: max 50 chars, não vazio, trim whitespace
- ✅ `description`: max 500 chars, não vazio, trim whitespace

### Indicator
- ✅ `target_value`: > 0 (gt=0)
- ✅ `name`: max 200 chars, não vazio, trim whitespace
- ✅ `description`: max 1000 chars, não vazio, trim whitespace
- ✅ `formula`: max 500 chars, não vazio, trim whitespace
- ✅ `unit`: max 50 chars, não vazio, trim whitespace

### IndicatorPillar
- ✅ `weight`: 0.0-1.0 (ge=0.0, le=1.0)
- ✅ `indicator_id`: > 0 (gt=0)
- ✅ `pillar_id`: > 0 (gt=0)

### Measurement
- ✅ `period_end` >= `period_start` (model_validator)
- ✅ `value`: >= 0 (ge=0.0)
- ✅ `indicator_id`: > 0 (gt=0)

---

## 🧪 Testes Criados

### test_schemas_pillar.py (3 classes, 10 testes)
- ✅ TestPillarCreate: valid, name_too_long, display_order_out_of_range, empty_name, whitespace_trimmed
- ✅ TestPillarUpdate: valid_partial, empty_update, invalid_display_order
- ✅ TestPillarRead: valid_read, from_orm_model

### test_schemas_indicator.py (3 classes, 8 testes)
- ✅ TestIndicatorCreate: valid, target_value_positive, empty_formula, invalid_triad
- ✅ TestIndicatorUpdate: valid_partial, empty_update, invalid_target_value
- ✅ TestIndicatorRead: valid_read

### test_schemas_measurement.py (3 classes, 8 testes)
- ✅ TestMeasurementCreate: valid, period_end_before_start, negative_value, same_dates
- ✅ TestMeasurementUpdate: valid_partial, empty_update, period_validation
- ✅ TestMeasurementRead: valid_read

**Total:** 26 testes unitários

---

## 🎉 Conclusão

STEP-003 concluído com sucesso! Todos os schemas Pydantic foram criados com:
- ✅ Validações robustas
- ✅ Documentação inline (Field descriptions)
- ✅ Exemplos JSON (json_schema_extra)
- ✅ Suporte a ORM (from_attributes=True)
- ✅ Testes unitários abrangentes
- ✅ Type hints completos

**Próximo passo:** STEP-004 - API Routes (4h)


