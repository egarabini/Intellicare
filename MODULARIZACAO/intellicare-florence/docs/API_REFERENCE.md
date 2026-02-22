# 📡 API Reference - Florence

**Versão**: 1.0.0  
**Base URL**: `http://localhost:8002`  
**Formato**: JSON  
**Autenticação**: Bearer Token (opcional)

---

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Endpoints Core](#endpoints-core)
3. [Endpoints RAG](#endpoints-rag)
4. [Schemas](#schemas)
5. [Códigos de Erro](#códigos-de-erro)
6. [Rate Limits](#rate-limits)

---

## 🎯 Visão Geral

Florence expõe **10 endpoints REST**:

### Endpoints Core (7)
- `GET /health` - Health check
- `GET /info` - Informações do módulo
- `GET /api/v1/resources` - Recursos disponíveis
- `POST /api/v1/interpret` - Interpretação simples
- `POST /api/v1/analyze` - Análise completa
- `POST /api/v1/analyze-trends` - Análise de tendências
- `POST /api/v1/validate` - Validação de dados

### Endpoints RAG (3)
- `POST /api/v1/rag/query` - Query direta ao RAG
- `GET /api/v1/rag/protocols` - Listar protocolos
- `POST /api/v1/analyze-with-rag` - Análise com RAG

---

## 🔧 Endpoints Core

### 1. Health Check

**Endpoint**: `GET /health`

**Descrição**: Verifica saúde do serviço.

**Request**: Nenhum parâmetro

**Response**:
```json
{
  "status": "healthy",
  "module": "florence",
  "version": "1.0.0",
  "timestamp": "2026-02-20T10:00:00Z",
  "dependencies": {
    "rag_enabled": true,
    "database": "connected"
  }
}
```

**Status Codes**:
- `200 OK`: Serviço saudável
- `503 Service Unavailable`: Serviço com problemas

---

### 2. Module Info

**Endpoint**: `GET /info`

**Descrição**: Informações detalhadas do módulo.

**Request**: Nenhum parâmetro

**Response**:
```json
{
  "name": "florence",
  "version": "1.0.0",
  "description": "Clinical Analysis Module",
  "capabilities": [
    "lab_interpretation",
    "correlation_detection",
    "trend_analysis",
    "rag_protocols"
  ],
  "supported_labs": 27,
  "supported_panels": 6,
  "protocols_indexed": 10
}
```

**Status Codes**:
- `200 OK`: Sucesso

---

### 3. List Resources

**Endpoint**: `GET /api/v1/resources`

**Descrição**: Lista todos os recursos disponíveis (exames, painéis, correlações).

**Request**: Nenhum parâmetro

**Response**:
```json
{
  "supported_labs": [
    {
      "id": "glucose_fasting",
      "name": "Glicemia de Jejum",
      "unit": "mg/dL",
      "panel": "metabolic",
      "reference_range": {"min": 70.0, "max": 100.0}
    }
  ],
  "panels": [
    {
      "id": "metabolic",
      "name": "Painel Metabólico",
      "labs": ["glucose_fasting", "hba1c"]
    }
  ],
  "correlation_patterns": [
    {
      "id": "metabolic_syndrome",
      "name": "Síndrome Metabólica",
      "required_labs": ["glucose_fasting", "triglycerides", "hdl"]
    }
  ]
}
```

**Status Codes**:
- `200 OK`: Sucesso

---

### 4. Interpret Labs

**Endpoint**: `POST /api/v1/interpret`

**Descrição**: Interpretação simples de exames laboratoriais.

**Request Body**:
```json
{
  "patient_id": "PAT-001",
  "results": {
    "glucose_fasting": 180.0,
    "hba1c": 8.5
  },
  "timestamp": "2026-02-20T10:00:00Z"  // Opcional
}
```

**Response**:
```json
{
  "patient_id": "PAT-001",
  "timestamp": "2026-02-20T10:00:00Z",
  "interpretations": [
    {
      "lab_id": "glucose_fasting",
      "value": 180.0,
      "unit": "mg/dL",
      "reference_range": {"min": 70.0, "max": 100.0},
      "status": "HIGH",
      "severity": "MODERATE",
      "deviation_percentage": 80.0,
      "clinical_significance": "Hiperglicemia de jejum..."
    }
  ],
  "summary": {
    "total_labs": 2,
    "abnormal_count": 2,
    "critical_count": 0
  }
}
```

**Status Codes**:
- `200 OK`: Sucesso
- `400 Bad Request`: Dados inválidos
- `422 Unprocessable Entity`: Validação falhou

**Exemplo cURL**:
```bash
curl -X POST http://localhost:8002/api/v1/interpret \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "PAT-001",
    "results": {"glucose_fasting": 180.0}
  }'
```

---

### 5. Analyze Labs

**Endpoint**: `POST /api/v1/analyze`

**Descrição**: Análise completa com detecção de correlações.

**Request Body**:
```json
{
  "patient_id": "PAT-002",
  "results": {
    "glucose_fasting": 180.0,
    "hba1c": 8.5,
    "triglycerides": 250.0,
    "hdl": 35.0,
    "systolic_bp": 145.0
  },
  "timestamp": "2026-02-20T10:00:00Z"
}
```

**Response**:
```json
{
  "patient_id": "PAT-002",
  "timestamp": "2026-02-20T10:00:00Z",
  "interpretations": [...],
  "correlations": [
    {
      "pattern_name": "metabolic_syndrome",
      "confidence": 0.85,
      "involved_labs": ["glucose_fasting", "triglycerides", "hdl"],
      "clinical_interpretation": "Síndrome metabólica detectada...",
      "recommendations": [
        "Avaliar risco cardiovascular",
        "Considerar mudanças no estilo de vida"
      ]
    }
  ],
  "summary": {
    "total_labs": 5,
    "abnormal_count": 4,
    "critical_count": 0,
    "correlations_detected": 1,
    "overall_status": "ATTENTION_NEEDED"
  }
}
```

**Status Codes**:
- `200 OK`: Sucesso
- `400 Bad Request`: Dados inválidos

**Exemplo cURL**:
```bash
curl -X POST http://localhost:8002/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "PAT-002",
    "results": {
      "glucose_fasting": 180.0,
      "triglycerides": 250.0,
      "hdl": 35.0
    }
  }'
```

---

### 6. Analyze Trends

**Endpoint**: `POST /api/v1/analyze-trends`

**Descrição**: Análise de tendências em séries temporais.

**Request Body**:
```json
{
  "patient_id": "PAT-003",
  "history": [
    {
      "timestamp": "2026-01-01T00:00:00Z",
      "results": {"glucose_fasting": 110.0}
    },
    {
      "timestamp": "2026-01-15T00:00:00Z",
      "results": {"glucose_fasting": 130.0}
    },
    {
      "timestamp": "2026-02-01T00:00:00Z",
      "results": {"glucose_fasting": 150.0}
    }
  ]
}
```

**Response**:
```json
{
  "patient_id": "PAT-003",
  "trends": [
    {
      "lab_id": "glucose_fasting",
      "direction": "INCREASING",
      "slope": 2.67,
      "r_squared": 0.98,
      "data_points": 3,
      "prediction_30d": 170.0,
      "clinical_significance": "Tendência de piora da glicemia..."
    }
  ],
  "summary": {
    "total_trends": 1,
    "worsening_trends": 1,
    "improving_trends": 0,
    "stable_trends": 0
  }
}
```

**Status Codes**:
- `200 OK`: Sucesso
- `400 Bad Request`: Dados insuficientes (mínimo 3 pontos)

---

### 7. Validate Data

**Endpoint**: `POST /api/v1/validate`

**Descrição**: Valida dados clínicos antes de processar.

**Request Body**:
```json
{
  "patient_id": "PAT-004",
  "results": {
    "glucose_fasting": 180.0,
    "hemoglobin": 12.5
  }
}
```

**Response**:
```json
{
  "valid": true,
  "errors": [],
  "warnings": [
    {
      "field": "glucose_fasting",
      "message": "Valor acima do normal",
      "severity": "WARNING"
    }
  ]
}
```

**Status Codes**:
- `200 OK`: Validação completa (mesmo com erros)

---

## 🤖 Endpoints RAG

### 8. RAG Query

**Endpoint**: `POST /api/v1/rag/query`

**Descrição**: Query direta ao sistema RAG para buscar protocolos clínicos.

**Request Body**:
```json
{
  "query": "Como manejar diabetes tipo 2?",
  "top_k": 3,
  "filters": {
    "specialty": "Endocrinologia"
  }
}
```

**Response**:
```json
{
  "query": "Como manejar diabetes tipo 2?",
  "results": [
    {
      "protocol_id": "diabetes_tipo2",
      "title": "Manejo de Diabetes Mellitus Tipo 2",
      "content": "# Diabetes Tipo 2\n\n## Indicações...",
      "score": 0.95,
      "metadata": {
        "specialty": "Endocrinologia",
        "version": "1.0",
        "date": "2024-01-15"
      }
    }
  ],
  "total_results": 3,
  "execution_time_ms": 45.2
}
```

**Status Codes**:
- `200 OK`: Sucesso
- `400 Bad Request`: Query inválida
- `503 Service Unavailable`: RAG não habilitado

**Exemplo cURL**:
```bash
curl -X POST http://localhost:8002/api/v1/rag/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Como interpretar creatinina elevada?",
    "top_k": 3
  }'
```

---

### 9. List Protocols

**Endpoint**: `GET /api/v1/rag/protocols`

**Descrição**: Lista todos os protocolos clínicos indexados.

**Request**: Nenhum parâmetro

**Response**:
```json
{
  "protocols": [
    {
      "id": "diabetes_tipo2",
      "title": "Manejo de Diabetes Mellitus Tipo 2",
      "specialty": "Endocrinologia",
      "version": "1.0",
      "date": "2024-01-15",
      "chunks": 3
    }
  ],
  "total_protocols": 10,
  "total_chunks": 30
}
```

**Status Codes**:
- `200 OK`: Sucesso
- `503 Service Unavailable`: RAG não habilitado

**Exemplo cURL**:
```bash
curl http://localhost:8002/api/v1/rag/protocols
```

---

### 10. Analyze with RAG

**Endpoint**: `POST /api/v1/analyze-with-rag`

**Descrição**: Análise completa com consulta a protocolos clínicos via RAG.

**Request Body**:
```json
{
  "patient_id": "PAT-005",
  "results": {
    "glucose_fasting": 180.0,
    "hba1c": 8.5
  },
  "query": "Como manejar diabetes tipo 2?",  // Opcional
  "top_k": 3,
  "timestamp": "2026-02-20T10:00:00Z"
}
```

**Response**:
```json
{
  "patient_id": "PAT-005",
  "timestamp": "2026-02-20T10:00:00Z",
  "interpretations": [...],
  "correlations": [...],
  "summary": {...},
  "relevant_protocols": [
    {
      "protocol_id": "diabetes_tipo2",
      "title": "Manejo de Diabetes Mellitus Tipo 2",
      "content": "...",
      "score": 0.95,
      "metadata": {...}
    }
  ],
  "rag_query": "Como interpretar e manejar: diabetes pattern, glucose fasting HIGH",
  "rag_execution_time_ms": 45.2
}
```

**Comportamento**:
- Se `query` fornecida: usa a query customizada
- Se `query` omitida: gera automaticamente baseada nos achados clínicos

**Status Codes**:
- `200 OK`: Sucesso
- `400 Bad Request`: Dados inválidos
- `503 Service Unavailable`: RAG não habilitado

**Exemplo cURL**:
```bash
curl -X POST http://localhost:8002/api/v1/analyze-with-rag \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "PAT-005",
    "results": {"glucose_fasting": 180.0, "hba1c": 8.5}
  }'
```

---

## 📦 Schemas

### LabResult

```json
{
  "lab_id": "string",
  "value": "number",
  "unit": "string",
  "reference_range": {
    "min": "number",
    "max": "number"
  },
  "status": "NORMAL | BORDERLINE | LOW | HIGH | CRITICAL_LOW | CRITICAL_HIGH",
  "severity": "NORMAL | MILD | MODERATE | SEVERE | CRITICAL",
  "deviation_percentage": "number",
  "clinical_significance": "string"
}
```

### Correlation

```json
{
  "pattern_name": "string",
  "confidence": "number (0-1)",
  "involved_labs": ["string"],
  "clinical_interpretation": "string",
  "recommendations": ["string"]
}
```

### Trend

```json
{
  "lab_id": "string",
  "direction": "INCREASING | DECREASING | STABLE",
  "slope": "number",
  "r_squared": "number (0-1)",
  "data_points": "integer",
  "prediction_30d": "number",
  "clinical_significance": "string"
}
```

### Protocol

```json
{
  "protocol_id": "string",
  "title": "string",
  "content": "string (markdown)",
  "score": "number (0-1)",
  "metadata": {
    "specialty": "string",
    "version": "string",
    "date": "string (ISO 8601)",
    "source": "string"
  }
}
```

---

## ⚠️ Códigos de Erro

### 400 Bad Request

**Causa**: Dados inválidos no request

**Exemplo**:
```json
{
  "error": "Invalid request",
  "details": {
    "field": "results",
    "message": "Results cannot be empty"
  }
}
```

### 422 Unprocessable Entity

**Causa**: Validação de dados falhou

**Exemplo**:
```json
{
  "error": "Validation failed",
  "details": [
    {
      "field": "patient_id",
      "message": "Patient ID is required"
    }
  ]
}
```

### 503 Service Unavailable

**Causa**: Serviço ou dependência indisponível

**Exemplo**:
```json
{
  "error": "Service unavailable",
  "message": "RAG system is not enabled",
  "suggestion": "Enable RAG in configuration"
}
```

### 500 Internal Server Error

**Causa**: Erro interno do servidor

**Exemplo**:
```json
{
  "error": "Internal server error",
  "message": "An unexpected error occurred",
  "request_id": "req-123456"
}
```

---

## 🚦 Rate Limits

### Limites Padrão

- **Requests por minuto**: 60
- **Requests por hora**: 1000
- **Concurrent requests**: 10

### Headers de Rate Limit

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1645354800
```

### Resposta quando limite excedido

**Status**: `429 Too Many Requests`

```json
{
  "error": "Rate limit exceeded",
  "retry_after": 30,
  "limit": 60,
  "window": "1 minute"
}
```

---

## 📊 Performance SLA

### Tempos de Resposta (p95)

- `GET /health`: < 10ms
- `GET /info`: < 20ms
- `GET /api/v1/resources`: < 50ms
- `POST /api/v1/interpret`: < 200ms
- `POST /api/v1/analyze`: < 300ms
- `POST /api/v1/analyze-trends`: < 400ms
- `POST /api/v1/rag/query`: < 500ms
- `POST /api/v1/analyze-with-rag`: < 600ms

### Throughput

- **Interpretações**: > 100 req/s
- **Análises completas**: > 50 req/s
- **Queries RAG**: > 20 req/s

---

## 🔐 Autenticação (Opcional)

Se autenticação estiver habilitada:

```bash
curl -X POST http://localhost:8002/api/v1/analyze \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{...}'
```

---

**Versão**: 1.0.0
**Última Atualização**: 2026-02-20
**Autor**: Equipe IntelliCare
