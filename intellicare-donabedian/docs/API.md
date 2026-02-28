# 📡 API REST - Documentação Completa

## Visão Geral

A API REST do módulo **intellicare-donabedian** fornece 30 endpoints organizados em 8 grupos funcionais para gerenciamento completo de indicadores de qualidade baseados no framework de Donabedian.

**Base URL**: `http://localhost:8003/api/v1`

**Formato**: JSON

**Autenticação**: Não implementada (planejada para versão futura)

---

## 📋 Grupos de Endpoints

### 1. Pilares (`/pillars`)
### 2. Indicadores (`/indicators`)
### 3. Associações Indicador-Pilar (`/indicator-pillars`)
### 4. Medições (`/measurements`)
### 5. Avaliação de Qualidade (`/assessment`)
### 6. Dashboard Analytics (`/dashboard`)
### 7. Análise de Tendências (`/trends`)
### 8. Health Check (`/health`)

---

## 1️⃣ Pilares - `/api/v1/pillars`

Os 7 pilares da qualidade de Donabedian são dados de referência fixos.

### `GET /pillars` - Listar todos os pilares

**Resposta 200**:
```json
[
  {
    "id": 1,
    "name": "Eficácia",
    "description": "Capacidade de produzir melhorias na saúde",
    "display_order": 1
  },
  {
    "id": 2,
    "name": "Efetividade",
    "description": "Grau de melhoria alcançado na prática",
    "display_order": 2
  }
]
```

### `GET /pillars/{id}` - Obter pilar específico

**Parâmetros**:
- `id` (path, integer): ID do pilar

**Resposta 200**:
```json
{
  "id": 1,
  "name": "Eficácia",
  "description": "Capacidade de produzir melhorias na saúde",
  "display_order": 1
}
```

**Resposta 404**:
```json
{
  "detail": "Pillar not found"
}
```

### `POST /pillars` - Criar novo pilar

**Body**:
```json
{
  "name": "Novo Pilar",
  "description": "Descrição do novo pilar",
  "display_order": 8
}
```

**Resposta 201**:
```json
{
  "id": 8,
  "name": "Novo Pilar",
  "description": "Descrição do novo pilar",
  "display_order": 8
}
```

### `PUT /pillars/{id}` - Atualizar pilar

**Parâmetros**:
- `id` (path, integer): ID do pilar

**Body**:
```json
{
  "name": "Pilar Atualizado",
  "description": "Nova descrição",
  "display_order": 8
}
```

**Resposta 200**: Retorna o pilar atualizado

### `DELETE /pillars/{id}` - Deletar pilar

**Parâmetros**:
- `id` (path, integer): ID do pilar

**Resposta 204**: Sem conteúdo (sucesso)

**Resposta 404**: Pilar não encontrado

---

## 2️⃣ Indicadores - `/api/v1/indicators`

Gerenciamento de indicadores de qualidade.

### `GET /indicators` - Listar indicadores

**Query Parameters**:
- `skip` (integer, default=0): Número de registros para pular
- `limit` (integer, default=100): Número máximo de registros
- `triad_dimension` (string, optional): Filtrar por dimensão (structure, process, outcome)

**Resposta 200**:
```json
[
  {
    "id": 1,
    "name": "Taxa de Ocupação de Leitos",
    "description": "Percentual de leitos ocupados",
    "formula": "(leitos ocupados / total de leitos) * 100",
    "unit": "%",
    "triad_dimension": "structure",
    "target_value": 85.0,
    "target_operator": "greater_equal",
    "created_at": "2024-01-15T10:30:00",
    "updated_at": "2024-01-15T10:30:00"
  }
]
```

### `GET /indicators/{id}` - Obter indicador específico

**Resposta 200**: Retorna o indicador completo

### `POST /indicators` - Criar indicador

