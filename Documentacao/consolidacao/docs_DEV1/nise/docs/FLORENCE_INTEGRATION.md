# 🤖 FLORENCE INTEGRATION - Dr. Nise AI Assistant

---

## 📋 VISÃO GERAL

**Florence** (Dr. Nise) é o assistente de IA do módulo NISE, especializado em treinamento médico e recursos FHIR R4.

**Tecnologias**:
- **Flowise**: Plataforma RAG/Chatbot
- **Ollama**: LLM local (llama2:7b)
- **pgvector**: Armazenamento de embeddings
- **FastAPI**: API de integração

---

## 🎯 FUNCIONALIDADES

### **1. Chat Interativo**
- Conversação natural sobre FHIR R4
- Contexto de sessão mantido
- Respostas baseadas em conhecimento médico

### **2. RAG (Retrieval-Augmented Generation)**
- Base de conhecimento FHIR R4
- Documentação médica
- Exemplos de uso
- Melhores práticas

### **3. Feedback e Aprendizado**
- Sistema de avaliação (1-5 estrelas)
- Comentários dos usuários
- Melhoria contínua

---

## 🚀 ENDPOINTS

### **POST /api/v1/florence/chat**

Enviar mensagem para Florence.

**Request**:
```json
{
  "message": "Como criar um recurso Patient FHIR R4?",
  "session_id": "session-123",
  "context": {
    "user_role": "medical_student",
    "specialty": "cardiology"
  }
}
```

**Response**:
```json
{
  "message": "Para criar um recurso Patient FHIR R4, você precisa...",
  "session_id": "session-123",
  "timestamp": "2026-03-24T10:00:00Z",
  "sources": [
    "FHIR R4 Patient Resource Documentation",
    "NISE Training Examples"
  ],
  "confidence": 0.95
}
```

---

### **GET /api/v1/florence/history/{session_id}**

Obter histórico de conversação.

**Response**:
```json
{
  "session_id": "session-123",
  "messages": [
    {
      "role": "user",
      "content": "Como criar um Patient?",
      "timestamp": "2026-03-24T10:00:00Z"
    },
    {
      "role": "assistant",
      "content": "Para criar um Patient...",
      "timestamp": "2026-03-24T10:00:05Z"
    }
  ],
  "created_at": "2026-03-24T10:00:00Z",
  "updated_at": "2026-03-24T10:05:00Z"
}
```

---

### **POST /api/v1/florence/feedback**

Enviar feedback sobre resposta.

**Request**:
```json
{
  "session_id": "session-123",
  "message_id": "msg-456",
  "rating": 5,
  "comment": "Resposta muito útil!"
}
```

---

### **GET /api/v1/florence/health**

Verificar status do serviço.

**Response**:
```json
{
  "status": "healthy",
  "service": "Florence (Dr. Nise)",
  "flowise_status": "connected"
}
```

---

## 🔧 CONFIGURAÇÃO

### **1. Variáveis de Ambiente**

```bash
# Flowise
FLOWISE_URL=http://flowise:3000
FLOWISE_CHATFLOW_ID=dr-nise-chatbot
FLOWISE_API_KEY=your-api-key

# Ollama
OLLAMA_URL=http://ollama:11434
OLLAMA_MODEL=llama2:7b
```

### **2. Flowise Chatflow**

Criar chatflow "dr-nise-chatbot" com:
- **LLM**: Ollama (llama2:7b)
- **Vector Store**: PostgreSQL + pgvector
- **Embeddings**: Ollama embeddings
- **System Message**: Personalidade Dr. Nise

### **3. Base de Conhecimento**

Documentos para RAG:
- FHIR R4 Specification
- NISE Training Examples
- Clinical Scenarios
- Best Practices

---

## 📊 EXEMPLOS DE USO

### **Exemplo 1: Pergunta sobre FHIR**

```python
import httpx

async def ask_florence():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/florence/chat",
            json={
                "message": "Quais são os campos obrigatórios de um Patient?",
                "session_id": "session-001"
            }
        )
        print(response.json())
```

### **Exemplo 2: Contexto Clínico**

```python
response = await client.post(
    "http://localhost:8000/api/v1/florence/chat",
    json={
        "message": "Como registrar glicemia de um paciente diabético?",
        "session_id": "session-002",
        "context": {
            "patient_id": "patient-123",
            "specialty": "endocrinology"
        }
    }
)
```

---

## 🎓 CASOS DE USO

### **1. Aprendizado FHIR**
- Explicar recursos FHIR
- Mostrar exemplos
- Validar estruturas

### **2. Suporte Clínico**
- Interpretar resultados
- Sugerir códigos LOINC
- Explicar terminologias

### **3. Troubleshooting**
- Debugar erros de validação
- Corrigir estruturas FHIR
- Otimizar queries

---

## 🔒 SEGURANÇA

- ✅ Rate limiting (100 req/min)
- ✅ Validação de input
- ✅ Sanitização de output
- ✅ Logs de auditoria
- ⏳ Autenticação (Fase 2)
- ⏳ LGPD compliance (Fase 2)

---

## 📈 MÉTRICAS

Métricas monitoradas:
- Número de conversações
- Tempo de resposta
- Taxa de satisfação
- Fontes mais usadas
- Tópicos mais frequentes

---

## 🚀 PRÓXIMOS PASSOS

1. ✅ Integração básica (Dia 16)
2. ⏳ RAG com conhecimento médico (Dia 17)
3. ⏳ Testes de conversação (Dia 17)
4. ⏳ Feedback loop (Semana 5)
5. ⏳ Personalização por usuário (Semana 6)

---

**Responsável**: DEV1  
**Data**: 24/03/2026  
**Versão**: 1.0

