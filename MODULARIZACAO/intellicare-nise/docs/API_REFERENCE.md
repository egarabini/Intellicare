# 📚 API Reference - IntelliCare NISE

## 📋 ÍNDICE

1. [Visão Geral](#visão-geral)
2. [Autenticação](#autenticação)
3. [Endpoints](#endpoints)
4. [Modelos de Dados](#modelos-de-dados)
5. [Códigos de Erro](#códigos-de-erro)
6. [Exemplos](#exemplos)

---

## 🎯 VISÃO GERAL

**Base URL**: `http://localhost:8000`  
**Versão**: `1.0.0`  
**Formato**: JSON  
**Documentação Interativa**: http://localhost:8000/docs

---

## 🔐 AUTENTICAÇÃO

Atualmente a API não requer autenticação. Em produção, será integrada com Keycloak SSO.

**Headers recomendados**:
```http
Content-Type: application/json
Accept: application/json
```

---

## 📡 ENDPOINTS

### **Health & Info**

#### `GET /health`

Verifica status da API.

**Response 200**:
```json
{
  "status": "healthy",
  "service": "intellicare-nise",
  "version": "1.0.0"
}
```

#### `GET /api/v1/info`

Informações do módulo.

**Response 200**:
```json
{
  "name": "intellicare-nise",
  "version": "1.0.0",
  "capabilities": ["oswaldo-integration", "chatbot", "rag", "flowise", "ollama"],
  "description": "Núcleo de Inteligência em Saúde e Educação",
  "metadata": {
    "integrations": ["oswaldo", "florence", "flowise", "ollama"],
    "endpoints": [...]
  }
}
```

---

### **Oswaldo Integration**

#### `GET /api/v1/oswaldo/paciente/{paciente_id}/resumo`

Busca resumo completo do paciente.

**Parâmetros**:
- `paciente_id` (path, required): ID do paciente
- `use_cache` (query, optional): Usar cache Redis (default: true)

**Response 200**:
```json
{
  "paciente_id": "pac-123",
  "diagnosticos": [
    {
      "paciente_id": "pac-123",
      "condicao": "diabetes",
      "classificacao": "tipo_2",
      "estadiamento": "A1",
      "data_diagnostico": "2024-01-15",
      "plano_cuidado_id": "plano-456"
    }
  ],
  "alertas_criticos": ["HbA1c muito elevada"],
  "total_alertas": 3,
  "plano_cuidado_atual": "plano-456",
  "risco_framingham": null
}
```

**Response 404**: Paciente não encontrado  
**Response 500**: Erro interno

#### `GET /api/v1/oswaldo/paciente/{paciente_id}/diagnosticos`

Busca diagnósticos do paciente.

**Parâmetros**:
- `paciente_id` (path, required): ID do paciente

**Response 200**:
```json
[
  {
    "paciente_id": "pac-123",
    "condicao": "diabetes",
    "classificacao": "tipo_2",
    "estadiamento": "A1",
    "data_diagnostico": "2024-01-15",
    "plano_cuidado_id": "plano-456"
  }
]
```

#### `GET /api/v1/oswaldo/paciente/{paciente_id}/alertas`

Busca alertas do paciente.

**Parâmetros**:
- `paciente_id` (path, required): ID do paciente
- `status` (query, optional): Status dos alertas (ativo, resolvido, todos)

**Response 200**:
```json
[
  {
    "alerta_id": "alerta-1",
    "tipo": "critico",
    "mensagem": "HbA1c muito elevada",
    "data_criacao": "2024-02-15",
    "status": "ativo",
    "paciente_id": "pac-123"
  }
]
```

---

### **Chatbot**

#### `POST /api/v1/chatbot/chat`

Envia mensagem para o chatbot Dr. Nise.

**Request Body**:
```json
{
  "question": "Qual o diagnóstico de diabetes do paciente pac-123?",
  "chatflow_id": "dr-nise-default",
  "session_id": "session-abc-123",
  "streaming": false
}
```

**Response 200**:
```json
{
  "text": "O paciente pac-123 possui diagnóstico de Diabetes Tipo 2...",
  "session_id": "session-abc-123",
  "chatflow_id": "dr-nise-default",
  "metadata": {
    "source": "oswaldo",
    "tools_used": ["oswaldo_diagnostico"]
  }
}
```

#### `GET /api/v1/chatbot/chatflows`

Lista chatflows disponíveis.

**Response 200**:
```json
{
  "total": 2,
  "chatflows": [
    {
      "id": "dr-nise-default",
      "name": "Dr. Nise - Assistente Médico",
      "description": "Chatbot padrão"
    }
  ]
}
```

#### `GET /api/v1/chatbot/chatflows/{chatflow_id}`

Detalhes de um chatflow.

**Response 200**:
```json
{
  "id": "dr-nise-default",
  "name": "Dr. Nise - Assistente Médico",
  "description": "Chatbot padrão para treinamento médico",
  "config": {
    "model": "llama2:7b",
    "temperature": 0.7
  }
}
```

#### `GET /api/v1/chatbot/health`

Verifica status do chatbot.

**Response 200**:
```json
{
  "status": "healthy",
  "flowise_available": true,
  "flowise_url": "http://localhost:3000"
}
```

#### `POST /api/v1/chatbot/test`

Testa chatbot com perguntas pré-definidas.

**Parâmetros**:
- `paciente_id` (query, required): ID do paciente

**Response 200**:
```json
{
  "paciente_id": "pac-123",
  "total_perguntas": 3,
  "resultados": [
    {
      "pergunta": "Qual o diagnóstico de diabetes do paciente pac-123?",
      "resposta": "O paciente possui...",
      "session_id": "session-test-123"
    }
  ]
}
```

---

## 📦 MODELOS DE DADOS

### **DiagnosticoResponse**
```typescript
{
  paciente_id: string
  condicao: "diabetes" | "has" | "drc"
  classificacao: string
  estadiamento: string
  data_diagnostico: string (ISO 8601)
  plano_cuidado_id?: string
}
```

### **AlertaResponse**
```typescript
{
  alerta_id: string
  tipo: "critico" | "aviso" | "info"
  mensagem: string
  data_criacao: string (ISO 8601)
  status: "ativo" | "resolvido"
  paciente_id: string
}
```

### **ChatRequest**
```typescript
{
  question: string
  chatflow_id: string = "dr-nise-default"
  session_id?: string
  streaming: boolean = false
}
```

---

### **Framingham Risk Score**

#### `POST /api/v1/framingham/calcular`

Calcula risco cardiovascular em 10 anos usando algoritmo Framingham.

**Request Body**:
```json
{
  "sexo": "M",
  "idade": 55,
  "colesterol_total": 220,
  "hdl": 45,
  "pa_sistolica": 140,
  "tabagismo": true,
  "diabetes": false
}
```

**Validações**:
- `sexo`: "M" (Masculino) ou "F" (Feminino)
- `idade`: 30-74 anos (faixa validada pelo Framingham)
- `colesterol_total`: 100-400 mg/dL
- `hdl`: 20-100 mg/dL
- `pa_sistolica`: 90-200 mmHg
- `tabagismo`: boolean
- `diabetes`: boolean

**Response 200**:
```json
{
  "risco_10_anos": 18.5,
  "classificacao": "intermediario",
  "pontos_totais": 12,
  "recomendacoes": [
    "⚠️ RISCO INTERMEDIÁRIO: Acompanhamento intensivo recomendado",
    "Estatina de intensidade moderada (Atorvastatina 10-20mg)",
    "Meta LDL < 100 mg/dL",
    "🩺 Controle rigoroso da pressão arterial (meta < 130/80 mmHg)",
    "Considerar anti-hipertensivo (IECA ou BRA)",
    "🚭 CESSAÇÃO DO TABAGISMO URGENTE - reduz risco em 50% em 1 ano",
    "Encaminhar para programa de cessação tabágica",
    "Considerar terapia de reposição de nicotina ou Bupropiona/Vareniclina",
    "🏃 Atividade física regular: 150 min/semana de exercício moderado",
    "🥗 Dieta mediterrânea ou DASH (rica em frutas, vegetais, grãos integrais)",
    "⚖️ Manter peso saudável (IMC 18.5-24.9)"
  ],
  "pontos_idade": 4,
  "pontos_colesterol": 1,
  "pontos_hdl": 1,
  "pontos_pa": 2,
  "pontos_tabagismo": 2,
  "pontos_diabetes": 0
}
```

**Classificação de Risco**:
- **Baixo**: < 10% - Manter estilo de vida saudável
- **Intermediário**: 10-20% - Estatina moderada + acompanhamento
- **Alto**: > 20% - Estatina alta intensidade + AAS + acompanhamento intensivo

**Response 422** (Validação):
```json
{
  "detail": [
    {
      "loc": ["body", "idade"],
      "msg": "ensure this value is greater than or equal to 30",
      "type": "value_error.number.not_ge"
    }
  ]
}
```

**Response 400** (Erro):
```json
{
  "detail": "Erro de validação: idade fora da faixa permitida"
}
```

---

#### `GET /api/v1/framingham/paciente/{paciente_id}`

Calcula risco Framingham para paciente do Oswaldo (busca dados automaticamente).

**Path Parameters**:
- `paciente_id`: ID do paciente no Oswaldo

**Dados Necessários no Oswaldo**:
- Dados demográficos (sexo, idade)
- Última medição de PA sistólica
- Último lipidograma (colesterol total, HDL)
- Histórico de tabagismo
- Diagnóstico de diabetes

**Response 200**:
```json
{
  "risco_10_anos": 15.2,
  "classificacao": "intermediario",
  "pontos_totais": 10,
  "recomendacoes": [...],
  "pontos_idade": 3,
  "pontos_colesterol": 1,
  "pontos_hdl": 0,
  "pontos_pa": 2,
  "pontos_tabagismo": 2,
  "pontos_diabetes": 2
}
```

**Response 404**:
```json
{
  "detail": "Paciente PAC999 não encontrado"
}
```

**Response 400**:
```json
{
  "detail": "Dados insuficientes para cálculo de risco: Lipidograma (colesterol total e HDL) não disponível"
}
```

**Exemplo de Uso**:
```bash
# Calcular risco para paciente PAC001
curl -X GET "http://localhost:8000/api/v1/framingham/paciente/PAC001"
```

---

## ⚠️ CÓDIGOS DE ERRO

| Código | Descrição |
|--------|-----------|
| 200 | Sucesso |
| 400 | Requisição inválida |
| 404 | Recurso não encontrado |
| 500 | Erro interno do servidor |
| 503 | Serviço indisponível |

---

**Versão**: 1.0.0  
**Última atualização**: 15/02/2026