**Body**:
```json
{
  "name": "Taxa de Ocupação de Leitos",
  "description": "Percentual de leitos ocupados",
  "formula": "(leitos ocupados / total de leitos) * 100",
  "unit": "%",
  "triad_dimension": "structure",
  "target_value": 85.0,
  "target_operator": "greater_equal"
}
```

**Campos obrigatórios**:
- `name`: Nome do indicador (único)
- `description`: Descrição detalhada
- `formula`: Fórmula de cálculo
- `unit`: Unidade de medida
- `triad_dimension`: Dimensão da tríade (structure, process, outcome)
- `target_value`: Valor alvo
- `target_operator`: Operador de comparação (greater, greater_equal, less, less_equal, equal)

**Resposta 201**: Retorna o indicador criado

### `PUT /indicators/{id}` - Atualizar indicador

**Body**: Mesmos campos do POST (todos opcionais)

**Resposta 200**: Retorna o indicador atualizado

### `DELETE /indicators/{id}` - Deletar indicador

**Resposta 204**: Sem conteúdo (sucesso)

---

## 3️⃣ Associações Indicador-Pilar - `/api/v1/indicator-pillars`

Gerenciamento de associações N:N entre indicadores e pilares com pesos.

### `GET /indicator-pillars` - Listar associações

**Query Parameters**:
- `indicator_id` (integer, optional): Filtrar por indicador
- `pillar_id` (integer, optional): Filtrar por pilar

**Resposta 200**:
```json
[
  {
    "id": 1,
    "indicator_id": 1,
    "pillar_id": 1,
    "weight": 1.0
  }
]
```

### `POST /indicator-pillars` - Criar associação

**Body**:
```json
{
  "indicator_id": 1,
  "pillar_id": 1,
  "weight": 1.5
}
```

**Campos**:
- `indicator_id` (obrigatório): ID do indicador
- `pillar_id` (obrigatório): ID do pilar
- `weight` (opcional, default=1.0): Peso da associação

**Resposta 201**: Retorna a associação criada

### `PUT /indicator-pillars/{id}` - Atualizar peso

**Body**:
```json
{
  "weight": 2.0
}
```

### `DELETE /indicator-pillars/{id}` - Deletar associação

**Resposta 204**: Sem conteúdo (sucesso)

---

## 4️⃣ Medições - `/api/v1/measurements`

Gerenciamento de medições temporais de indicadores.

### `GET /measurements` - Listar medições

**Query Parameters**:
- `indicator_id` (integer, optional): Filtrar por indicador
- `period_start` (date, optional): Data inicial do período
- `period_end` (date, optional): Data final do período
- `status` (string, optional): Filtrar por status (green, yellow, red)

**Resposta 200**:
```json
[
  {
    "id": 1,
    "indicator_id": 1,
    "value": 87.5,
    "period_start": "2024-01-01",
    "period_end": "2024-01-31",
    "period_type": "monthly",
    "status": "green",
    "created_at": "2024-02-01T08:00:00"
  }
]
```

### `POST /measurements` - Criar medição

**Body**:
```json
{
  "indicator_id": 1,
  "value": 87.5,
  "period_start": "2024-01-01",
  "period_end": "2024-01-31",
  "period_type": "monthly",
  "status": "green"
}
```

**Campos obrigatórios**:
- `indicator_id`: ID do indicador
- `value`: Valor medido
- `period_start`: Data de início do período
- `period_end`: Data de fim do período
- `period_type`: Tipo de período (daily, weekly, monthly, quarterly, yearly)
- `status`: Status da medição (green, yellow, red)

**Resposta 201**: Retorna a medição criada

---

## 5️⃣ Avaliação de Qualidade - `/api/v1/assessment`

Endpoints para avaliação de qualidade baseada nas medições.

### `GET /assessment/pillar/{pillar_id}` - Avaliação por pilar

**Parâmetros**:
- `pillar_id` (path, integer): ID do pilar
- `start_date` (query, date, optional): Data inicial
- `end_date` (query, date, optional): Data final

**Resposta 200**:
```json
{
  "pillar_id": 1,
  "pillar_name": "Eficácia",
  "score": 8.5,
  "total_indicators": 10,
  "indicators_met": 8,
  "indicators_not_met": 2,
  "compliance_rate": 80.0,
  "period_start": "2024-01-01",
  "period_end": "2024-12-31"
}
```

### `GET /assessment/overall` - Avaliação geral

**Query Parameters**:
- `start_date` (date, optional): Data inicial
- `end_date` (date, optional): Data final

**Resposta 200**:
```json
{
  "overall_score": 7.8,
  "total_indicators": 50,
  "indicators_met": 39,
  "compliance_rate": 78.0,
  "pillar_scores": [
    {
      "pillar_id": 1,
      "pillar_name": "Eficácia",
      "score": 8.5,
      "compliance_rate": 85.0
    }
  ],
  "period_start": "2024-01-01",
  "period_end": "2024-12-31"
}
```

---

## 6️⃣ Dashboard Analytics - `/api/v1/dashboard`

Endpoints para métricas agregadas do dashboard.

### `GET /dashboard/summary` - Resumo geral

**Resposta 200**:
```json
{
  "total_pillars": 7,
  "total_indicators": 50,
  "total_measurements": 600,
  "latest_measurement_date": "2024-12-31",
  "overall_compliance": 78.0,
  "green_indicators": 39,
  "yellow_indicators": 8,
  "red_indicators": 3
}
```

### `GET /dashboard/pillar-distribution` - Distribuição por pilar

**Resposta 200**:
```json
[
  {
    "pillar_name": "Eficácia",
    "indicator_count": 10,
    "avg_compliance": 85.0
  }
]
```

---

## 7️⃣ Análise de Tendências - `/api/v1/trends`

Endpoints para análise temporal de indicadores.

### `GET /trends/indicator/{indicator_id}` - Tendência de indicador

**Parâmetros**:
- `indicator_id` (path, integer): ID do indicador
- `start_date` (query, date, optional): Data inicial
- `end_date` (query, date, optional): Data final
- `period_type` (query, string, optional): Tipo de agregação

**Resposta 200**:
```json
{
  "indicator_id": 1,
  "indicator_name": "Taxa de Ocupação",
  "data_points": [
    {
      "period_start": "2024-01-01",
      "period_end": "2024-01-31",
      "value": 87.5,
      "status": "green"
    }
  ],
  "trend": "increasing",
  "avg_value": 86.2,
  "min_value": 82.0,
  "max_value": 90.0
}
```

---

## 8️⃣ Health Check - `/health`

### `GET /health` - Verificar saúde da API

**Resposta 200**:
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2024-02-10T15:30:00"
}
```

---

## 🔧 Códigos de Status HTTP

| Código | Significado |
|--------|-------------|
| 200 | OK - Requisição bem-sucedida |
| 201 | Created - Recurso criado com sucesso |
| 204 | No Content - Recurso deletado com sucesso |
| 400 | Bad Request - Dados inválidos |
| 404 | Not Found - Recurso não encontrado |
| 422 | Unprocessable Entity - Erro de validação |
| 500 | Internal Server Error - Erro no servidor |

---

## 📝 Notas Importantes

1. **Validação**: Todos os endpoints validam dados usando Pydantic schemas
2. **Async**: Todos os endpoints são assíncronos para melhor performance
3. **Paginação**: Endpoints de listagem suportam `skip` e `limit`
4. **Filtros**: Endpoints de listagem suportam filtros via query parameters
5. **Timestamps**: Datas/horas em formato ISO 8601
6. **Documentação Interativa**: Acesse `/docs` para Swagger UI

---

## 🚀 Exemplos de Uso

Ver arquivo principal [README.md](../README.md) para exemplos completos de uso com Python/httpx.

